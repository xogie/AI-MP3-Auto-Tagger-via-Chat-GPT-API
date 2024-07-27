from flask import Flask, render_template, request, jsonify, send_from_directory, send_file
import os
import json
import openai
from mutagen.easyid3 import EasyID3
from mutagen.mp3 import EasyMP3, MP3
from mutagen.id3 import ID3, APIC
from select_directory import select_directory, create_json
from concurrent.futures import ThreadPoolExecutor, as_completed
import io

app = Flask(__name__)

EasyID3.RegisterTextKey('year', 'TDRC')

progress = 0
progress_message = ""

settings_file = 'settings.json'

def load_settings():
    if os.path.exists(settings_file):
        with open(settings_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        default_settings = {
            'chat_gpt_api_key': '',
            'overwrite_existing_tags': False
        }
        with open(settings_file, 'w', encoding='utf-8') as f:
            json.dump(default_settings, f, indent=4)
        return default_settings

def update_metadata(filepath, metadata):
    try:
        audiofile = EasyMP3(filepath)
        audiofile['artist'] = metadata['artist']
        audiofile['title'] = metadata['title']
        audiofile['genre'] = metadata['genre']
        audiofile['album'] = metadata['album']
        audiofile['year'] = metadata['year']
        audiofile.save()
        #print(f"Updated metadata for file {filepath}")
    except Exception as e:
        print(f"Error updating metadata for file {filepath}: {str(e)}")

def ai_retag_files(files):
    settings = load_settings()
    openai.api_key = settings['chat_gpt_api_key']

    updated_files = []
    for file in files:
        if not file['artist'] or not file['title']:
            filename_without_extension = os.path.splitext(file['name'])[0]
            if not file['artist']:
                file['artist'] = filename_without_extension
            if not file['title']:
                file['title'] = filename_without_extension

        prompt = (
            f"Artist: {file['artist']}\n"
            f"Title: {file['title']}\n"
            "Please provide updated metadata for this artist and title. It is very important to include the year and album. "
            "If you do not know any specific value, leave it blank. You should clean up the information as best as you can. "
            "Translate any foreign languages to ENGLISH. "
            "Return the metadata as a JSON object in the format:\n"
            "{\n"
            '  "artist": "example artist",\n'
            '  "title": "example title",\n'
            '  "genre": "example genre (if unknown, guess based on the artist normal style)",\n'
            '  "album": "example album",\n'
            '  "year": "example year"\n'
            "}"
        )

        try:
            response = openai.ChatCompletion.create(
                model="gpt-4o-mini-2024-07-18",
                messages=[
                    {"role": "system", "content": "You are a helpful mp3 tagging assistant based on basic information."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=150
            )

            response_content = response.choices[0]['message']['content'].strip()
            #print(f"Response for file {file['name']}: {response_content}")

            json_start = response_content.find("{")
            json_end = response_content.rfind("}") + 1
            if json_start != -1 and json_end != -1:
                json_response = response_content[json_start:json_end]
            else:
                raise ValueError("JSON object not found in the response")

            json_response = json_response.replace(',}', '}').replace('}\n}', '}').strip()

            try:
                updated_metadata = json.loads(json_response)
                updated_file = {
                    'artist': updated_metadata.get('artist', ''),
                    'title': updated_metadata.get('title', ''),
                    'genre': updated_metadata.get('genre', ''),
                    'album': updated_metadata.get('album', ''),
                    'year': updated_metadata.get('year', ''),
                    'name': file['name'],
                    'path': file['path']
                }
                updated_files.append(updated_file)
            except json.JSONDecodeError as json_err:
                #print(f"JSON decode error for file {file['name']}: {str(json_err)}")
                #print(f"Raw response: {response_content}")
                updated_files.append(file)

        except Exception as e:
            #print(f"Error retagging file {file['name']}: {str(e)}")
            updated_files.append(file)

    #print(f"Updated files: {updated_files}")
    return updated_files

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/auto_tag', methods=['POST'])
def auto_tag():
    try:
        files = request.json
        #print(f"Files received for auto-tagging: {files}")

        updated_files = ai_retag_files(files)
        #print(f"Updated files from AI retagging: {updated_files}")

        for updated_file in updated_files:
            update_metadata(updated_file['path'], updated_file)

        return jsonify({"status": "success", "updatedData": updated_files})
    except Exception as e:
        print(f"Error in auto_tag endpoint: {str(e)}")
        return jsonify({"error": str(e)})

@app.route('/select_directory', methods=['GET'])
def select_directory_endpoint():
    try:
        directory = select_directory()
        if not directory:
            return jsonify({"error": "No directory selected"})
        return jsonify({"directory": directory})
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/update_files', methods=['POST'])
def update_files():
    try:
        files = request.json
        print(f"Received files for update: {files}")
        for file in files:
            filepath = file['path']
            audiofile = EasyMP3(filepath)
            audiofile['artist'] = file.get('artist', '') or ''
            audiofile['title'] = file.get('title', '') or ''
            audiofile['genre'] = file.get('genre', '') or ''
            audiofile['album'] = file.get('album', '') or ''
            audiofile['year'] = file.get('year', '') or ''
            audiofile.save()
            print(f"Updated metadata for file {filepath}")
        return jsonify({"status": "success"})
    except Exception as e:
        print(f"Error updating files: {str(e)}")
        return jsonify({"error": str(e)})

@app.route('/load_directory', methods=['POST'])
def load_directory():
    global progress, progress_message
    try:
        directory = request.form['directory']
        if not os.path.isdir(directory):
            return jsonify({"error": "Directory does not exist"})

        json_file = 'mp3_data.json'
        if os.path.exists(json_file):
            os.remove(json_file)

        files = create_json(directory)
        progress = 100
        return jsonify(files)
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/get_album_art', methods=['GET'])
def get_album_art():
    file_path = request.args.get('file_path')
    audio = MP3(file_path, ID3=ID3)
    if audio.tags:
        for tag in audio.tags.values():
            if isinstance(tag, APIC):
                return send_file(
                    io.BytesIO(tag.data),
                    mimetype=tag.mime,
                    as_attachment=False,
                    download_name='album_art.jpg'
                )
    return '', 404

@app.route('/progress', methods=['GET'])
def get_progress():
    global progress, progress_message
    return jsonify({"progress": progress, "message": progress_message})

@app.route('/settings', methods=['GET', 'POST'])
def handle_settings():
    if request.method == 'GET':
        settings = load_settings()
        return jsonify(settings)
    elif request.method == 'POST':
        try:
            settings = request.json
            with open(settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=4)
            return jsonify({"status": "success"})
        except Exception as e:
            return jsonify({"error": str(e)})

def get_metadata(filepath):
    audiofile = EasyMP3(filepath)
    if (audiofile and audiofile.tags):
        metadata = {
            'path': filepath,
            'name': os.path.basename(filepath),
            'artist': audiofile.tags.get('artist', [''])[0],
            'title': audiofile.tags.get('title', [''])[0],
            'genre': audiofile.tags.get('genre', [''])[0],
            'album': audiofile.tags.get('album', [''])[0],
            'year': audiofile.tags.get('year', [''])[0] if 'year' in audiofile.tags else ''
        }
    else:
        metadata = {
            'path': filepath,
            'name': os.path.basename(filepath),
            'artist': '',
            'title': '',
            'genre': '',
            'album': '',
            'year': ''
        }
    return metadata

@app.route('/audio/<path:filename>')
def audio(filename):
    directory = os.path.dirname(filename)
    filename = os.path.basename(filename)
    return send_from_directory(directory, filename)

def process_file(file_path):
    try:
        audio = EasyID3(file_path)
        return {
            'artist': audio.get('artist', [''])[0],
            'title': audio.get('title', [''])[0],
            'genre': audio.get('genre', [''])[0],
            'album': audio.get('album', [''])[0],
            'year': audio.get('date', [''])[0],
            'name': os.path.basename(file_path),
            'path': file_path
        }
    except mutagen.id3.ID3NoHeaderError:
        return {
            'artist': '',
            'title': '',
            'genre': '',
            'album': '',
            'year': '',
            'name': os.path.basename(file_path),
            'path': file_path
        }
    
@app.route('/deletefile', methods=['GET'])
def delete_file():
    file_path = request.args.get('file')
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            return jsonify({"status": "success"})
        else:
            return jsonify({"status": "error", "message": "File does not exist"}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

def create_json(directory):
    global progress, progress_message
    mp3_files = []
    total_files = 0
    for root, _, files in os.walk(directory):
        total_files += len([file for file in files if file.lower().endswith('.mp3')])
    progress_message = f'Found {total_files} MP3 files.'
    progress = 0

    with ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
        futures = []
        count = 0
        for root, _, files in os.walk(directory):
            for file in files:
                if file.lower().endswith('.mp3'):
                    file_path = os.path.join(root, file)
                    futures.append(executor.submit(process_file, file_path))
                    count += 1
                    if count % 1000 == 0:
                        progress_message = f'Loading {count} files...'
                        progress = (count / total_files) * 100
        
        for future in as_completed(futures):
            mp3_files.append(future.result())

    with open('mp3_data.json', 'w', encoding='utf-8') as f:
        json.dump(mp3_files, f, indent=4)

    progress_message = 'All files loaded successfully.'
    progress = 100
    return mp3_files

if __name__ == "__main__":
    app.run(port=5555)
