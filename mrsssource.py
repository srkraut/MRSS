#importing essential
import requests
import xml.etree.ElementTree as ET
from tqdm import tqdm
from datetime import datetime, timedelta
import pytz
from pathlib import Path

def fetch_source(source_url):
    teams_videos = []
    formatted_date = ""
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
                # Get the current date and time


        if media_group is not None:
            teams = media_group.find('media:team', namespaces)
            video_content = media_group.find('media:content[@type="video/mp4"]', namespaces)
            if teams is not None and video_content is not None:
                current_datetime = datetime.now()
                # Convert formatted_date (string) back to a datetime object using the same format
                formatted_date_obj = datetime.strptime(formatted_date, output_format)

                teams_text = teams.text.strip()
                video_url = video_content.get('url')
                # Append the team and video URL to the array
                if formatted_date_obj < current_datetime:
                    print(formatted_date + " The formatted date is in the past.")
                    # # Get the current date and time
                    # localized_datetime_obj = datetime.now()

                    # # Add one hour to the current time
                    # one_hour_later = localized_datetime_obj + timedelta(hours=1)

                    # # Define the output format
                    # output_format = "%Y-%m-%d %H:%M:%S"

                    # # Format the time one hour from now
                    # formatted_one_hour_later = one_hour_later.strftime(output_format)
                    # teams_videos.append({'by_team': teams_text, 'video_url': video_url , 'exp_date' : formatted_one_hour_later})
                    # print(formatted_one_hour_later)



                else:
                    teams_videos.append({'by_team': teams_text, 'video_url': video_url , 'exp_date' : formatted_date})

    return teams_videos