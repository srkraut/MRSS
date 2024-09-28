import requests
import xml.etree.ElementTree as ET
from tqdm import tqdm
from datetime import datetime , timedelta
import pytz
from pathlib import Path
import json
import os

# Function to download a file with progress
def download_file(url, local_filename):
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        total_size = int(r.headers.get('content-length', 0))
        with open(local_filename, 'wb') as f, tqdm(
            desc=local_filename,
            total=total_size,
            unit='iB',
            unit_scale=True,
        ) as bar:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
                bar.update(len(chunk))

# Function to upload a file with progress
def upload_file(file_path, url, data, headers):
    total_size = int(file_path.stat().st_size)
    with open(file_path, 'rb') as f, tqdm(
        desc=f'Uploading {file_path.name}',
        total=total_size,
        unit='iB',
        unit_scale=True
    ) as bar:
        class UploadProgress:
            def __init__(self, file, bar):
                self.file = file
                self.bar = bar

            def read(self, size=-1):
                data = self.file.read(size)
                self.bar.update(len(data))
                return data

        files = {'files': (file_path.name, UploadProgress(f, bar), 'video/mp4')}
        response = requests.post(url, files=files, data=data, headers=headers)
        response.raise_for_status()
        return response
    
def is_date_past(date_str):
    date_format = "%Y-%m-%d %H:%M:%S"
    date_obj = datetime.strptime(date_str, date_format)
    current_time = datetime.now()
    return date_obj < current_time

def fetch_and_merge_layouts(url1, url2, headers):
   
    response1 = requests.get(url1, headers=headers)
    response2 = requests.get(url2, headers=headers)

    # Parse the JSON data
    json_data1 = response1.json()
    json_data2 = response2.json()

    # Merge the two JSON arrays
    merged_data = json_data1 + json_data2
    # Extract 'layout' names and 'layoutId's into a list of dictionaries
    layout_details = [{'layout': item['layout'], 'layoutId': item.get('layoutId'), 'publishedStatus':item.get('publishedStatus') } for item in merged_data]

    return layout_details