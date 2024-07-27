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
import logging
logging.basicConfig(level=logging.DEBUG)
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
        print(f"Updated metadata for file {filepath}")
    except Exception as e:
        print(f"Error updating metadata for file {filepath}: {str(e)}")

def ai_retag_files(files):
    settings = load_settings()
    openai.api_key = settings['chat_gpt_api_key']
    overwrite_existing_tags = settings.get('overwrite_existing_tags', False)

    updated_files = []
    for file in files:
        # Check if there are any missing tags
        if all(file.get(tag) for tag in ['artist', 'title', 'genre', 'album', 'year']) and not overwrite_existing_tags:
            # If there are no missing tags and we are not overwriting, skip the AI tagging
            updated_files.append(file)
            continue

        filename_without_extension = os.path.splitext(file['name'])[0]

        # Ensure filename is used as default for missing tags
        artist = file['artist'] if file['artist'] else filename_without_extension
        title = file['title'] if file['title'] else filename_without_extension

        prompt = (
            f"Artist: {artist}\n"
            f"Title: {title}\n"
            "Please provide updated metadata for this artist and title. It is very important to include the year and album. "
            "If you do not know any specific value, leave it blank. You should clean up the information as best as you can. "
            "Translate any foreign languages to ENGLISH. "
            "Return the metadata as a JSON object in the format:\n"
            "{\n"
            '  "artist": "example artist only",\n'
            '  "title": "example title only",\n'
            '  "genre": "example genre only (if unknown, guess based on the artist normal style)",\n'
            '  "album": "example album only",\n'
            '  "year": "example year only"\n'
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
            print(f"Response for file {file['name']}: {response_content}")

            json_start = response_content.find("{")
            json_end = response_content.rfind("}") + 1
            if json_start != -1 and json_end != -1:
                json_response = response_content[json_start:json_end]
            else:
                raise ValueError("JSON object not found in the response")

            json_response = json_response.replace(',}', '}').replace('}\n}', '}').strip()

            try:
                updated_metadata = json.loads(json_response)

                # If overwrite_existing_tags is False, only update missing tags
                if not overwrite_existing_tags:
                    if file['artist']:
                        updated_metadata['artist'] = file['artist']
                    if file['title']:
                        updated_metadata['title'] = file['title']
                    if file['genre']:
                        updated_metadata['genre'] = file['genre']
                    if file['album']:
                        updated_metadata['album'] = file['album']
                    if file['year']:
                        updated_metadata['year'] = file['year']

                updated_file = {
                    'artist': updated_metadata.get('artist', file['artist']),
                    'title': updated_metadata.get('title', file['title']),
                    'genre': updated_metadata.get('genre', file['genre']),
                    'album': updated_metadata.get('album', file['album']),
                    'year': updated_metadata.get('year', file['year']),
                    'name': file['name'],
                    'path': file['path']
                }
                updated_files.append(updated_file)
            except json.JSONDecodeError as json_err:
                print(f"JSON decode error for file {file['name']}: {str(json_err)}")
                print(f"Raw response: {response_content}")
                updated_files.append(file)

        except Exception as e:
            print(f"Error retagging file {file['name']}: {str(e)}")
            updated_files.append(file)

    print(f"Updated files: {updated_files}")
    return updated_files

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/auto_tag', methods=['POST'])
def auto_tag():
    try:
        files = request.json
        logging.debug(f"Files received for auto-tagging: {json.dumps(files, indent=4)}")
        
        updated_files = ai_retag_files(files)
        logging.debug(f"Updated files from AI retagging: {json.dumps(updated_files, indent=4)}")
        
        for updated_file in updated_files:
            update_metadata(updated_file['path'], updated_file)
        
        # Return the correctly updated data
        return jsonify({"status": "success", "updatedData": updated_files})
    except Exception as e:
        logging.error(f"Error in auto_tag endpoint: {str(e)}")
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
        print(f"Received files for update: {json.dumps(files, indent=4)}")  # Debugging line
        for file in files:
            filepath = file['path']
            audiofile = EasyMP3(filepath)
            
            # Update tags if provided, otherwise delete the tag
            if 'artist' in file:
                if file['artist']:
                    audiofile['artist'] = file['artist']
                else:
                    audiofile.tags.pop('artist', None)
            if 'title' in file:
                if file['title']:
                    audiofile['title'] = file['title']
                else:
                    audiofile.tags.pop('title', None)
            if 'genre' in file:
                if file['genre']:
                    audiofile['genre'] = file['genre']
                else:
                    audiofile.tags.pop('genre', None)
            if 'album' in file:
                if file['album']:
                    audiofile['album'] = file['album']
                else:
                    audiofile.tags.pop('album', None)
            if 'year' in file:
                if file['year']:
                    audiofile['year'] = file['year']
                else:
                    audiofile.tags.pop('year', None)

            audiofile.save()
            print(f"Updated metadata for file {filepath}")  # Debugging line
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
    print(f"Retrieving album art for: {file_path}")
    audio = MP3(file_path, ID3=ID3)
    if audio.tags:
        for tag in audio.tags.values():
            if isinstance(tag, APIC):
                print(f"Album art found for: {file_path}")
                return send_file(
                    io.BytesIO(tag.data),
                    mimetype=tag.mime,
                    as_attachment=False,
                    download_name='album_art.jpg'
                )
    print(f"No album art found for: {file_path}")
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
            result = future.result()
            if result:
                mp3_files.append(result)
                print(f"Processed file: {result}")  # Debugging line

    with open('mp3_data.json', 'w', encoding='utf-8') as f:
        json.dump(mp3_files, f, indent=4)

    progress_message = 'All files loaded successfully.'
    progress = 100
    return mp3_files

if __name__ == "__main__":
    app.run(port=5555)
