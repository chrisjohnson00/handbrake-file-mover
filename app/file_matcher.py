import os
import re
from pathlib import Path


def extract_show_from_filename(filename):
    """
    Take input like 'Shameless (US) - S01E01 - Pilot HDTV-720p.mp4' and return it's show name
    """
    filename_split = filename.split(' - ')
    # if the file doesn't match the standard pattern
    if len(filename_split) != 3:
        # try 'Downton.Abbey.S05E05.HDTV.x264-FTP.mp4' style file name
        regex_pattern = r"(.+)(S\d{1,2}E\d{1,2})(.+)"
        matches = re.match(regex_pattern, filename)
        if not matches or len(matches.groups()) < 3:
            raise Exception("{} split with no parts returned, we will die now".format(filename))
        else:
            ret_value = matches.group(1).replace('.', ' ')
            return replace_last(ret_value, " - ", "").strip()
    else:
        return filename_split[0].strip()


def replace_last(source_string, replace_what, replace_with):
    head, _sep, tail = source_string.rpartition(replace_what)
    return head + replace_with + tail


def extract_season_from_filename(filename):
    try:
        season_episode_split = extract_season_episode_parts(filename)
        season_number = int(season_episode_split[0].strip().replace('S', ''))
        return "Season {}".format(season_number)
    except ValueError:
        return None


def extract_season_episode_parts(filename):
    filename_split = filename.upper().split(' - ')
    if len(filename_split) != 3:
        # try 'Downton.Abbey.S05E05.HDTV.x264-FTP.mp4' style file name
        regex_pattern = r"(.+)(S\d{1,2}E\d{1,2})(.+)"
        matches = re.match(regex_pattern, filename)
        if not matches or len(matches.groups()) < 3:
            raise Exception("{} split with no parts returned, we will die now".format(filename))
        else:
            season_episode = matches.group(2)
    else:
        season_episode = filename_split[1].strip()
    season_episode_split = season_episode.split('E')
    return season_episode_split


def extract_episode_number_from_filename(filename):
    # first try episodic file names
    try:
        season_episode_split = extract_season_episode_parts(filename)
        episode_number = int(season_episode_split[1].strip().replace('E', '').replace('-', ''))
        return episode_number
    except IndexError:
        # a IndexError is raised if the episode is not episodic, process it as a day based show YYYY-MM-DD
        pattern = re.compile(r"\d{4}-\d{1,2}-\d{1,2}")
        match = pattern.search(filename)
        if match:
            return match.group(0)
        else:
            raise ValueError(f"Could not determine episode number or date from {filename}")


def extract_episode_name_from_filename(filename):
    filename_split = filename.split(' - ')
    if len(filename_split) != 3:
        # try 'Downton.Abbey.S05E05.HDTV.x264-FTP.mp4' style file name
        regex_pattern = r"(.+)(S\d{1,2}E\d{1,2})(.+)"
        matches = re.match(regex_pattern, filename)
        if not matches or len(matches.groups()) < 3:
            raise Exception("{} split with no parts returned, we will die now".format(filename))
        else:
            ret_value = matches.group(3)
            # if it starts with a `.` then remove it
            if ret_value[0] == ".":
                ret_value = ret_value[1:len(ret_value)]
            # if it starts ith " - " then remove it
            if ret_value[0:3] == " - ":
                ret_value = ret_value[3:len(ret_value)]
            return ret_value
    else:
        return filename_split[2].strip()


def get_show_file_parts(filename):
    """
    a meta function which returns all the parts of the filename in a dict
    """
    return {
        "show": extract_show_from_filename(filename),
        "season": extract_season_from_filename(filename),
        "episode_number": extract_episode_number_from_filename(filename),
        "episode_name": extract_episode_name_from_filename(filename),
        "filename": filename
    }


def get_file_parts_for_directory(directory):
    files = []
    for filename in os.listdir(directory):
        if os.path.isfile(os.path.join(directory, filename)):
            files.append(get_show_file_parts(filename))
        else:
            print("Skipping '{}' since it's not a file".format(filename), flush=True)
    return files


def find_match(source, files):
    for file in files:
        if file['episode_number'] == source['episode_number']:
            return file


def find_show_directory(base_path, show_name):
    """
    Well... it turns out that some files download with "Game of Thrones" while the directory is actually "Game Of
    Thrones", and damn it... it doesn't match... this makes it match!
    :param base_path:
    :param show_name:
    :return:
    """
    shows = []
    p = Path(base_path)
    for x in p.iterdir():
        if x.is_dir():
            shows.append(str(x))
    for show in shows:
        if "{}/{}".format(base_path, show_name.lower()) == show.lower():
            return show
    return None
