#imports
import requests
import xml.etree.ElementTree as ET
from tqdm import tqdm
from datetime import datetime 
import pytz
from pathlib import Path
import json
import os

# init cms authentication
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
    headers = {
            'Authorization': f'Bearer {access_token}'
        }
else:
    print('Failed to get access token. Status code:', response.status_code, 'Response:', response.text)


#list out all the layout (should be 15) form folder number 7 
#if count is 0 fetch all fifteen.

layout_list_by_folder= 'https://cdn2.barvanna.com/api/layout?folderId=7'

def check_layout_response(url, headers=None):
    try:
        # Send a GET request to the URL with optional headers
        response = requests.get(url, headers=headers)

        # Raise an exception if the request was unsuccessful
        response.raise_for_status()

        # Try to parse the response as JSON
        data = response.json()
        # Count the number of items in the JSON array
        item_count = len(data)

        print("Number of items in the array:", item_count)
        # Check if data is a list and has 15 elements or is empty
        if isinstance(data, list) and (len(data) > 5):
        
            return True
            
        else:
            return False

    except requests.exceptions.RequestException as e:
        # Handle any errors during the request
        print(f"An error occurred: {e}")
        return False
    except ValueError:
        # Handle case where the response is not valid JSON
        print("The response is not valid JSON.")
        return False
    

result = check_layout_response(layout_list_by_folder, headers=headers)

source_url = 'https://assets.vedia.ai/rawshorts/public/vedia/mrss/prod/generic/sports-previews/mlb-pre/rss/baseball/mlb-game-preview/barvanna/latest.mrss.xml'
# source_url = 'https://cdn.itsoch.com/latest.mrss.xml'

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
    
#constants
teams_videos = []
formatted_date = ""

def fetch_source() :
    # Fetch the XML content from the URL
    response = requests.get(source_url)
    response.raise_for_status()
    xml_content = response.content

    # Parse the XML content
    root = ET.fromstring(xml_content)

    # Define the namespace
    namespaces = {'media': 'http://search.yahoo.com/mrss/'}

    # Iterate through each item in the feed
    for item in root.findall('.//item'):
        media_group = item.find('media:group', namespaces)
        custom_parms = item.find('customParams', namespaces)
        if custom_parms is not None:
            expire_date = custom_parms.find('match_date', namespaces)
            if expire_date is not None:
                expire_date_text = expire_date.text.strip()
                # Define the format of the input date string
                input_format = "%B %d, %Y %H:%M"

                # Parse the date string into a naive datetime object
                naive_datetime_obj = datetime.strptime(expire_date_text, input_format)

                # Assume the input datetime is in a specific timezone (e.g., 'US/Eastern')
                # Replace 'US/Eastern' with the desired timezone
                timezone_obj = pytz.timezone('US/Eastern')

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
                teams_videos.append({'by_team': teams_text, 'video_url': video_url , 'exp_date' : formatted_date})

    # Print the array
    print(teams_videos)   

def create_layout(arr):
    # Loop through each item in teams_videos and upload the video``
    for item in arr:
        try:
            teams_text = item['by_team'].replace(' ', '_')
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
                # 'expires' : '2024-09-08 21:20:00'
                'expires': item['exp_date']
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
                'folderId': '7'
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


        except Exception as e:
            print(f"Error processing {item}: {e}")

    print("Completed processing all items")


#check if the MLB folder is empty and dont have 15 matches , now grab the matches and create the layout one by one if the result dont have 15 matches

if not result:
    # Code to execute if result is False
    print("The response did not meet the expected criteria. Executing code to download and setup all 15 layout")
    # Insert your alternate block of code here
    fetch_source()
    create_layout(teams_videos)   
    
else:
    print("The response met the expected criteria of 15 layout in the folder")

source_names = teams_videos
cms_layout = []

#now check and compare the layout name and source names.
#lets fetch source and fetch layout name from the cms folder and make an array and compare the both names respectively.
#the araay comparison may be up and down , but what we do is , we dont touch existing names and we replace new name from source to unmatch layout in cms.

def fetch_and_merge_layouts(url1, url2, headers):
    """
    Fetch JSON data from two URLs with headers, merge them, and extract 'layout' names and 'layoutId's into an array.
    
    Parameters:
    url1 (str): The first URL to fetch JSON data from.
    url2 (str): The second URL to fetch JSON data from.
    headers (dict): Headers to include in the HTTP requests.
    
    Returns:
    list: An array of dictionaries containing 'layout' names and 'layoutId's from the merged JSON data.
    """
    # Fetch JSON data from both URLs with headers
    response1 = requests.get(url1, headers=headers)
    response2 = requests.get(url2, headers=headers)

    # Parse the JSON data
    json_data1 = response1.json()
    json_data2 = response2.json()

    # Merge the two JSON arrays
    merged_data = json_data1 + json_data2

    # Extract 'layout' names and 'layoutId's into a list of dictionaries
    layout_details = [{'layout': item['layout'], 'layoutId': item.get('layoutId')} for item in merged_data]

    return layout_details

# Example usage
url1 = 'https://cdn2.barvanna.com/api/layout?folderId=7&start=0&size=10'
url2 = 'https://cdn2.barvanna.com/api/layout?folderId=7&start=10&size=15'

# Assuming headers is already defined in your environment
cms_layout = fetch_and_merge_layouts(url1, url2, headers)
print(cms_layout)


fetch_source()
missing_layouts = []
missing_teams = []

def compare_arrays(source, cms):
    """
    Compares source and cms arrays, returning two lists:
        1. Missing layouts (present in cms but not in source), with layout ID.
        2. Missing teams (present in source but not in cms), with team name and video URL.
    """
    source_dict = {tuple(item['by_team'].split(' , ')): item for item in source}
    cms_dict = {tuple(item['layout'].replace('_', ' ').split(' , ')): item for item in cms}

   
    for layout, item in cms_dict.items():
        if layout not in source_dict:
            missing_layouts.append({'layout': item['layout'], 'layoutId': item['layoutId']})

    
    for team, item in source_dict.items():
        if team not in cms_dict:
            missing_teams.append({'by_team': item['by_team'], 'video_url': item['video_url']})

# Find the missing layouts
update_result = compare_arrays(source_names, cms_layout)

def create_replacement_array(missing_layouts, missing_teams):
    """Creates a replacement array based on missing layouts and teams."""
    replacements = []
    max_length = max(len(missing_layouts), len(missing_teams))

    for i in range(max_length):
        layout_data = missing_layouts[i] if i < len(missing_layouts) else {'layout': None, 'layoutId': None}
        team_data = missing_teams[i] if i < len(missing_teams) else {'by_team': None, 'video_url': None}
        
        # Only create a replacement if either layout or team data is not None
        if layout_data['layout'] or team_data['by_team']:
            replacements.append({
                'replace_layout': layout_data['layout'],
                'layout_id': layout_data['layoutId'],
                'by_team': team_data['by_team'],
                'video_url': team_data['video_url']
            })

    return replacements



replacement_array = create_replacement_array(missing_layouts, missing_teams)
print(replacement_array)


#create a function to delete the layout that is in the cms using update_result

def delete_and_create_new_layout(arr):
    # Loop through each item in teams_videos and upload the video
    for item in arr:
        try:
            layout_headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }

            teams_text = item['by_team'].replace(' ', '_')
            video_url = item['video_url']
            layoutid = 0
             
            #editing the layout name 
            if item['layout_id'] is not None:
               layoutid = item['layout_id']
               edit_url = f"https://cdn2.barvanna.com/api/layout/{layoutid}"
                # Define the data payload with the parameters you want to update
               data_payload = {
                        "name": teams_text  # Assuming 'name' is part of the item dictionary
                    }
               edit_response = requests.put(edit_url, headers=layout_headers , json=data_payload)
               print(edit_response)

            if item['layout_id'] is None : 
                create_layout(arr)
                break

            # Step 1: Download the video file from the provided URL
            filename = f"{video_url.split('/')[-1].split('.')[0]}.mp4"
            download_file(video_url, filename)

            # Step 2: Upload the video file via POST request
            file_path = Path(filename)
            data = {
                'name': filename,
                'folderId': '5',
                'deleteOnExpiry': 1,
                # 'expires' : '2024-09-08 21:20:00'
                'expires': item['exp_date']
            }
            headers = {
                'Authorization': f'Bearer {access_token}'
            }

            # Perform the upload
            upload_response = upload_file(file_path, upload_url, data, headers)
            uploaded_media_id = upload_response.json()['files'][0]['mediaId']
            print(f"Uploaded {filename}: {upload_response.text}")

            #do checkout and get draft id
            # # Get the draft layout ID
            draftid_url = f"https://cdn2.barvanna.com/api/layout/checkout/{layoutid}"
            layoutid_payload = {
                    "layoutId": layoutid,
                }
            draft_response = requests.put(draftid_url, headers=layout_headers , json=layoutid_payload)
            draft_response.raise_for_status()
            draft_layout_id = draft_response.json()['layoutId']
            print(f"Draft layout ID: {draft_layout_id}")

            #now get the playlist name , delete the existing video and put another one , ok !
            # Get the playlist ID of the draft layout
            draft_layout_details_url = f"https://cdn2.barvanna.com/api/layout?layoutId={draft_layout_id}&embed=regions,playlists,widgets"
            draft_layout_response = requests.get(draft_layout_details_url, headers=layout_headers)
            draft_layout_response.raise_for_status()
            print(draft_layout_response.json())
            playlist_id = draft_layout_response.json()[0]['regions'][0]['regionPlaylist']['playlistId']
            print(f"Playlist ID: {playlist_id}")

            #get old widget id (old video) and delete it from playlist
            old_video_widget_id = draft_layout_response.json()[0]['regions'][0]['regionPlaylist']['widgets'][0]['widgetId']
            #delete a widget
            delete_widget_url = f'https://cdn2.barvanna.com/api/playlist/widget/{old_video_widget_id}'
            delete_widget_response = requests.delete(delete_widget_url , headers=layout_headers)
            delete_widget_response.raise_for_status()
            print(f"widget deleted :  {old_video_widget_id}")


            # Step 4: Assign the uploaded media to the playlist
            assign_url = f'https://cdn2.barvanna.com/api/playlist/library/assign/{playlist_id}'
            payload = {'media': [uploaded_media_id]}  # Ensure the media is sent as an array
            assign_response = requests.post(assign_url, json=payload, headers=layout_headers)
            assign_response.raise_for_status()
            print(f"Assigned media ID 4761 to playlist ID {playlist_id}")

            # Step 5: Publish the layout
            publish_url = f'https://cdn2.barvanna.com/api/layout/publish/{layoutid}'
            publishref = {'publishNow': 1}
            publish_response = requests.put(publish_url, json=publishref, headers=layout_headers)
            publish_response.raise_for_status()
            published_layout_id = publish_response.json()['layoutId']
            print(f"Published layout ID: {published_layout_id}")


        except Exception as e:
            print(f"Error processing {item}: {e}")

    print("Completed processing all items")

delete_and_create_new_layout(replacement_array)



file_path = 'output_array.json'
# if replacement_array:
#         # Save the array to a JSON file, replacing it if it already exists
#     with open(file_path, 'w') as json_file:
#         json.dump(teams_videos, json_file, indent=4)
#         print(f"Data saved to {file_path}")

# download the mrss feed into a file
# match the old file with new file , only check similar title video name
# if video is changed , create a array , put layout id to delete and match name and video name . 
# if video is changed then delete the old file and save latest mrss as mrss old.

#downloading the mrss feed and saving it in the local storage
# Define the file path


# Save the array to a JSON file
# Save the array to a JSON file only if the file doesn't exist
if not os.path.exists(file_path):
    with open(file_path, 'w') as json_file:
        json.dump(teams_videos, json_file, indent=4)
    print(f"Data saved to {file_path}")
else:
    print(f"File {file_path} already exists. No data was saved.")

# Load the array from a JSON file
def load_from_json(path):
    with open(path, 'r') as json_file:
        data = json.load(json_file)
    return data

# Load the array from the file later
loaded_data = load_from_json(file_path)

print("Loaded Data:", loaded_data)

print("cms layout" , cms_layout)

# compare loaded data with source data array
# Initialize an empty list for new videos
new_video = []

# Iterate through the output array
for out_item in loaded_data:
    for src_item in teams_videos:
        if out_item['by_team'] == src_item['by_team'] and out_item['video_url'] != src_item['video_url']:
            new_video.append({'by_team': out_item['by_team'], 'video_url': src_item['video_url']})

print (new_video)
new_update_array = []


# Check if new_video is empty or not and print the appropriate message
if not new_video:
    print("No changes.")
else:
    print("There is a new video in the existing layout, updating the layout.")
    # compare new video with cms layout and delete the cms layout and replace by new video and name
    # Initialize the new array

    # Iterate over the new update array
    for update in new_video:
        teams = update['by_team'].replace(' ', '_')  # Format to match layout in CMS
        for item in cms_layout:
            if item['layout'] == teams:
                new_entry = {
                    'layout_id': item['layoutId'],
                    'by_team': update['by_team'],
                    'video_url': update['video_url'],
                    'exp_date' : update['exp_date']
                }
                new_update_array.append(new_entry)
    
    print("new data : " , new_update_array)
     #delete layout id , and put new layout (replacing the layout simplified)
    delete_and_create_new_layout(new_update_array)
    #delete existing output_array and replace it with current source
    # Save the array to a JSON file, replacing it if it already exists
    with open(file_path, 'w') as json_file:
        json.dump(teams_videos, json_file, indent=4)
        print(f"Data saved to {file_path}")