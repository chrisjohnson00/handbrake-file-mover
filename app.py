import os
import consul
from datetime import datetime
from app.file_matcher import get_show_file_parts, find_match, get_file_parts_for_directory
from kafka import KafkaConsumer
from json import loads
import subprocess
import os.path
from prometheus_client import Gauge, start_http_server

CONFIG_PATH = "handbrake-file-mover"


def main():
    print("INFO: Starting!!", flush=True)
    start_http_server(8080)
    directory = get_config("output_directory_path")

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

        if move_type == "tv":
            # filename is from the kafka message value
            filename = message_body['filename']
            full_path = os.path.join(directory, filename)
            move_path = get_move_directory(move_type)
            move_tv_show(filename, full_path, move_path)
        elif move_type == "movies":
            # filename is from the kafka message value
            filename = message_body['filename']
            full_path = os.path.join(directory, filename)
            move_path = get_move_directory(move_type)
            move_movie(filename, full_path, move_path)
        elif move_type == "to_encode":
            copy_for_encoding(message_body)
        else:
            print("WARNING: There was an invalid move_type in {}".format(message_body), flush=True)

        print("INFO: Done processing message {}".format(message_body), flush=True)
        file_discovered_metrics.labels(move_type).dec()


def move_movie(filename, full_path, move_path):
    move_file(full_path, "{}/{}".format(move_path, filename))


def move_tv_show(filename, full_path, move_path):
    # break up the file into it's parts for easy comparison to original file to replace
    source_file_parts = get_show_file_parts(filename)
    # move_path/show/season
    target_dir = "{}/{}/{}".format(move_path, source_file_parts['show'], source_file_parts['season'])
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
                    print("INFO - {} - {} was not found".format(datetime.now().strftime("%b %d %H:%M:%S"), full_path))
            except Exception as e:
                raise Exception("Could not copy {}, encountered Exception {}".format(full_path, e))
        else:
            print(
                "INFO: {} - Couldn't match any file in target directory '{}' for '{}'".format(
                    datetime.now().strftime("%b %d %H:%M:%S"), target_dir, source_file_parts['filename']),
                flush=True)
    else:
        print(
            "INFO: {} - SKIPPING '{}', calculated target directory '{}' was not found!!".format(
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
    print("File copy command called {}".format(command), flush=True)
    subprocess.run(command, check=True)


def move_file(src, dest):
    command = ["mv", src, dest]
    print("File move command called {}".format(command), flush=True)
    subprocess.run(command, check=True)


def copy_for_encoding(message_body):
    """
    Sample message_body: {'source_full_path': '/tv/The 100/Season 4/The 100 - S04E01 - Echoes WEBRip-1080p.mkv',
    'move_type': 'to_encode', 'type': 'tv', 'quality': '1080p'}
    :param message_body: The kafka message to process
    :return:
    """
    copy_path = get_copy_path(message_body['quality'])
    copy_file(message_body['source_full_path'], "{}/.".format(copy_path))


def get_copy_path(quality):
    return get_config("WATCH_{}".format(quality))


if __name__ == '__main__':
    main()
