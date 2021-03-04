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
    ({'@type': 'Video', 'StreamOrder': '0', 'ID': '1', 'UniqueID': '1450078728267531232', 'Format': 'HEVC',
      'Format_Profile': 'Main 10', 'Format_Level': '4', 'Format_Tier': 'Main', 'CodecID': 'V_MPEGH/ISO/HEVC',
      'Duration': '1439.972000000', 'Width': '1920', 'Height': '1080', 'Stored_Height': '1088', 'Sampled_Width': '1920',
      'Sampled_Height': '1080', 'PixelAspectRatio': '1.000', 'DisplayAspectRatio': '1.778', 'FrameRate_Mode': 'CFR',
      'FrameRate': '29.970', 'FrameCount': '43156', 'ColorSpace': 'YUV', 'ChromaSubsampling': '4:2:0', 'BitDepth': '10',
      'Delay': '0.000', 'Encoded_Library': 'Lavc58.98.100 hevc_nvenc', 'Default': 'Yes', 'Forced': 'No',
      'colour_description_present': 'Yes', 'colour_description_present_Source': 'Container / Stream',
      'colour_range': 'Limited', 'colour_range_Source': 'Container / Stream', 'colour_primaries_Source': 'Stream',
      'transfer_characteristics_Source': 'Stream', 'matrix_coefficients': 'BT.709',
      'matrix_coefficients_Source': 'Container / Stream', 'extra': {'VARIANT_BITRATE': '0'}}, True),

])
def test_is_x265(test_input, expected):
    assert expected == is_x265(test_input)
