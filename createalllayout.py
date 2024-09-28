#create all layout
import requests
import xml.etree.ElementTree as ET
from tqdm import tqdm
from datetime import datetime , timedelta
import pytz
from pathlib import Path
from utils import *

def create_layout(arr , access_token, folderId , url_all):
    # Loop through each item in teams_videos and upload the video``
    # URL for uploading the video
    upload_url = f'https://{url_all}/api/library'
    layout_url = f'https://{url_all}/api/layout'
    for item in arr:
        try:
            exp_date = ""
            if is_date_past(item['exp_date']):
                # Get the current date and time
                current_date = datetime.now()

                # Add one day
                next_day = current_date + timedelta(days=3)

                # Format the new date as a string
                next_day_str = next_day.strftime('%Y-%m-%d %H:%M:%S')
                exp_date = next_day_str
            else:
                exp_date = item['exp_date']
            
            teams_text = item['by_team'].replace(' ', '_')
            video_url = item['video_url']

            # Step 1: Download the video file from the provided URL
            filename = f"{video_url.split('/')[-1].split('.')[0]}.mp4"
            download_file(video_url, filename)

            # Step 2: Upload the video file via POST request
            file_path = Path(filename)
            data = {
                'name': filename,
                'folderId': folderId,
                'deleteOnExpiry': 1,
                # 'expires' : '2024-10-08 21:20:00'
                'expires': exp_date
            }
            headers = {
                'Authorization': f'Bearer {access_token}'
            }

            # Perform the upload
            upload_response = upload_file(file_path, upload_url, data, headers)
            uploaded_media_id = upload_response.json()['files'][0]['mediaId']
            print(f"Uploaded {filename}: {upload_response.text}")

            # Step 3: Create a new layout for the video
            layout_data = {
                'resolutionId': 1,
                'name': teams_text,
                'folderId': folderId
            }
            layout_headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            layout_response = requests.post(layout_url, json=layout_data, headers=layout_headers)
            layout_response.raise_for_status()
            original_layout_id = layout_response.json()['layoutId']
            print(f"Created layout for {teams_text}: {layout_response.text}")

            # Get the draft layout ID
            draftid_url = f"https://{url_all}/api/layout?parentId={original_layout_id}"
            draft_response = requests.get(draftid_url, headers=layout_headers)
            draft_response.raise_for_status()
            draft_layout_id = draft_response.json()[0]['layoutId']
            print(f"Draft layout ID: {draft_layout_id}")

            # Get the playlist ID of the draft layout
            draft_layout_details_url = f"https://{url_all}/api/layout?layoutId={draft_layout_id}&embed=regions,playlists,widgets"
            draft_layout_response = requests.get(draft_layout_details_url, headers=layout_headers)
            draft_layout_response.raise_for_status()
            playlist_id = draft_layout_response.json()[0]['regions'][0]['regionPlaylist']['playlistId']
            print(f"Playlist ID: {playlist_id}")

            # Step 4: Assign the uploaded media to the playlist
            assign_url = f'https://{url_all}/api/playlist/library/assign/{playlist_id}'
            payload = {'media': [uploaded_media_id]}  # Ensure the media is sent as an array
            assign_response = requests.post(assign_url, json=payload, headers=layout_headers)
            assign_response.raise_for_status()
            print(f"Assigned media ID {uploaded_media_id} to playlist ID {playlist_id}")

            # Step 5: Publish the layout
            publish_url = f'https://{url_all}/api/layout/publish/{original_layout_id}'
            publishref = {'publishNow': 1}
            publish_response = requests.put(publish_url, json=publishref, headers=layout_headers)
            publish_response.raise_for_status()
            published_layout_id = publish_response.json()['layoutId']
            print(f"Published layout ID: {published_layout_id}")


        except Exception as e:
            print(f"Error processing {item}: {e}")

    print("Completed processing all items")