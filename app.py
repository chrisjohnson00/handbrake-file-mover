import os
import consul
from app.file_matcher import get_show_file_parts, find_match, get_file_parts_for_directory, find_show_directory
from kafka import KafkaProducer
from kafka.errors import KafkaError
import pulsar
from json import loads, dumps
import subprocess
import os.path
from prometheus_client import Gauge, start_http_server
from pathlib import Path
from app.utils import is_x265
import pygogo as gogo

CONFIG_PATH = "handbrake-file-mover"
# logging setup
kwargs = {}
formatter = gogo.formatters.structured_formatter
logger = gogo.Gogo('struct', low_formatter=formatter).get_logger(**kwargs)


def main():
    logger.info("Starting!!")
    start_http_server(8080)
    output_directory_path = get_config("output_directory_path")

    client = pulsar.Client(f"pulsar://{get_config('PULSAR_SERVER')}")

    file_discovered_metrics = Gauge('handbrake_job_move_file_in_process', 'File Mover Found A File',
                                    labelnames=["move_type"])

    consumer = client.subscribe(get_config('PULSAR_TOPIC'), get_config('PULSAR_SUBSCRIPTION'))

    while True:
        msg = consumer.receive()
        try:
            # decode from bytes, encode with backslashes removed, decode back to a string, then load it as a dict
            message_body = loads(msg.data().decode().encode('latin1', 'backslashreplace').decode('unicode-escape'))
            process_message(file_discovered_metrics, message_body, output_directory_path)
            # Acknowledge successful processing of the message
            consumer.acknowledge(msg)
        except:  # noqa: E722
            # Message failed to be processed
            consumer.negative_acknowledge(msg)

    client.close()


def process_message(file_discovered_metrics, message_body, output_directory_path):
    # message value should be an object with {'filename':'value",'type','tv|movie'}
    # but could also be: {'source_full_path': '/tv/The 100/Season 4/The 100 - S04E01 - Echoes WEBRip-1080p.mkv',
    #     'move_type': 'to_encode', 'type': 'tv', 'quality': '1080p'}
    # move_type is common between the all message types
    logger.info("Processing new message", extra={'message_body': message_body})
    move_type = message_body['move_type']
    file_discovered_metrics.labels(move_type).inc()
    if 'filename' in message_body:
        # filename is from the kafka message value
        filename = message_body['filename']
        full_path = os.path.join(output_directory_path, filename)
    elif 'source_full_path' in message_body:
        full_path = message_body['source_full_path']
    if os.path.exists(full_path):
        if move_type == "tv":
            final_path = process_tv_move(filename, full_path, move_type)
            send_post_move_message(move_type, final_path)
        elif move_type == "movie":
            final_path = process_movie_move(filename, full_path, move_type)
            send_post_move_message(move_type, final_path)
        elif move_type == "to_encode":
            process_to_encode_move(full_path, message_body)
        else:
            logger.warning("There was an invalid move_type", extra={'message_body': message_body})
    else:
        logger.warning("{} doesn't exist on disk, skipping processing".format(full_path))
    logger.info("Done processing message", extra={'message_body': message_body})
    file_discovered_metrics.labels(move_type).dec()


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
            logger.debug("mediainfo", extra={'track': track})
            isx265 = is_x265(track)
    if isx265:
        logger.info(f"{full_path} is x265 already, skipping encoding")
        send_post_move_message(message_body['type'], full_path)
    else:
        logger.info(f"{full_path} will be re-encoded")
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
    final_path = "{}/{}".format(move_path, filename)
    move_file(full_path, final_path)
    return final_path


def process_tv_move(filename, full_path, move_type):
    """
    move type tv is used when a tv show is encoded and needs to be put back into Plex. this will replace a matching file
    :param filename:
    :param full_path:
    :param move_type:
    :return:
    """
    move_path = get_move_directory(move_type)
    return move_tv_show(filename, full_path, move_path)


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
        logger.info(f"Looking for matching file for '{filename}' in target directory '{target_dir}'")
        file_to_replace = find_match(source_file_parts, get_file_parts_for_directory(target_dir))
        if file_to_replace:
            fn = file_to_replace['filename']
            logger.info(f"Replacing '{fn}' in target directory '{target_dir}' with '{source_file_parts['filename']}'")
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
                    logger.warning(f"{full_path} was not found")
            except Exception as e:
                raise Exception("Could not copy {}, encountered Exception {}".format(full_path, e))
        else:
            logger.warning(
                f"Couldn't match any file in target directory '{target_dir}' for '{source_file_parts['filename']}'")
        return target_file_full_path
    else:
        logger.warning(f"SKIPPING '{filename}', calculated target directory '{target_dir}' was not found!!")
    return None


def get_move_directory(move_type):
    return get_config("move_{}_directory_path".format(move_type))


def get_file_size(file):
    return os.stat(file).st_size


def get_config(key, config_path=CONFIG_PATH):
    if os.environ.get(key):
        return os.environ.get(key)
    logger.info(f"looking for {config_path}/{key} in consul")
    c = consul.Consul()
    index, data = c.kv.get("{}/{}".format(config_path, key))
    return data['Value'].decode("utf-8")


def copy_file(src, dest):
    command = ["cp", src, dest]
    logger.info(f"File copy command called {command}")
    subprocess.run(command, check=True)


def move_file(src, dest):
    command = ["mv", src, dest]
    logger.info(f"File move command called {command}")
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


def send_post_move_message(type, file_path):
    # send the message to kafka, if configured
    kafka_server = get_config('KAFKA_SERVER')
    kafka_topic = get_config('KAFKA_TOPIC_POST_MOVE')
    message = {'type': type, 'file_path': file_path}
    if kafka_server and kafka_topic:
        producer = KafkaProducer(bootstrap_servers=[kafka_server],
                                 acks=1,
                                 api_version_auto_timeout_ms=10000,
                                 value_serializer=lambda x:
                                 dumps(x).encode('utf-8'))

        future = producer.send(topic=kafka_topic, value=message)
        try:
            future.get(timeout=60)
        except KafkaError as ke:
            logger.error(f"Kafka error: {ke}")
            raise ke
        logger.info("Sent message {} to {}".format(message, kafka_topic))
    else:
        logger.warning("KAFKA_SERVER or KAFKA_TOPIC was not found in configs, no messages will be sent")


if __name__ == '__main__':
    main()
