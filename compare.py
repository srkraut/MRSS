#importing essential
import requests
import xml.etree.ElementTree as ET
from tqdm import tqdm
from datetime import datetime 
import pytz
from pathlib import Path

def compare_arrays(source, cms):
    """
    Compares source and cms arrays, returning two lists:
        1. Missing layouts (present in cms but not in source), with layout ID.
        2. Missing teams (present in source but not in cms), with team name and video URL.
    """
    missing_layouts = []
    missing_teams = []

    source_dict = {tuple(item['by_team'].split(' , ')): item for item in source}
    cms_dict = {tuple(item['layout'].replace('_', ' ').split(' , ')): item for item in cms}

   
    for layout, item in cms_dict.items():
        if layout not in source_dict:
            missing_layouts.append({'layout': item['layout'], 'layoutId': item['layoutId'], 'publishedStatus': item['publishedStatus']})

    
    for team, item in source_dict.items():
        if team not in cms_dict:
            missing_teams.append({'by_team': item['by_team'], 'video_url': item['video_url'] , 'exp_date': item['exp_date']})
    
    """Creates a replacement array based on missing layouts and teams."""
    replacements = []


    # Format the new date as a string
    max_length = max(len(missing_layouts), len(missing_teams))

    for i in range(max_length):
        layout_data = missing_layouts[i] if i < len(missing_layouts) else {'layout': None, 'layoutId': None, 'publishedStatus': None}
        team_data = missing_teams[i] if i < len(missing_teams) else {'by_team': None, 'video_url': None}
        
        # Only create a replacement if either layout or team data is not None
        if layout_data['layout'] or team_data['by_team']:
            replacements.append({
                'replace_layout': layout_data['layout'],
                'layout_id': layout_data['layoutId'],
                'by_team': team_data['by_team'],
                'video_url': team_data['video_url'],
                'exp_date' : team_data['exp_date'],
                'publishedStatus': layout_data['publishedStatus']
            })

    return replacements