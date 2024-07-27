import tkinter as tk
from tkinter import filedialog
import os
import json
import mutagen
from mutagen.easyid3 import EasyID3
from concurrent.futures import ThreadPoolExecutor, as_completed

def center_window(root):
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry('{}x{}+{}+{}'.format(width, height, x, y))

def select_directory():
    root = tk.Tk()
    center_window(root)
    root.withdraw()  # Hide the main window
    directory = filedialog.askdirectory(parent=root)
    root.destroy()  # Destroy the main window after selecting directory
    return directory

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

def showMessage(message):
    print(message)  # Placeholder function. Replace with actual implementation.

def create_json(directory):
    mp3_files = []
    total_files = 0
    for root, _, files in os.walk(directory):
        total_files += len([file for file in files if file.lower().endswith('.mp3')])
    showMessage(f'Found {total_files} MP3 files.')

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
                        showMessage(f'Loading {count} files...')
        
        for future in as_completed(futures):
            result = future.result()
            if result:
                mp3_files.append(result)
                print(f"Processed file: {result}")  # Debugging line
    
    with open('mp3_data.json', 'w', encoding='utf-8') as f:
        json.dump(mp3_files, f, indent=4)
    
    showMessage('All files loaded successfully.')
    return mp3_files

if __name__ == "__main__":
    directory = select_directory()
    if directory:
        create_json(directory)
        print(directory)
