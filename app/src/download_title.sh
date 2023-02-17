#!/bin/sh

URL_video="$1"
PATH_DOWNLOAD="/home/pi/MyScript/TelegramBot/Music"

title=`youtube-dl --get-title $URL_video`
echo -n $title #> "$PATH_DOWNLOAD/.name_song"
#echo "+++++++++++++++ FINE SCRIPT download_title.sh +++++++++++"
