import os
import platform
from flask import Flask, request, jsonify
from pytubefix import YouTube
from pytubefix.cli import on_progress
from flask_cors import CORS
from pathlib import Path
import re

app = Flask(__name__)
CORS(app)

# Function to get the user's Downloads folder dynamically
def get_download_folder():
    if platform.system() == 'Windows':
        # For Windows, typically it's under C:\Users\<username>\Downloads
        download_folder = Path(os.getenv('USERPROFILE')) / 'Downloads'
    elif platform.system() == 'Darwin':  # macOS
        download_folder = Path(os.getenv('HOME')) / 'Downloads'
    else:  # For Linux or other Unix-based systems
        download_folder = Path(os.getenv('HOME')) / 'Downloads'
    
    return download_folder

def sanitize_filename(filename):
    # Remove invalid characters for Windows filenames
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    return filename

@app.route('/', methods=['GET']) 
def check_api():
    return 'API is working'

# API endpoint to download video
@app.route('/download', methods=['POST'])
def download_video():
    try:
        # Get the video URL from the request body
        data = request.json
        video_url = data.get('url')
        method = data.get('method') 
        count = data.get('count', 1)  # Default count is 1 if not provided

        if not video_url:
            return jsonify({"error": "URL is required"}), 400

        # Get the dynamic download path
        download_path = get_download_folder()

        # Ensure the download directory exists
        if not download_path.exists():
            download_path.mkdir(parents=True)

        # Initialize YouTube object with use_po_token=True for bot detection bypass
        yt = YouTube(video_url, on_progress_callback=on_progress, use_po_token=True)

        # Select the appropriate stream based on the method
        if method == 'itag_18':
            ys = yt.streams.get_by_itag(18)  # Itag 18 corresponds to 360p mp4
        elif method == 'itag_128':
            ys = yt.streams.get_by_itag(140)  # Itag 140 corresponds to audio stream
        else:
            ys = yt.streams.get_highest_resolution()  # Default to highest resolution

        # Check if the stream was found, else return an error
        if not ys:
            return jsonify({"error": f"Stream with method '{method}' not found."}), 400

        # Sanitize the filename to remove invalid characters
        sanitized_title = sanitize_filename(yt.title)
        download_filename = f"{sanitized_title}({count}).mp4"

        # Download the video
        ys.download(str(download_path / download_filename))

        return jsonify({"message": f"'{yt.title}' downloaded successfully!"}), 200

    except Exception as e:
        print("Error:", e)
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Use the environment variable PORT or default to 5000 for local development
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True)
