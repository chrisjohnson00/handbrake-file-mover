import os
import consul
from datetime import datetime
from app.file_matcher import get_show_file_parts, find_match, get_file_parts_for_directory, find_show_directory
from kafka import KafkaConsumer
from json import loads
import subprocess
import os.path
from prometheus_client import Gauge, start_http_server
from pathlib import Path
from app.utils import is_x265

CONFIG_PATH = "handbrake-file-mover"


def main():
    print("INFO: Starting!!", flush=True)
    start_http_server(8080)
    output_directory_path = get_config("output_directory_path")

    consumer = KafkaConsumer(
        get_config("KAFKA_TOPIC"),
        bootstrap_servers=['kafka-headless.kafka.svc.cluster.local:9092'],
        auto_offset_reset='earliest',
        enable_auto_commit=True,
        group_id=get_consumer_group(),
        value_deserializer=lambda x: loads(x.decode('utf-8')))

    file_discovered_metrics = Gauge('handbrake_job_move_file_in_process', 'File Mover Found A File',
                                    labelnames=["move_type"])
    for message in consumer:
        message_body = message.value
        # message value should be an object with {'filename':'value",'type','tv|movie'}
        # but could also be: {'source_full_path': '/tv/The 100/Season 4/The 100 - S04E01 - Echoes WEBRip-1080p.mkv',
        #     'move_type': 'to_encode', 'type': 'tv', 'quality': '1080p'}
        # move_type is common between the all message types
        move_type = message_body['move_type']
        print("INFO: Processing new message {}".format(message_body), flush=True)
        file_discovered_metrics.labels(move_type).inc()

        if 'filename' in message_body:
            # filename is from the kafka message value
            filename = message_body['filename']
            full_path = os.path.join(output_directory_path, filename)
        elif 'source_full_path' in message_body:
            full_path = message_body['source_full_path']
        if os.path.exists(full_path):
            if move_type == "tv":
                process_tv_move(filename, full_path, move_type)
            elif move_type == "movies":
                process_movie_move(filename, full_path, move_type)
            elif move_type == "to_encode":
                process_to_encode_move(full_path, message_body)
            else:
                print("WARNING: There was an invalid move_type in {}".format(message_body), flush=True)
        else:
            print("{} doesn't exist on disk, skipping processing".format(full_path))

        print("INFO: Done processing message {}".format(message_body), flush=True)
        file_discovered_metrics.labels(move_type).dec()
        # force commit
        consumer.commit_async()


def process_to_encode_move(full_path, message_body):
    """
    to encode is from the download webhook
    :param full_path:
    :param message_body:
    :return:
    """
    # first check to see if the file is already in the needed x265 format, if so, skip encoding
    mediainfo = get_mediainfo(full_path)
    isx265 = False
    for track in mediainfo['media']['track']:
        if track['@type'] == 'Video':
            print("DEBUG: mediainfo: {}".format(track))
            isx265 = is_x265(track)
    if isx265:
        print("INFO: {} is x265 already, skipping encoding".format(full_path), flush=True)
    else:
        print("INFO: {} will be re-encoded".format(full_path), flush=True)
        copy_for_encoding(message_body)


def process_movie_move(filename, full_path, move_type):
    """
    move type movies just puts the movie into plex
    :param filename:
    :param full_path:
    :param move_type:
    :return:
    """
    move_base_path = get_move_directory(move_type)
    # Add the movie name to the move path
    move_path = "{}/{}".format(move_base_path, Path(filename).stem)
    # create the move path
    os.makedirs(move_path, exist_ok=True)
    # move the file!
    move_file(full_path, "{}/{}".format(move_path, filename))


def process_tv_move(filename, full_path, move_type):
    """
    move type tv is used when a tv show is encoded and needs to be put back into Plex. this will replace a matching file
    :param filename:
    :param full_path:
    :param move_type:
    :return:
    """
    move_path = get_move_directory(move_type)
    move_tv_show(filename, full_path, move_path)


def get_mediainfo(full_path):
    """
    This method calls to mediainfo to get all the details of the media file and returns a dict object
    :param full_path: The path to the file
    :return: The mediainfo output as a dict
    """
    command = ['mediainfo', '-f', '--Output=JSON', full_path]
    completed_process = subprocess.run(command, check=True, capture_output=True)
    mediainfo_json = loads(completed_process.stdout)
    return mediainfo_json


def move_tv_show(filename, full_path, move_path):
    # break up the file into it's parts for easy comparison to original file to replace
    source_file_parts = get_show_file_parts(filename)
    # move_path/show/season
    target_dir = "{}/{}".format(find_show_directory(move_path, source_file_parts['show']), source_file_parts['season'])
    target_dir_exists = os.path.isdir(target_dir)
    # let's hope that the original directory is found!
    if target_dir_exists:
        print(
            "INFO: {} - Looking for matching file for '{}' in target directory '{}'".format(
                datetime.now().strftime("%b %d %H:%M:%S"), filename,
                target_dir),
            flush=True)
        file_to_replace = find_match(source_file_parts, get_file_parts_for_directory(target_dir))
        if file_to_replace:
            print(
                "INFO: {} - Replacing '{}' in target directory '{}' with '{}'".format(
                    datetime.now().strftime("%b %d %H:%M:%S"), file_to_replace['filename'],
                    target_dir, source_file_parts['filename']),
                flush=True)
            try:
                target_file_full_path = "{}/{}".format(target_dir, source_file_parts['filename'])
                original_file_full_path = "{}/{}".format(target_dir, file_to_replace['filename'])
                if os.path.exists(target_file_full_path) and os.path.exists(full_path):
                    move_file(full_path, target_file_full_path)
                elif os.path.exists(full_path):
                    copy_file(full_path, target_file_full_path)
                    os.remove(original_file_full_path)
                    os.remove(full_path)
                else:
                    print("WARN: {} - {} was not found".format(datetime.now().strftime("%b %d %H:%M:%S"), full_path))
            except Exception as e:
                raise Exception("Could not copy {}, encountered Exception {}".format(full_path, e))
        else:
            print(
                "WARN: {} - Couldn't match any file in target directory '{}' for '{}'".format(
                    datetime.now().strftime("%b %d %H:%M:%S"), target_dir, source_file_parts['filename']),
                flush=True)
    else:
        print(
            "WARN: {} - SKIPPING '{}', calculated target directory '{}' was not found!!".format(
                datetime.now().strftime("%b %d %H:%M:%S"), filename,
                target_dir),
            flush=True)


def get_consumer_group():
    return get_config("consumer_group")


def get_move_directory(move_type):
    return get_config("move_{}_directory_path".format(move_type))


def get_file_size(file):
    return os.stat(file).st_size


def get_config(key, config_path=CONFIG_PATH):
    if os.environ.get(key):
        return os.environ.get(key)
    print("INFO: looking for {}/{} in consul".format(config_path, key), flush=True)
    c = consul.Consul()
    index, data = c.kv.get("{}/{}".format(config_path, key))
    return data['Value'].decode("utf-8")


def copy_file(src, dest):
    command = ["cp", src, dest]
    print("INFO: {} - File copy command called {}".format(datetime.now().strftime("%b %d %H:%M:%S"), command),
          flush=True)
    subprocess.run(command, check=True)


def move_file(src, dest):
    command = ["mv", src, dest]
    print("INFO: {} - File move command called {}".format(datetime.now().strftime("%b %d %H:%M:%S"), command),
          flush=True)
    subprocess.run(command, check=True)


def copy_for_encoding(message_body):
    """
    Sample message_body: {'source_full_path': '/tv/The 100/Season 4/The 100 - S04E01 - Echoes WEBRip-1080p.mkv',
    'move_type': 'to_encode', 'type': 'tv', 'quality': '1080p'}
    :param message_body: The kafka message to process
    :return:
    """
    copy_path = get_copy_path(message_body['quality'], message_body['type'])
    copy_file(message_body['source_full_path'], "{}/.".format(copy_path))


def get_copy_path(quality, type):
    path = get_config("WATCH_{}_{}".format(quality, type))
    return path


if __name__ == '__main__':
    main()
