def is_x265(video_track):
    x265_partials = ['x265', 'HEVC']
    if 'Encoded_Library_Name' in video_track:
        encoded_library_name = video_track['Encoded_Library_Name']
    elif 'CodecID' in video_track:
        encoded_library_name = video_track['CodecID']
    print("DEBUG: encoding {}".format(encoded_library_name))
    for keyword in x265_partials:
        if keyword in encoded_library_name:
            return True
    return False
