import requests
import xml.etree.ElementTree as ET
from tqdm import tqdm
from datetime import datetime
import pytz
from pathlib import Path


# Provided data
url = "https://cdn2.barvanna.com/api/authorize/access_token"
client_id = "1d38f411a6928018cfc3a411b120d124bf81af76"
client_secret = "214713e8ab75008865825bb99fe5f3e1b8ecf56b9acbc70c3002df4de4241a11210b6f5983679a15b48842fd6e1e889508f25f3b5b0dc2c83a831b529f4d0c27bfe64e3b9fb47ab1a482aaaf174b0f4a5b63ca00873b810b9d7f360bf6796176043e981b736a46a6921edf78135523b62243bbbd0232b0b5650ae321cdb38a"
grant_type = "client_credentials"

# Define the payload for the form-data
form_data = {
    'client_id': client_id,
    'client_secret': client_secret,
    'grant_type': grant_type
}

# Make the request
response = requests.post(url, data=form_data)

# Check if the request was successful
if response.status_code == 200:
    # Parse the returned JSON for the access token
    token_data = response.json()
    access_token = token_data.get('access_token')
    print('Access token:', access_token)
else:
    print('Failed to get access token. Status code:', response.status_code, 'Response:', response.text)

# In actual code, handle exceptions and potential errors.


# Define the URL of the XML
url = 'https://assets.vedia.ai/rawshorts/public/vedia/mrss/prod/generic/sports-previews/cbk-pre/rss/basketball/cbk-game-preview/barvanna/latest.mrss.xml'

# Fetch the XML content from the URL
response = requests.get(url)
response.raise_for_status()
xml_content = response.content

# Parse the XML content
root = ET.fromstring(xml_content)

# Define the namespace
namespaces = {'media': 'http://search.yahoo.com/mrss/'}

# Initialize an array to hold the team and video URL
teams_videos = []

# Iterate through each item in the feed
for item in root.findall('.//item'):
    media_group = item.find('media:group', namespaces)
    custom_parms = item.find('customParams', namespaces)
    if custom_parms is not None:
        expire_date = custom_parms.find('match_date', namespaces)
        if expire_date is not None:
            expire_date_text = expire_date.text.strip()
            # Define the format of the input date string without the timezone
            input_format = "%B %d, %Y %I:%M %p"

            # Parse the date string into a naive datetime object (excluding the timezone part)
            naive_datetime_obj = datetime.strptime(expire_date_text[:-4], input_format)

            # Extract the timezone part (last three characters)
            timezone_str = expire_date_text[-3:]

            # Map common timezone abbreviations to their corresponding pytz timezones
            timezone_mapping = {
                'EST': 'US/Eastern',
                'EDT': 'US/Eastern',
                'CST': 'US/Central',
                'CDT': 'US/Central',
                'MST': 'US/Mountain',
                'MDT': 'US/Mountain',
                'PST': 'US/Pacific',
                'PDT': 'US/Pacific'
            }

            # Get the corresponding pytz timezone object
            if timezone_str in timezone_mapping:
                timezone_obj = pytz.timezone(timezone_mapping[timezone_str])
            else:
                raise ValueError("Unsupported timezone")

            # Localize the naive datetime object to the specific timezone
            localized_datetime_obj = timezone_obj.localize(naive_datetime_obj)

            # Define the output format
            output_format = "%Y-%m-%d %H:%M:%S"

            # Convert the localized datetime object to the desired format
            formatted_date = localized_datetime_obj.strftime(output_format)

            print(formatted_date)
                
    if media_group is not None:
        teams = media_group.find('media:team', namespaces)
        video_content = media_group.find('media:content[@type="video/mp4"]', namespaces)
        if teams is not None and video_content is not None:
            teams_text = teams.text.strip()
            video_url = video_content.get('url')
            # Append the team and video URL to the array
            teams_videos.append({'teams': teams_text, 'video_url': video_url})

# Print the array
print(teams_videos)


# URL for uploading the video
upload_url = 'https://cdn2.barvanna.com/api/library'
layout_url = 'https://cdn2.barvanna.com/api/layout'

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

# Loop through each item in teams_videos and upload the video
for item in teams_videos:
    try:
        teams_text = item['teams'].replace(' ', '_')
        video_url = item['video_url']

        # Step 1: Download the video file from the provided URL
        filename = f"{video_url.split('/')[-1].split('.')[0]}.mp4"
        download_file(video_url, filename)

        # Step 2: Upload the video file via POST request
        file_path = Path(filename)
        data = {
            'name': filename,
            'folderId': '5',
            'deleteOnExpiry': 1,
            'expires': formatted_date
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
            'folderId': '5'
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
        draftid_url = f"https://cdn2.barvanna.com/api/layout?parentId={original_layout_id}"
        draft_response = requests.get(draftid_url, headers=layout_headers)
        draft_response.raise_for_status()
        draft_layout_id = draft_response.json()[0]['layoutId']
        print(f"Draft layout ID: {draft_layout_id}")

        # Get the playlist ID of the draft layout
        draft_layout_details_url = f"https://cdn2.barvanna.com/api/layout?layoutId={draft_layout_id}&embed=regions,playlists,widgets"
        draft_layout_response = requests.get(draft_layout_details_url, headers=layout_headers)
        draft_layout_response.raise_for_status()
        playlist_id = draft_layout_response.json()[0]['regions'][0]['regionPlaylist']['playlistId']
        print(f"Playlist ID: {playlist_id}")

        # Step 4: Assign the uploaded media to the playlist
        assign_url = f'https://cdn2.barvanna.com/api/playlist/library/assign/{playlist_id}'
        payload = {'media': [uploaded_media_id]}  # Ensure the media is sent as an array
        assign_response = requests.post(assign_url, json=payload, headers=layout_headers)
        assign_response.raise_for_status()
        print(f"Assigned media ID {uploaded_media_id} to playlist ID {playlist_id}")

        # Step 5: Publish the layout
        publish_url = f'https://cdn2.barvanna.com/api/layout/publish/{original_layout_id}'
        publishref = {'publishNow': 1}
        publish_response = requests.put(publish_url, json=publishref, headers=layout_headers)
        publish_response.raise_for_status()
        published_layout_id = publish_response.json()['layoutId']
        print(f"Published layout ID: {published_layout_id}")

        # Step 6: Insert the published layout into the campaign
        campaign_url = 'https://cdn2.barvanna.com/api/campaign/layout/assign/2248'
        campaign_payload = {'layoutId': published_layout_id}
        campaign_response = requests.post(campaign_url, json=campaign_payload, headers=layout_headers)
        campaign_response.raise_for_status()
        print(f"Inserted layout ID {published_layout_id} into campaign")

    except Exception as e:
        print(f"Error processing {item}: {e}")

print("Completed processing all items")