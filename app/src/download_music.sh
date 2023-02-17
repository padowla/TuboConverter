#!/bin/sh
#echo "++++++++++++ INIZIO SCRIPT download_music.sh ++++++++++"
URL_video="$1"
output_name="$2"
PATH_DOWNLOAD="/home/pi/MyScript/TelegramBot/Music"
PATH_LOG="/home/pi/MyScript/TelegramBot/mylog"

youtube-dlc -q --extract-audio --audio-format "mp3" $URL_video -o "$PATH_DOWNLOAD/$output_name.%(ext)s" &>> $PATH_LOG
#echo "++++++++++++++++ FINE DEL download_music.sh +++++++++++++++++++"
