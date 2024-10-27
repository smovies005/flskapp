import os
import requests
import pickle
import re
import json
from flask import Flask, request, jsonify, render_template
from google.auth.transport.requests import AuthorizedSession
import datetime

app = Flask(__name__)

# Scopes for Google Photos
SCOPES = ['https://www.googleapis.com/auth/photoslibrary.readonly']

def load_credentials(token_file):
    with open(token_file, 'rb') as token:
        creds = pickle.load(token)
    return creds

def list_photos(creds):
    session = AuthorizedSession(creds)
    photos = []
    next_page_token = None

    while True:
        params = {
            'pageSize': 100,
            'pageToken': next_page_token
        }
        response = session.get('https://photoslibrary.googleapis.com/v1/mediaItems', params=params)

        if response.status_code == 200:
            media_items = response.json().get('mediaItems', [])
            photos.extend(media_items)
            next_page_token = response.json().get('nextPageToken')
            if not next_page_token:  # Exit loop if there's no next page
                break
        else:
            print(f'Error retrieving photos: {response.status_code}')
            break

    return photos

def sanitize_filename(filename):
    return re.sub(r'[<>:"/\\|?*]', '_', filename)

@app.route('/')
def index():
    return render_template('upload.html')

@app.route('/upload', methods=['POST'])
def upload_token():
    try:
        if 'token' not in request.files:
            return 'No token file uploaded', 400

        token_file = request.files['token']
        # Use in-memory storage instead of saving to a file
        token_data = token_file.read()  # Read the token file directly into memory
        creds = pickle.loads(token_data)  # Load credentials from in-memory bytes

        # Retrieve media items
        photos = list_photos(creds)

        # Prepare JSON data
        photo_data = [
            {
                'title': sanitize_filename(photo.get('filename', f'Photo_{i+1}')),
                'url': photo['baseUrl']
            } 
            for i, photo in enumerate(photos) if photo.get('mimeType', '').startswith('image/')
        ]

        # Directly return the JSON response
        return jsonify(photo_data)
    except Exception as e:
        print(f"Error occurred: {e}")  # Log error to console
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
