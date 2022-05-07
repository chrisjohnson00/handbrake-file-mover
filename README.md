Run locally

Export the path to your in/out dir, then run the app

    export watch_directory_path=/home/chris/Documents/output
    export move_directory_path=/home/chris/Documents/Television

    python app.py
    
Running tests

    python -m pytest

PyPi Dependency updates

    docker run -it --rm -v ${PWD}:/repo -w /repo python:3.8-slim bash

Then inside the container:

    pip install --upgrade pip
    pip install --upgrade kafka-python pulsar-client python-consul prometheus-client pygogo fastavro==0.24.0
    pip freeze > requirements.txt
    sed -i '/pkg_resources/d' requirements.txt

`pulsar-client` does not support Python 3.9
