#importing essential
import requests
import xml.etree.ElementTree as ET
from tqdm import tqdm
from datetime import datetime , timedelta
import pytz
from pathlib import Path
import json
import os
from utils import *
from mrsssource import *
from createalllayout import *
from compare import *
from replace import *

# init cms authentication
url_all = "cdn2.barvanna.com"
source_url = 'https://assets.vedia.ai/rawshorts/public/vedia/mrss/prod/generic/sports-previews/mlb-pre/rss/baseball/mlb-game-preview/barvanna/latest.mrss.xml'
url = f"https://{url_all}/api/authorize/access_token"
folderId = 7
client_id = "1d38f411a6928018cfc3a411b120d124bf81af76"
client_secret = "214713e8ab75008865825bb99fe5f3e1b8ecf56b9acbc70c3002df4de4241a11210b6f5983679a15b48842fd6e1e889508f25f3b5b0dc2c83a831b529f4d0c27bfe64e3b9fb47ab1a482aaaf174b0f4a5b63ca00873b810b9d7f360bf6796176043e981b736a46a6921edf78135523b62243bbbd0232b0b5650ae321cdb38a"
grant_type = "client_credentials"
access_token = ""
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


source_array = fetch_source(source_url)
print(source_array)

# fetch 
url1 = f'https://{url_all}/api/layout?folderId={folderId}&start=0&size=10'
url2 = f'https://{url_all}/api/layout?folderId={folderId}&start=10&size=15'# Assuming headers is already defined in your environment
cms_array = fetch_and_merge_layouts(url1, url2, headers)
print(cms_array)

if cms_array:
    #there is layout in cms and do replacement
    if source_array:
        replace_and_create_new_layout(compare_arrays(source_array,cms_array),access_token,f'https://{url_all}/api/library',folderId,url_all)
    else:
        print("no data in source")
else:
    #if there is no layout in cms folder 
    #else populate the whole teams_videos to the layout
    create_layout(source_array , access_token , folderId , url_all )