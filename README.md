# AI MP3 Auto Tagger via Chat GPT API

AI MP3 Auto Tagger via Chat GPT API is a tool designed to automate the process of tagging MP3 files using artificial intelligence. You need a Chat GPT API Key to use the auto-tagging feature.

If you like the direction of this project, please consider supporting me and motivating me to finish: [Buy Me a Coffee](https://buymeacoffee.com/gitxogie)

---

## Overview
AI MP3 Auto Tagger via Chat GPT API leverages the capabilities of OpenAI's GPT models to accurately tag your music files with metadata such as artist, title, genre, album, and year. This application includes features for batch processing, directory selection, and manual editing, ensuring your music library is well-organized with minimal effort. You can also play and edit tags right from your browser. Note: This tool is still under development and may contain bugs. Test and save your MP3 files in a testing folder. 

### Cost Estimation
Each call uses a maximum of 150 input tokens. Based on this, 25,000 MP3 calls would cost approximately $0.5625 (I think).

## Key Features

- **Automatic Tagging**: Utilize OpenAI's GPT models to generate accurate metadata for your MP3 files.
- **Batch Processing**: Tag multiple files at once for efficiency.
- **Manual Editing**: Edit tags manually with an easy-to-use interface.
- **Directory Selection**: Select and load entire directories of MP3 files.
- **Integration with Mutagen**: Save tags directly to your MP3 files using the Mutagen library.
- **Web Interface**: Simple and intuitive web-based interface for managing your music library.
- **Play MP3**: Double-click on any row to play the MP3 file.

## Getting Started

### Prerequisites
- Python 3.x
- Flask
- Mutagen
- OpenAI API key
- *Install required python modules. I'll work on finishing a requirements.txt file. 

### Installation
Clone the repository:
git clone https://github.com/xogie/AI-MP3-Auto-Tagger-via-Chat-GPT-API.git
cd AI-MP3-Auto-Tagger-via-Chat-GPT-API


### Setup
Obtain your OpenAI API key:
    Go to OpenAI API.
    Sign up or log in to your account.
    Navigate to the API keys section and create a new API key.

Configure your settings:
    Open the settings and enter your OpenAI API key.

Running the Application
python main.py

Open your browser and navigate to:
http://127.0.0.1:5555

### Usage
Selecting a Directory
Click on the "Select Directory" button.
Choose the directory containing your MP3 files.
Bug: Large number of MP3 files might cause issues.

### Auto-Tagging Files
After loading the directory, select the files you want to auto-tag.
Click on the "Auto Tag" button to start the tagging process (Batch Button).
If you have Artist - Title, it will search from that; if missing, it will search using the file name.

Editing Tags Manually
Select a row in the table to enable the edit menu.
Edit the artist, title, genre, album, and year fields as needed.

### Playing MP3 Files
Double-click on any row in the table to play the corresponding MP3 file (over the file name).
Known Issues and Work in Progress

### Testing: Ensure you thoroughly test the application with your files. Changes to metadata can be permanent.
Enhancements: Additional features and improvements are planned. Fingerprinting, and maybe some extra lookups.

### Contributing
Fork the repository.
Create a new branch (git checkout -b feature-branch).
Make your changes.
Commit your changes (git commit -m 'Add some feature').
Push to the branch (git push origin feature-branch).
Open a Pull Request.

AI MP3 Auto Tagger via Chat GPT API
<a href="https://ibb.co/YhCM8vD"><img src="https://i.ibb.co/YhCM8vD/image.png" alt="image" border="0"></a>

This is a work in progress tool that will change your metadata for your MP3 files using the OpenAI Chat GPT API.
