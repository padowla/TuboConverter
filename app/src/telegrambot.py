
# -*- coding: utf-8 -*-


'''
    MADE WITH API FROM telegram-bot-api INSTALLED WITH PIP INSTALL...
    https://python-telegram-bot.org/
'''
import os
import subprocess
import logging
import re
import shutil
from telegram.ext import Updater, Application, CommandHandler, MessageHandler, filters, ConversationHandler, ContextTypes
from telegram import Bot, Update
from telegram import MessageEntity
import time, threading
from functools import wraps
import mutagen
from mutagen.easyid3 import EasyID3
from telegram.ext.filters import MessageFilter

#                                      PATH GLOBALI                                                ##
PATH_API='config/api_telegram'
PATH_LOG='mylog'
PATH_MUSIC='Music/' #occhio allo slash alla fine


#                                    VARIABILI GLOBALI                                             ##
PLAYLIST_NAME, PLAYLIST_PICTURE = range(2)
CMD_YOUTUBEDL = "yt-dlp"


# Initialize logging
logging.basicConfig(filename=PATH_LOG,filemode='a',format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',level=logging.INFO)


##                                    FILTRI CUSTOM                                                ##
class FilterPlaylist(MessageFilter):
    def filter(self,message):
        return 'playlist?list' in message.text


##                                   FUNZIONI GLOBALI                                              ##

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    #questa funzione dovrebbe processare uno specifico tipo di aggiornamento dell'update ==> il comando /start
    update.effective_chat.send_message("Cosa so fare?Converto un video di Youtube in file audio!!")

'''
    Set ID3 tag on audio file.
'''
def set_id3_tag(file_path, cover_path=None, title=None, artist=None, albumartist=None, album=None, genre=None,track_num=None, total_track_num=None, disc_num=None, total_disc_num=None):

    tags = EasyID3(file_path)

    if cover_path:
        cmd='lame --ti "{cover_path}" "{file_path}"'.format(file_path=file_path,cover_path=cover_path)
        logging.info("SET COVER ART\t{file_path} <-> {cover_path}".format(file_path=file_path,cover_path=cover_path))
        os.system(cmd)
    if title:
        tags['title'] = title
    if artist:
        tags['artist'] = artist
    if albumartist:
        tags['albumartist'] = albumartist
    if album:
        tags['album'] = album
        logging.info("SET ALBUM TITLE\t{file_path} <-> {album}".format(file_path=file_path,album=album))
    if genre:
        tags['genre'] = genre
    if total_track_num:
        if track_num:
            tags['tracknumber'] = '{}/{}'.format(track_num, total_track_num)
        else:
            tags['tracknumber'] = '/{}'.format(total_track_num)
    else:
        if track_num:
            tags['tracknumber'] = '{}'.format(track_num)
    if total_disc_num:
        if disc_num:
            tags['discnumber'] = '{}/{}'.format(disc_num, total_disc_num)
        else:
            tags['discnumber'] = '/{}'.format(total_disc_num)
    else:
        if track_num:
            tags['discnumber'] = '{}'.format(disc_num)

    tags.save()

def download_title(update: Update, context: ContextTypes.DEFAULT_TYPE,URL2conv) -> str:
    cmd = CMD_YOUTUBEDL + " --get-title {URL2conv}".format(URL2conv=URL2conv)
    logging.info("FINAL COMMAND EXECUTED: {cmd}".format(cmd=cmd))
    out = subprocess.check_output(cmd.split())
    title = out.decode("utf-8").rstrip("\n") #passo da byte a stringa e rimuovo il newline alla fine
    title_song_rep = title.replace('"', '').replace('/','-').replace('(','').replace(')','').replace('~','-') #tolgo eventuali caratteri che darebbero fastidio nella open dentro la sendAudio
    return title_song_rep


'''
   Salva l'url della playlist da scaricare.
   Ritorna lo stato successivo
'''
def playlist_url_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["playlist_url"] = update.message.text
    logging.info("PLAYLIST URL: {pl}".format(pl=context.user_data["playlist_url"]))
    query_playlist_name(update, context)
    return PLAYLIST_NAME


'''
   Chiede all'utente di inserire il nome dell'album/playlist
'''
async def query_playlist_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text('🔤 Type the playlist/album name 🔤:')


'''
    Salva il nome della playlist inserito dall'utente.
    Ritorna lo stato successivo.
'''
def playlist_name_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["playlist_name"] = update.message.text
    logging.info("PLAYLIST NAME TYPED BY USER: {pl}".format(pl=context.user_data["playlist_name"]))
    query_playlist_image(update, context)
    return PLAYLIST_PICTURE


'''
   Chiede all'utente di inviare l'immagine dell'album/playlist
'''
async def query_playlist_image(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text('🖼 Send the image of playlist/album 🖼:')


'''
    Salva l'immagine della playlist inviata dall'utente.
    Ritorna lo stato successivo.
'''
def playlist_picture_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    audiocover_id = update.message.photo[-1].file_id
    audiocover_image = context.bot.getFile(audiocover_id)
    logging.info("[DOWLOAD AUDIOCOVER FILE]\t downloading {audiocover_id}...".format(audiocover_id=audiocover_id))
    audiocover_image_name = get_format_filename() + ".jpg"
    path_audiocover="{PATH_MUSIC}{audiocover_image_name}".format(PATH_MUSIC=PATH_MUSIC,audiocover_image_name=audiocover_image_name)
    audiocover_image.download("{path_audiocover}".format(path_audiocover=path_audiocover))
    logging.info("[DOWLOADED AUDIOCOVER FILE]\t {path_audiocover} downloaded correctly".format(path_audiocover=path_audiocover))
    context.user_data["playlist_picture"] = path_audiocover
    logging.info("PLAYLIST PICTURE PATH: {pl}".format(pl=context.user_data["playlist_picture"]))
    convert_playlist(update, context)
    return ConversationHandler.END


'''
    Ritorna il formato nome per i file: IDTHREAD_UNIXTIMESTAMP.ext
'''
def get_format_filename():
    ID_thread=str(threading.get_ident())
    UNIX_TIMESTAMP=str(int(time.time()))
    return ID_thread+'_'+UNIX_TIMESTAMP

'''
    Ritorna il nome del file nel formato IDTHREAD_UNIXTIMESTAMP.ext dove <ext> è mp3
'''
def download_audio(update: Update, context: ContextTypes.DEFAULT_TYPE,URL2conv,title_song,path_audiocover=None,album_title="") -> str:
    ext = "mp3"
    format_filename = get_format_filename()
    audiofilename = format_filename + "." + ext #il nome del file audio
    PATH_AUDIOFILE="{PATH_MUSIC}{audiofilename}".format(PATH_MUSIC=PATH_MUSIC,audiofilename=audiofilename)
    cmd = CMD_YOUTUBEDL + " -q --add-metadata --embed-thumbnail --format bestaudio --extract-audio --audio-format \"{ext}\" --audio-quality 160K {URL2conv} -o {virg}{PATH_AUDIOFILE}{virg}".format(ext=ext,URL2conv=URL2conv,PATH_AUDIOFILE=PATH_AUDIOFILE,virg='"')
    logging.info("[DOWNLOAD AUDIO FILE]\t{title_song} <---> {audiofilename}\t\t >{cmd}".format(title_song=title_song,audiofilename=audiofilename,cmd=cmd) )
    try:
        os.system(cmd) #qui si crea il file su disco...
    except:
        logging.info("[-] ERROR [DOWNLOAD AUDIO FILE]\t {audiofilename} downloaded correctly".format(audiofilename=audiofilename))
        raise DownloadFileError("Error during download file")

    logging.info("[DOWNLOAD AUDIO FILE]\t {audiofilename} downloaded correctly".format(audiofilename=audiofilename))

    # add id3 tags
    set_id3_tag(file_path=PATH_AUDIOFILE,cover_path=path_audiocover, album=album_title)

    #rinomino il file audio
    new_filename=r"{title_song}.{ext}".format(title_song=title_song,ext=ext)
    new_path=r"{PATH_MUSIC}{new_filename}".format(PATH_MUSIC=PATH_MUSIC,new_filename=new_filename)

    try:
        os.rename(PATH_AUDIOFILE,new_path)
    except:
        logging.info("[-] ERROR [RENAME FILE]\t {audiofilename} ---> {NEW_NAME}".format(audiofilename=audiofilename,NEW_NAME=new_path))
        raise RenameFileError("Error during renaming the file")

    logging.info("[RENAME AUDIO FILE]\t {audiofilename} renamed to {NEW_NAME} correctly".format(audiofilename=audiofilename,NEW_NAME=new_path))

    #cancello i file annessi al file principale (.jpg,.tmp.mp3)
    #cmd_rm_junk=r"rm -rf {PATH_MUSIC}{files_junk}*".format(PATH_MUSIC=PATH_MUSIC,files_junk=formatfilename)
    #os.system(cmd_rm_junk)

    return new_path


async def convert_url(update: Update, context: ContextTypes.DEFAULT_TYPE,url_builtin = None,count = 0,path_audiocover=None,album_title="") -> None:
    #creo un handler per gestire gli update di Telegram e dunque convertire l'url passato in base alla corrispondenza con una una regex
    if(url_builtin is None):
        URL2conv = update.message.text
    else:
        URL2conv = url_builtin
    if(url_builtin is None):
        await update.message.reply_text("⏳ATTENDI IL DOWNLOAD ⏳")
    try:
        title_song = download_title(update,context,URL2conv)
        PATH_UPLOAD = ''
        PATH_UPLOAD = download_audio(update,context,URL2conv,title_song,path_audiocover,album_title)

        if(url_builtin is None):
            await update.message.reply_text("🗃... FILE AUDIO PRONTO PER L'INVIO ...🗃")

        #COSTRUZIONE DEL PATH PER L'UPLOAD DEL SERVER
        logging.info("[PATH_UPLOAD]\t{PATH_UPLOAD}".format(PATH_UPLOAD=PATH_UPLOAD))

        #INVIO DEL FILE AUDIO ALL'UTENTE
        if(url_builtin is not None):
            update.message.reply_text("✔DOWNLOAD DELL'AUDIO N°%s" %count )
        await update.effective_chat.send_audio(audio=open(PATH_UPLOAD,'rb'),title=title_song)
        os.remove(PATH_UPLOAD)
        logging.info("[DELETED]\t{PATH_UPLOAD}".format(PATH_UPLOAD=PATH_UPLOAD))
    except RenameFileError as e:
        update.message.reply_text("⚠⚠⚠ERROR DURING RENAME FILE⚠⚠⚠")
        logging.error(str(e))
    except DownloadFileError as e:
        update.message.reply_text("⚠⚠⚠ERROR DURING DOWNLOAD FILE⚠⚠⚠")
        logging.error(str(e))


async def convert_playlist(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    #context.bot.send_message(chat_id=update.effective_chat.id,text="⏳ATTENDI IL DOWNLOAD DELLA PLAYLIST⏳")
    count=0 #contatore per il numero di video inviati
    command_final = CMD_YOUTUBEDL + " -j --flat-playlist " + context.user_data["playlist_url"] + " | jq -r '.id' | sed 's_^_https://youtu.be/_'"
    #si viene a creare una stringa dove gli urls sono separati l'un l'altro da un carattere di \n...
    list_urls = ((subprocess.check_output(command_final,shell=True)).decode("utf-8")).split('\n')  #creo la stringa con il comando split(\n)
    list_urls.pop() #per eliminare l'ultimo elemento della lista che risulta essere una stringa vuota
    logging.info("list_urls: {lista}".format(lista=list_urls))
    playlist_name = context.user_data["playlist_name"]
    playlist_picture = context.user_data["playlist_picture"]
    logging.info("DOWNLOAD OF A PLAYLIST  WITH %s AUDIO FILEs",len(list_urls))
    await update.message.reply_text("⏭ DOWNLOAD IN CORSO DI %s VIDEO DALLA PLAYLIST INVIATA⏮" %len(list_urls) )
    for url in list_urls:
        count+=1
        convert_url(update,context,url,count,playlist_picture,playlist_name) #invio il singolo url estratto con il ciclo for alla routine per il download url classico


def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    #Alcuni utenti confusi potrebbero provare ad inviare comandi al bot che non può comprendere in quanto non aggiunti al dispatcher
    #Dunque è possibile usare un MessageHandler con il filtro "command" per rispondere a tutti i comandi che non sono riconosciuti dai precedenti handler
    #Tale Handler deve essere aggiunto come ultimo altrimenti verrebbe attivato prima che CommandHandler abbia la possibilità di
    #poter esaminare l'aggiornamento. Una volta gestito infatti un aggiornamento tutti gli altri gestori vengono ignorati
    #Per aggirare questo fenomeno è possibile  passare l'argomento "group" nel metodo add_handler con un valore intero diverso da 0
    update.message.reply_text("Scusami ma non capisco ciò che mi chiedi..")

async def unknown_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    #Questa callback gestisce invece il caso in cui si immetta al posto dell'URL o dei comandi validi inseribili del testo che non è riconosciuto come valido
    await update.message.reply_text("⚠⚠⚠  L'URL inviato non è valido a quanto pare...  ⚠⚠⚠")

def clear_env():
    WAIT_SECONDS = 86400 #il numero di secondi in un giorno
    with open(PATH_LOG,'w'):
        pass
    #ciclo for che cancella eventuali file o cartelle residue nella directory Music
    for element in os.listdir(PATH_MUSIC):
        full_path = PATH_MUSIC + element
        if(os.path.isfile(full_path)):
            os.remove(full_path)
        else:
            shutil.rmtree(full_path)
    logging.info("ENVIRONMENT CLEARED")
    threading.Timer(WAIT_SECONDS,clear_env).start() #dopo WAIT_SECONDS il thread che si occupa di pulire il file di log ed eventuali file audio  rimasti incacellati si richiama da solo


#ECCEZIONI USER-DEFINED
'''Base class for other exceptions'''
class Error(Exception):
    pass

'''Error raised when renaming of file fail'''
class RenameFileError(Error):
    pass

'''Error raised when downloading of file fail'''
class DownloadFileError(Error):
    pass

######################

regex_url_single_video = re.compile(
        r'^(?:http|ftp)s?://' # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' #domain...
        r'localhost|' #localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
        r'(?::\d+)?' # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)

def main() -> None:
    """Start the bot"""
    #LEGGO DAL FILE api_telegram LA API DEL BOT IN QUESTIONE
    with open(PATH_API,'r') as file:
        TOKEN=file.read().replace('\n','') #il replace serve in quanto alla fine del file è presente un carattere di -a capo- da eliminare

    application = Application.builder().token(TOKEN).build()

    #INIZIALIZZO LE CLASSI DEI FILTRI
    filter_playlist = FilterPlaylist()

    # Initialize different handlers

    #    (1)   #
    application.add_handler(CommandHandler('start',start))

    #    (2)   #
    playlist_handler = ConversationHandler(
    entry_points=[MessageHandler(filters.TEXT & filters.Entity(MessageEntity.URL) & filter_playlist, playlist_url_handler)],
    fallbacks=[],
    states={
        PLAYLIST_NAME: [MessageHandler(filters.TEXT, playlist_name_handler)],
        PLAYLIST_PICTURE: [MessageHandler(filters.Document.IMAGE | filters.PHOTO, playlist_picture_handler)]
    })
    application.add_handler(playlist_handler)

    #    (3)   #
    #ALTERNATIVA ALLA REGEX --> handler = MessageHandler(Filters.text & ( Filters.entity(MessageEntity.URL) | Filters.entity(MessageEntity.TEXT_LINK),callback) se il messaggio è testuale e contiene un link
    application.add_handler(MessageHandler(filters.TEXT & filters.Entity(MessageEntity.URL) & filters.Regex(regex_url_single_video),convert_url))

    #    (4)    #
    application.add_handler(MessageHandler(filters.TEXT,unknown_text))

    #    (5)    #
    #dispatcher.add_handler(MessageHandler(filters.photo, playlist_picture_handler,run_async=True))

    #    (6)    #
    #dispatcher.add_handler(MessageHandler(filters.text, playlist_name_handler,run_async=True))


    #   !!!!!!  L'HANDLER UNKNOWN COME ULTIMO !!!!!          #
    application.add_handler(MessageHandler(filters.COMMAND,unknown_command))
    #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!#
    #    (FINE)   #

    #AVVIO IL BOT
    application.run_polling()
    clear_env() #pulisco il file di log ogni WAIT_SECONDS secondi
    logging.info("SERVER STARTED")


if __name__ == "__main__":
    main()
