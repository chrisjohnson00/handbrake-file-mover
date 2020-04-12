import os
import consul
import shutil
import time
from datetime import datetime

CONFIG_PATH = "handbrake-file-mover"


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
            time.sleep(10)
            # loop until the file size stops growing
            while file_size != get_file_size(full_path):
                print(
                    "{} - File is still growing, waiting".format(datetime.now().strftime("%b %d %H:%M:%S")),
                    flush=True)
                file_size = get_file_size(full_path)
                time.sleep(10)

            #     print(
            #     "{} - Moving '{}' to '{}/{}'".format(datetime.now().strftime("%b %d %H:%M:%S"), full_path, move_path,
            #                                          filename),
            #     flush=True)
            # shutil.move(full_path, "{}/{}".format(move_path, filename))
            # file, extension = os.path.splitext(filename)
        time.sleep(10)


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
