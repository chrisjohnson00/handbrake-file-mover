import os
import consul
import shutil
import time
from datetime import datetime
from app.file_matcher import get_show_file_parts, find_match, get_file_parts_for_directory

CONFIG_PATH = "handbrake-file-mover"
SLEEP_TIME = 61


def main():
    directory = get_watch_directory()
    move_path = get_move_directory()
    while True:
        for filename in os.listdir(directory):
            full_path = os.path.join(directory, filename)
            file_size = get_file_size(full_path)
            print(
                "{} - Found '{}' and it's size is {}".format(datetime.now().strftime("%b %d %H:%M:%S"), filename,
                                                             file_size),
                flush=True)
            time.sleep(SLEEP_TIME)
            # loop until the file size stops growing
            while file_size != get_file_size(full_path):
                print(
                    "{} - File is still growing, waiting".format(datetime.now().strftime("%b %d %H:%M:%S")),
                    flush=True)
                file_size = get_file_size(full_path)
                time.sleep(SLEEP_TIME)

            # break up the file into it's parts for easy comparison to original file to replace
            source_file_parts = get_show_file_parts(filename)
            # move_path/show/season
            target_dir = "{}/{}/{}".format(move_path, source_file_parts['show'], source_file_parts['season'])
            target_dir_exists = os.path.isdir(target_dir)
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
                    # remove the original file, then move the new one in place
                    os.remove("{}/{}".format(target_dir, file_to_replace['filename']))
                    shutil.move(full_path, "{}/{}".format(target_dir, source_file_parts['filename']))
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
        time.sleep(SLEEP_TIME)


def get_watch_directory():
    return get_config("watch_directory_path")


def get_move_directory():
    return get_config("move_directory_path")


def get_file_size(file):
    return os.stat(file).st_size


def get_config(key, config_path=CONFIG_PATH):
    if os.environ.get(key):
        return os.environ.get(key)
    c = consul.Consul()
    index, data = c.kv.get("{}/{}".format(config_path, key))
    return data['Value'].decode("utf-8")


if __name__ == '__main__':
    main()
