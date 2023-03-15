FROM python:3.11-slim

WORKDIR /usr/src/app

RUN apt-get update && \
    apt-get install mediainfo -y && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD [ "python", "./app.py" ]
