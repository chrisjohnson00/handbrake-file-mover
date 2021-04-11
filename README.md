Run locally

Export the path to your in/out dir, then run the app

    export watch_directory_path=/home/chris/Documents/output
    export move_directory_path=/home/chris/Documents/Television

    python app.py
    
Running tests

    python -m pytest

PyPi Dependency updates

    pip install --upgrade pip
    pip install --upgrade kafka-python python-consul prometheus-client pygogo
    pip freeze > requirements.txt
    sed -i '/pkg-resources/d' requirements.txt
