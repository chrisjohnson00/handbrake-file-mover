def extract_show_from_filename(filename):
    """
    Take input like 'Shameless (US) - S01E01 - Pilot HDTV-720p.mp4' and return it's show name
    """
    filename_split = filename.split('-')
    return filename_split[0].strip()


def extract_season_from_filename(filename):
    filename_split = filename.split('-')
    season_episode = filename_split[1].strip()
    season_episode_split = season_episode.split('E')
    season_number = int(season_episode_split[0].strip().replace('S', ''))
    return "Season {}".format(season_number)


def extract_episode_number_from_filename(filename):
    filename_split = filename.split('-')
    season_episode = filename_split[1].strip()
    season_episode_split = season_episode.split('E')
    episode_number = int(season_episode_split[1].strip().replace('E', ''))
    return episode_number


def extract_episode_name_from_filename(filename):
    filename_split = filename.split('-')
    return filename_split[2].strip()


def get_show_file_parts(filename):
    """
    a meta function which returns all the parts of the filename in a dict
    """
    return {
        "show": extract_show_from_filename(filename),
        "season": extract_season_from_filename(filename),
        "episode_number": extract_episode_number_from_filename(filename),
        "episode_name": extract_episode_name_from_filename(filename)
    }
