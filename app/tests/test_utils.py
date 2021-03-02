from app.utils import is_x265
import pytest


@pytest.mark.parametrize("test_input,expected", [
    ({'CodecID': 'foobar'}, False),
    ({'CodecID': 'V_MS/VFW/FOURCC / WVC1'}, False),
    ({'CodecID': 'avc1'}, False),
    ({'Encoded_Library_Name': 'x264'}, False),
    ({'CodecID': 'V_MPEG4/ISO/AVC'}, False),
    ({'CodecID': 'V_MPEGH/ISO/HEVC'}, True),
    ({'Encoded_Library_Name': 'x265'}, True),

])
def test_is_x265(test_input, expected):
    assert expected == is_x265(test_input)
