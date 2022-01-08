#!/bin/sh

#echo "++++++++++++ INIZIO SCRIPT download_playlist_title.sh ++++++++++"

URL_playlist="$1"

PATH_DOWNLOAD="/home/pi/MyScript/TelegramBot/Music"

youtube-dlc -s --flat-playlist $URL_playlist -o "(playlist_title)s.%(ext)s" #&>> $PATH_LOG
#	DA FARE DOPO
#./download_playlist_title.sh https://www.youtube.com/playlist?list=PLukIQhHGD2GfWexbZRiKXbSGfTnVtPWtn | sed '2!d' | cut -f 2 -d ":"

#echo "++++++++++++++++ FINE DEL download_playlist_title.sh +++++++++++++++++++"
