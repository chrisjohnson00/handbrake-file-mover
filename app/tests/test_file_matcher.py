from app.file_matcher import extract_show_from_filename, extract_episode_name_from_filename, \
    extract_episode_number_from_filename, extract_season_from_filename, get_show_file_parts
import pytest


@pytest.mark.parametrize("test_input,expected", [('Shameless (US) - S01E01 - Pilot HDTV-720p.mp4', "Shameless (US)"),
                                                 ('Downton.Abbey.S05E05.HDTV.x264-FTP.mp4', "Downton.Abbey")])
def test_extract_show_from_filename(test_input, expected):
    assert expected == extract_show_from_filename(test_input)


def test_extract_season_from_filename():
    filename = 'Shameless (US) - S01E01 - Pilot HDTV-720p.mp4'
    assert "Season 1" == extract_season_from_filename(filename)


def test_extract_episode_number_from_filename():
    filename = 'Shameless (US) - S01E01 - Pilot HDTV-720p.mp4'
    assert 1 == extract_episode_number_from_filename(filename)


def test_extract_episode_name_from_filename():
    filename = 'Shameless (US) - S01E01 - Pilot HDTV-720p.mp4'
    assert "Pilot HDTV" == extract_episode_name_from_filename(filename)


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
        "episode_name": "Pilot HDTV",
        "filename": 'Shameless (US) - S01E01 - Pilot HDTV-720p.mp4'
    }
    assert expected == get_show_file_parts(filename)
