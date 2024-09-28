import requests
import xml.etree.ElementTree as ET
from tqdm import tqdm
from datetime import datetime , timedelta
import pytz
from pathlib import Path
import json
import os
from utils import *
from createalllayout import *


def replace_and_create_new_layout(arr,access_token,upload_url,folderId,url_all):
    # Loop through each item in teams_videos and upload the video
    for item in arr:
        try:
            exp_date = ""
            if is_date_past(item['exp_date']):
                # Get the current date and time
                current_date = datetime.now()

                # Add one day
                next_day = current_date + timedelta(days=1)

                # Format the new date as a string
                next_day_str = next_day.strftime('%Y-%m-%d %H:%M:%S')
                exp_date = next_day_str
            else:
                exp_date = item['exp_date']

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
               edit_url = f"https://{url_all}/api/layout/{layoutid}"
                # Define the data payload with the parameters you want to update
               data_payload = {
                        "name": teams_text  # Assuming 'name' is part of the item dictionary
                    }
               edit_response = requests.put(edit_url, headers=layout_headers , json=data_payload)
               print(edit_response)

            if item['layout_id'] is None : 
                create_layout(arr,access_token,folderId,url_all)
                break

            # Step 1: Download the video file from the provided URL
            filename = f"{video_url.split('/')[-1].split('.')[0]}.mp4"
            download_file(video_url, filename)

            # Step 2: Upload the video file via POST request
            file_path = Path(filename)
            data = {
                'name': filename,
                'folderId': folderId,
                'deleteOnExpiry': 1,
                # 'expires' : '2024-09-08 21:20:00'
                'expires': exp_date
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
            print(item['publishedStatus'])
            if(item['publishedStatus'] == 'Published'):
                draftid_url = f"https://{url_all}/api/layout/checkout/{layoutid}"
                layoutid_payload = {
                        "layoutId": layoutid,
                    }
                draft_response = requests.put(draftid_url, headers=layout_headers , json=layoutid_payload)
                draft_response.raise_for_status()
                draft_layout_id = draft_response.json()['layoutId']
                print(f"Draft layout ID: {draft_layout_id}")
            else:
                print("parent id line")
                parentid_url = f"https://{url_all}/api/layout?parentId={layoutid}"
                payload = {}
                parent_response = requests.get(parentid_url, headers=layout_headers , data=payload )
                parent_response.raise_for_status()
                print(parent_response.json())
                parent_layout_id = parent_response.json()[0]['layoutId']
                print(f"Parent layout ID: {parent_layout_id}")
                draft_layout_id = parent_layout_id


            #now get the playlist name , delete the existing video and put another one , ok !
            # Get the playlist ID of the draft layout
            draft_layout_details_url = f"https://{url_all}/api/layout?layoutId={draft_layout_id}&embed=regions,playlists,widgets,widget_validity,tags,permissions,actions"
            draft_layout_response = requests.get(draft_layout_details_url, headers=layout_headers)
            draft_layout_response.raise_for_status()
            print(draft_layout_response.json())
            playlist_id = draft_layout_response.json()[0]['regions'][0]['regionPlaylist']['playlistId']
            print(f"Playlist ID: {playlist_id}")

            
            try:
                # Get old widget id (old video) and delete it from playlist
                old_video_widget_id = draft_layout_response.json()[0]['regions'][0]['regionPlaylist']['widgets'][0]['widgetId']
                
                # Delete a widget
                print("Old widget id: " + old_video_widget_id)
                
                delete_widget_url = f'https://{url_all}/api/playlist/widget/{old_video_widget_id}'
                delete_widget_response = requests.delete(delete_widget_url, headers=layout_headers)
                
                # Raise an error if the request failed
                delete_widget_response.raise_for_status()
                
                print(f"Widget deleted: {old_video_widget_id}")

            except (KeyError, IndexError) as e:
                # Handle errors related to missing data in the JSON response (KeyError or IndexError)
                print(f"Error occurred while fetching widget id: {e}. Proceeding with next part of code.")

            except requests.HTTPError as http_err:
                # Handle HTTP errors raised by the raise_for_status()
                print(f"HTTP error occurred: {http_err}. Proceeding with next part of code.")

            except Exception as err:
                # Handle any other exceptions
                print(f"An error occurred: {err}. Proceeding with next part of code.")

            # Code below the try-except will still run if an error occurs
            # Your next block of code here


            # Step 4: Assign the uploaded media to the playlist
            assign_url = f'https://{url_all}/api/playlist/library/assign/{playlist_id}'
            payload = {'media': [uploaded_media_id]}  # Ensure the media is sent as an array
            assign_response = requests.post(assign_url, json=payload, headers=layout_headers)
            assign_response.raise_for_status()
            print(f"Assigned media to playlist ID {playlist_id}")
           
            # if(item['publishedStatus'] == 'Published'):
            #     # Step 5: Publish the layout
            #     publish_url = f'https://{url_all}/api/layout/publish/{layoutid}'
            #     publishref = {'publishNow': 1}
            #     publish_response = requests.put(publish_url, json=publishref, headers=layout_headers)
            #     publish_response.raise_for_status()
            #     published_layout_id = publish_response.json()['layoutId']
            #     print(f"Published layout ID: {published_layout_id}")
            # else:
            # Step 5: Publish the layout
            publish_url = f'https://{url_all}/api/layout/publish/{layoutid}'
            payload = {'publishNow': 'on'}
            publish_response = requests.put(publish_url, json=payload, headers=layout_headers)
            publish_response.raise_for_status()
            published_layout_id = publish_response.json()['layoutId']
            print(f"Published layout ID: {published_layout_id}")
        


        except Exception as e:
            print(f"Error processing {item}: {e}")

    print("Completed processing all items")