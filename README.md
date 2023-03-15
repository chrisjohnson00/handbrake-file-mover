Run locally

Export the path to your in/out dir, then run the app

    export watch_directory_path=/home/chris/Documents/output
    export move_directory_path=/home/chris/Documents/Television

    python app.py
    
Running tests

    python -m pytest

PyPi Dependency updates

    docker run -it --rm -v ${PWD}:/repo -w /repo python:3.10-slim bash

Then inside the container:

    pip install --upgrade pip
    pip install --upgrade pulsar-client python-consul prometheus-client pygogo fastavro
    pip freeze > requirements.txt
    sed -i '/pkg_resources/d' requirements.txt

