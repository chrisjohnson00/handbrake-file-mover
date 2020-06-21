import os
import consul
import shutil
from datetime import datetime
from app.file_matcher import get_show_file_parts, find_match, get_file_parts_for_directory
from kafka import KafkaConsumer
from json import loads
import os.path
from os import path

CONFIG_PATH = "handbrake-file-mover"
SLEEP_TIME = 61


def main():
    print("Starting!!", flush=True)
    directory = "/watch"

    consumer = KafkaConsumer(
        'completedHandbrakeEncoding',
        bootstrap_servers=['kafka-headless.kafka.svc.cluster.local:9092'],
        auto_offset_reset='earliest',
        enable_auto_commit=True,
        group_id=get_consumer_group(),
        value_deserializer=lambda x: loads(x.decode('utf-8')))

    for message in consumer:
        message_body = message.value
        print("Processing new message {}".format(message_body), flush=True)

        # message value should be an object with {'filename':'value",'type','tv|movie'}
        # filename is from the kafka message value
        filename = message_body['filename']
        move_type = message_body['move_type']
        full_path = os.path.join(directory, filename)

        if path.exists(full_path):
            if move_type == "tv":
                move_path = get_move_directory(move_type)
                move_tv_show(filename, full_path, move_path)
            elif move_type == "movies":
                move_path = get_move_directory(move_type)
                move_movie(filename, full_path, move_path)
            else:
                print("WARNING: There was no type in {}".format(message_body), flush=True)
        else:
            print("WARNING: {} is not found on disk".format(full_path))


def move_movie(filename, full_path, move_path):
    shutil.move(full_path, "{}/{}".format(move_path, filename))


def move_tv_show(filename, full_path, move_path):
    # break up the file into it's parts for easy comparison to original file to replace
    source_file_parts = get_show_file_parts(filename)
    # move_path/show/season
    target_dir = "{}/{}/{}".format(move_path, source_file_parts['show'], source_file_parts['season'])
    target_dir_exists = path.isdir(target_dir)
    # let's hope that the original directory is found!
    if target_dir_exists:
        print(
            "{} - Looking for matching file for '{}' in target directory '{}'".format(
                datetime.now().strftime("%b %d %H:%M:%S"), filename,
                target_dir),
            flush=True)
        file_to_replace = find_match(source_file_parts, get_file_parts_for_directory(target_dir))
        if file_to_replace:
            print(
                "{} - Replacing '{}' in target directory '{}' with '{}'".format(
                    datetime.now().strftime("%b %d %H:%M:%S"), file_to_replace['filename'],
                    target_dir, source_file_parts['filename']),
                flush=True)
            try:
                target_file_full_path = "{}/{}".format(target_dir, source_file_parts['filename'])
                original_file_full_path = "{}/{}".format(target_dir, file_to_replace['filename'])
                if path.exists(target_file_full_path):
                    shutil.move(full_path, target_file_full_path)
                else:
                    shutil.copyfile(full_path, target_file_full_path)
                    os.remove(original_file_full_path)
            except Exception as e:
                raise Exception("Could not copy {}, encountered Exception {}".format(full_path, e))
        else:
            print(
                "{} - Couldn't match any file in target directory '{}' for '{}'".format(
                    datetime.now().strftime("%b %d %H:%M:%S"), target_dir, source_file_parts['filename']),
                flush=True)
    else:
        print(
            "{} - SKIPPING '{}', calculated target directory '{}' was not found!!".format(
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
    print("looking for {}/{} in consul".format(config_path, key), flush=True)
    c = consul.Consul()
    index, data = c.kv.get("{}/{}".format(config_path, key))
    return data['Value'].decode("utf-8")


if __name__ == '__main__':
    main()
