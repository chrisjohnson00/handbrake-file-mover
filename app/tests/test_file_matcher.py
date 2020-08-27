from app.file_matcher import extract_show_from_filename, extract_episode_name_from_filename, \
    extract_episode_number_from_filename, extract_season_from_filename, get_show_file_parts
import pytest


@pytest.mark.parametrize("test_input,expected", [('Shameless (US) - S01E01 - Pilot HDTV-720p.mp4', "Shameless (US)"),
                                                 ('Downton.Abbey.S05E05.HDTV.x264-FTP.mp4', "Downton Abbey"), (
                                                         'The Scooby-Doo Show - S01E06 - Scared a Lot in Camelot WEBRip-720p.mkv',  # noqa: E501
                                                         'The Scooby-Doo Show'), (
                                                         'Home Movie - The Princess Bride - S01E09 - Chapter Nine - Have Fun Storming The Castle! WEBDL-1080p.mkv',  # noqa: E501
                                                         "Home Movie - The Princess Bride"),
                                                 ('SpongeBob SquarePants - S10E30-E31 - Company Picnic + Pull Up a Barrel HDTV-720p.mkv',  # noqa: E501
                                                 "SpongeBob SquarePants")])
def test_extract_show_from_filename(test_input, expected):
    assert expected == extract_show_from_filename(test_input)


@pytest.mark.parametrize("test_input,expected", [('Shameless (US) - S01E01 - Pilot HDTV-720p.mp4', "Season 1"),
                                                 ('Downton.Abbey.S05E05.HDTV.x264-FTP.mp4', "Season 5"),
                                                 (
                                                         'The Scooby-Doo Show - S01E06 - Scared a Lot in Camelot WEBRip-720p.mkv',  # noqa: E501
                                                         'Season 1'), (
                                                         'Spongebob SquarePants - s01e28 - SB-129 [480p] [h.265].mkv',
                                                         'Season 1'),
                                                 (
                                                         'Home Movie - The Princess Bride - S01E09 - Chapter Nine - Have Fun Storming The Castle! WEBDL-1080p.mkv',  # noqa: E501
                                                         "Season 1"),
                                                 (
                                                 'SpongeBob SquarePants - S10E30-E31 - Company Picnic + Pull Up a Barrel HDTV-720p.mkv',  # noqa: E501
                                                 'Season 10')])
def test_extract_season_from_filename(test_input, expected):
    assert expected == extract_season_from_filename(test_input)


@pytest.mark.parametrize("test_input,expected", [('Shameless (US) - S01E01 - Pilot HDTV-720p.mp4', 1),
                                                 ('Downton.Abbey.S05E05.HDTV.x264-FTP.mp4', 5), (
                                                         'The Scooby-Doo Show - S01E06 - Scared a Lot in Camelot WEBRip-720p.mkv',  # noqa: E501
                                                         6), (
                                                         'Home Movie - The Princess Bride - S01E09 - Chapter Nine - Have Fun Storming The Castle! WEBDL-1080p.mkv',  # noqa: E501
                                                         9),
                                                 ('SpongeBob SquarePants - S10E30-E31 - Company Picnic + Pull Up a Barrel HDTV-720p.mkv', 30)])  # noqa: E501
def test_extract_episode_number_from_filename(test_input, expected):
    assert expected == extract_episode_number_from_filename(test_input)


@pytest.mark.parametrize("test_input,expected",
                         [('Shameless (US) - S01E01 - Pilot HDTV-720p.mp4', "Pilot HDTV-720p.mp4"),
                          ('Downton.Abbey.S05E05.HDTV.x264-FTP.mp4', "HDTV.x264-FTP.mp4"), (
                                  'The Scooby-Doo Show - S01E06 - Scared a Lot in Camelot WEBRip-720p.mkv',
                                  'Scared a Lot in Camelot WEBRip-720p.mkv'), (
                                  'Home Movie - The Princess Bride - S01E09 - Chapter Nine - Have Fun Storming The Castle! WEBDL-1080p.mkv',  # noqa: E501
                                  "Chapter Nine - Have Fun Storming The Castle! WEBDL-1080p.mkv"),
                          ('SpongeBob SquarePants - S10E30-E31 - Company Picnic + Pull Up a Barrel HDTV-720p.mkv',
                           "Company Picnic + Pull Up a Barrel HDTV-720p.mkv")])
def test_extract_episode_name_from_filename(test_input, expected):
    assert expected == extract_episode_name_from_filename(test_input)


def test_get_show_file_parts():
    """
     "show": extract_show_from_filename(filename),
        "season": extract_season_from_filename(filename),
        "episode_number": extract_episode_number_from_filename(filename),
        "episode_name":
    :return:
    """
    filename = 'Shameless (US) - S01E01 - Pilot HDTV-720p.mp4'
    expected = {
        "show": "Shameless (US)",
        "season": "Season 1",
        "episode_number": 1,
        "episode_name": "Pilot HDTV-720p.mp4",
        "filename": 'Shameless (US) - S01E01 - Pilot HDTV-720p.mp4'
    }
    assert expected == get_show_file_parts(filename)
