ARG WORKING_DIRECTORY=/app

# set base image (host OS)
FROM ubuntu:20.04

# renew in this stage the argument
ARG WORKING_DIRECTORY

ARG DEBIAN_FRONTEND=noninteractive

# set the working directory in the container
WORKDIR $WORKING_DIRECTORY

# copy the content of the local app directory to the working directory
COPY app/ .

# install packages
RUN apt-get update && apt-get install --no-install-recommends -y curl wget musl-dev gcc vim nano python3.8 python3.8-dev python3.8-venv python3-pip python3-wheel build-essential jq youtube-dl ffmpeg id3v2 -y && apt-get clean && rm -rf /var/lib/apt/lists/*

# install python-telegram-bot
RUN pip3 install python-telegram-bot

# install dependencies
RUN pip3 install --no-cache-dir -r requirements.txt

# list copied files
RUN ["ls","-l","-a","-R","."]

# command to run on container start
CMD [ "python3", "src/telegrambot.py" ]
