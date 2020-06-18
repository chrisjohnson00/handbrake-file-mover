import os
import re


def extract_show_from_filename(filename):
    """
    Take input like 'Shameless (US) - S01E01 - Pilot HDTV-720p.mp4' and return it's show name
    """
    filename_split = filename.split('-')
    # if the file doesn't match the standard pattern
    if len(filename_split) < 3:
        # try 'Downton.Abbey.S05E05.HDTV.x264-FTP.mp4' style file name
        regex_pattern = r"(.+)\.(S\d{1,2}E\d{1,2})\.(.+)"
        matches = re.match(regex_pattern, filename)
        if not matches or len(matches.groups()) < 3:
            raise Exception("{} split with no parts returned, we will die now".format(filename))
        else:
            return matches.group(1)
    else:
        return filename_split[0].strip()


def extract_season_from_filename(filename):
    season_episode_split = extract_season_episode_parts(filename)
    season_number = int(season_episode_split[0].strip().replace('S', ''))
    return "Season {}".format(season_number)


def extract_season_episode_parts(filename):
    filename_split = filename.split('-')
    if len(filename_split) < 3:
        # try 'Downton.Abbey.S05E05.HDTV.x264-FTP.mp4' style file name
        regex_pattern = r"(.+)\.(S\d{1,2}E\d{1,2})\.(.+)"
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
    season_episode_split = extract_season_episode_parts(filename)
    episode_number = int(season_episode_split[1].strip().replace('E', ''))
    return episode_number


def extract_episode_name_from_filename(filename):
    filename_split = filename.split('-')
    if len(filename_split) < 3:
        # try 'Downton.Abbey.S05E05.HDTV.x264-FTP.mp4' style file name
        regex_pattern = r"(.+)\.(S\d{1,2}E\d{1,2})\.(.+)"
        matches = re.match(regex_pattern, filename)
        if not matches or len(matches.groups()) < 3:
            raise Exception("{} split with no parts returned, we will die now".format(filename))
        else:
            return matches.group(3)
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
