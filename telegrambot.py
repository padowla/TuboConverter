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
from telegram.ext import Updater
from telegram.ext import CommandHandler
from telegram.ext import MessageHandler, Filters
from telegram.ext.dispatcher import run_async
from telegram import MessageEntity
import time, threading
from telegram.ext import BaseFilter
from functools import wraps
from telegram import ChatAction

##                                   FILTRI CUSTOM                                                 ##
class FilterPlaylist(BaseFilter):
    def filter(self,message):
        return 'playlist?list' in message.text



##                                   FUNZIONI GLOBALI                                              ##
"""
Questo decoratore parametrizzato ti consente di segnalare diverse azioni a seconda del tipo di risposta del tuo bot.  In questo modo gli utenti avranno un feedback simile dal tuo bot come da un vero essere umano, per essmpio quando sta inviando il video uscirà scritto 'Sta inviando un video...' sotto il nome.
"""
def send_action(action):
        """Sends `action` while processing func command."""

        def decorator(func):
                @wraps(func)
                def command_func(update, context, *args, **kwargs):
                    context.bot.send_chat_action(chat_id=update.effective_message.chat_id, action=action)
                    return func(update, context,  *args, **kwargs)
                return command_func
                                                                
        return decorator


##                 DECORATORI PER GLI HANDLER DELLE CALL BACK           ##                                                                
send_typing_action = send_action(ChatAction.TYPING)


def start(update,context):
    #questa funzione dovrebbe processare uno specifico tipo di aggiornamento dell'update ==> il comando /start
    context.bot.send_message(chat_id=update.effective_chat.id, text="Cosa so fare? Converto un video di Youtube in file audio!!")

def set_cover(path_audiofile,path_cover):
    cmd='eyeD3 --add-image "{path_cover}:FRONT_COVER" {path_audiofile}'.format(path_audiofile=path_audiofile,path_cover=path_cover)
    print(cmd)
    logging.info("[SET COVER ART]\t{path_audiofile} <-> {path_cover}".format(path_audiofile=path_audiofile,path_cover=path_cover))
    os.system(cmd)


def download_title(update,context,URL2conv):
    cmd = "youtube-dl --get-title {URL2conv}".format(URL2conv=URL2conv) 
    logging.info("FINAL COMMAND EXECUTED: {cmd}".format(cmd=cmd))
    out = subprocess.check_output(cmd.split())    
    title = out.decode("utf-8").rstrip("\n") #passo da byte a stringa e rimuovo il newline alla fine
    title_song_rep = title.replace('"', '').replace('/','-').replace('(','').replace(')','').replace('~','-') #tolgo eventuali caratteri che darebbero fastidio nella open dentro la sendAudio
    return title_song_rep
 

"""
    Ritorna il nome del file nel formato IDTHREAD_UNIXTIMESTAMP.ext dove <ext> è mp3
"""

def download_audio(update,context,URL2conv,title_song):
    ext="mp3" #possibilità futura di avere più estensioni
    ID_thread=str(threading.get_ident())
    UNIX_TIMESTAMP=str(int(time.time()))
    formatfilename=ID_thread+'_'+UNIX_TIMESTAMP
    audiofilename="{formatfilename}.{ext}".format(formatfilename=formatfilename,ext=ext) #il nome del file audio
    imagefilename="{ID}.jpg".format(ID=ID_thread) #il nome del file immagine usato come copertina
    PATH_AUDIOCOVER="{PATH_MUSIC}{imagefilename}".format(PATH_MUSIC=PATH_MUSIC,imagefilename=imagefilename)
    PATH_AUDIOFILE="{PATH_MUSIC}{audiofilename}".format(PATH_MUSIC=PATH_MUSIC,audiofilename=audiofilename)
    cmd="youtube-dl -q --add-metadata --embed-thumbnail --extract-audio --audio-format \"{ext}\" {URL2conv} -o {virg}{PATH_AUDIOFILE}{virg}".format(ext=ext,URL2conv=URL2conv,PATH_AUDIOFILE=PATH_AUDIOFILE,virg='"')
    logging.info("[DOWNLOAD AUDIO FILE]\t{title_song} <---> {audiofilename}\t\t >{cmd}".format(title_song=title_song,audiofilename=audiofilename,cmd=cmd) )
    try:
        os.system(cmd) #qui si crea il file su disco...
    except:
        logging.info("[-] ERROR [DOWNLOAD AUDIO FILE]\t {audiofilename} downloaded correctly".format(audiofilename=audiofilename))
        raise DownloadFileError("Error during download file")
    
    logging.info("[DOWNLOAD AUDIO FILE]\t {audiofilename} downloaded correctly".format(audiofilename=audiofilename))
    
    #aggiungo la cover di copertina
    set_cover(PATH_AUDIOFILE,PATH_AUDIOCOVER)

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

    


@run_async
@send_typing_action
def convert_url(update,context,url_builtin = None,count = 0):
    #creo un handler per gestire gli update di Telegram e dunque convertire l'url passato in base alla corrispondenza con una una regex
    if(url_builtin is None):
        URL2conv = update.message.text
    else:
        URL2conv = url_builtin
    if(url_builtin is None):
        context.bot.send_message(chat_id=update.effective_chat.id,text="⏳ATTENDI IL DOWNLOAD ⏳")
    try:
        title_song = download_title(update,context,URL2conv)
    
        PATH_UPLOAD=''
    
        PATH_UPLOAD = download_audio(update,context,URL2conv,title_song)
 
        if(url_builtin is None):
            context.bot.send_message(chat_id=update.effective_chat.id,text="🗃... FILE AUDIO PRONTO PER L'INVIO ...🗃")

        #COSTRUZIONE DEL PATH PER L'UPLOAD DEL SERVER
        logging.info("[PATH_UPLOAD]\t{PATH_UPLOAD}".format(PATH_UPLOAD=PATH_UPLOAD))

        #INVIO DEL FILE AUDIO ALL'UTENTE
        if(url_builtin is not None):
            context.bot.send_message(chat_id=update.effective_chat.id,text="✔DOWNLOAD DELL'AUDIO N°%s" %count )
        context.bot.send_audio(chat_id=update.effective_chat.id,audio=open(PATH_UPLOAD,'rb'),title=title_song)
        os.remove(PATH_UPLOAD)
        logging.info("[DELETED]\t{PATH_UPLOAD}".format(PATH_UPLOAD=PATH_UPLOAD))
 
    except RenameFileError as e:
        context.bot.send_message(chat_id=update.effective_chat.id,text="⚠⚠⚠ERROR DURING RENAME FILE⚠⚠⚠")
        logging.error(str(e))
    except DownloadFileError as e:
        context.bot.send_message(chat_id=update.effective_chat.id,text="⚠⚠⚠ERROR DURING DOWNLOAD FILE⚠⚠⚠")
        logging.error(str(e))
        
@run_async
def convert_playlist(update,context):
    #context.bot.send_message(chat_id=update.effective_chat.id,text="⏳ATTENDI IL DOWNLOAD DELLA PLAYLIST⏳")
    count=0 #contatore per il numero di video inviati
    command_final="youtube-dl -j --flat-playlist " + update.message.text + " | jq -r '.id' | sed 's_^_https://youtu.be/_'"
    #si viene a creare una stringa dove gli urls sono separati l'un l'altro da un carattere di \n...
    list_urls = ((subprocess.check_output(command_final,shell=True)).decode("utf-8")).split('\n')  #creo la stringa con il comando split(\n)
    list_urls.pop() #per eliminare l'ultimo elemento della lista che risulta essere una stringa vuota
    logging.info("list_urls: {lista}".format(lista=list_urls))
    logging.info("DOWNLOAD OF A PLAYLIST  WITH %s AUDIO FILEs",len(list_urls))
    context.bot.send_message(chat_id=update.effective_chat.id,text="⏭ DOWNLOAD IN CORSO DI %s VIDEO DALLA PLAYLIST INVIATA⏮" %len(list_urls) )
    for url in list_urls:
        count+=1
        convert_url(update,context,url,count) #invio il singolo url estratto con il ciclo for alla routine per il download url classico
        

def unknown_command(update,context):
    #Alcuni utenti confusi potrebbero provare ad inviare comandi al bot che non può comprendere in quanto non aggiunti al dispatcher
    #Dunque è possibile usare un MessageHandler con il filtro "command" per rispondere a tutti i comandi che non sono riconosciuti dai precedenti handler
    #Tale Handler deve essere aggiunto come ultimo altrimenti verrebbe attivato prima che CommandHandler abbia la possibilità di
    #poter esaminare l'aggiornamento. Una volta gestito infatti un aggiornamento tutti gli altri gestori vengono ignorati
    #Per aggirare questo fenomeno è possibile  passare l'argomento "group" nel metodo add_handler con un valore intero diverso da 0
    context.bot.send_message(chat_id=update.effective_chat.id,text="Scusami ma non capisco ciò che mi chiedi...")

def unknown_text(update,context):
    #Questa callback gestisce invece il caso in cui si immetta al posto dell'URL o dei comandi validi inseribili del testo che non è riconosciuto come valido
    context.bot.send_message(chat_id=update.effective_chat.id,text="⚠⚠⚠  L'URL inviato non è valido a quanto pare...  ⚠⚠⚠")

def clear_env():
    base_path = "/home/pi/MyScript/TuboConverter/Music"
    WAIT_SECONDS = 86400 #il numero di secondi in un giorno
    with open(PATH_LOG,'w'):
        pass
    #ciclo for che cancella eventuali file o cartelle residue nella directory Music
    for element in os.listdir(base_path):
        full_path = base_path + "/" + element
        if(os.path.isfile(full_path)):
            os.remove(full_path)
        else:
            shutil.rmtree(full_path)
    logging.info("ENVIRONMENT CLEARED")
    threading.Timer(WAIT_SECONDS,clear_env).start() #dopo WAIT_SECONDS il thread che si occupa di pulire il file di log ed eventuali file audio  rimasti incacellati si richiama da solo


#ECCEZIONI USER-DEFINED
"""Base class for other exceptions"""
class Error(Exception):
    pass

"""Error raised when renaming of file fail"""
class RenameFileError(Error):
    pass

######################            

regex_url_single_video = re.compile(
        r'^(?:http|ftp)s?://' # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' #domain...
        r'localhost|' #localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
        r'(?::\d+)?' # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
#________________________________________________________________________________________________________

#PATH GLOBALI
PATH_API='/home/pi/MyScript/TuboConverter/api_telegram'
PATH_LOG='/home/pi/MyScript/TuboConverter/mylog'
PATH_MUSIC="/home/pi/MyScript/TuboConverter/Music/" #occhio allo slash alla fine

#________________________________________________________________________________________________________
#LEGGO DAL FILE api_telegram LA API DEL BOT IN QUESTIONE

with open(PATH_API,'r') as file:

	TOKEN=file.read().replace('\n','') #il replace serve in quanto alla fine del file è presente un carattere di -a capo- da eliminare

#INSTANZIO L'UPDATER
updater = Updater(token=TOKEN,use_context=True,workers=10) #il numero di thread prima era a 40 ma il raspberry andava in crash,dunque lo metto a 10
#il parametro use-context = True è un argomento speciale necessario solamente per la versione 12 della libreria. Il valore di default è False
# Permette di avere una retrocompatibilità con le versioni più vecchie della libreria e dare tempo agli utenti di fare l'upgrade
#Dalla versione 13 sarà True di default

#INSTANZIO IL DISPATCHER
dispatcher = updater.dispatcher #per avere un rapido accesso al Dispatcher usato dall'Updater lo introduco localmente

#INIZIALIZZO IL LOGGING
logging.basicConfig(filename=PATH_LOG,filemode='a',format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',level=logging.INFO)

#INIZIALIZZO LE CLASSI DEI FILTRI
filter_playlist = FilterPlaylist()

#INIZIALIZZO I DIVERSI HANDLER UTILI

#    (1)   #
start_handler = CommandHandler('start',start)
dispatcher.add_handler(start_handler)

#    (2)   #
convert_url_playlist_handler = MessageHandler(Filters.text & Filters.entity(MessageEntity.URL) & filter_playlist,convert_playlist)
dispatcher.add_handler(convert_url_playlist_handler)

#    (3)   #
#ALTERNATIVA ALLA REGEX --> handler = MessageHandler(Filters.text & ( Filters.entity(MessageEntity.URL) | Filters.entity(MessageEntity.TEXT_LINK),callback) se il messaggio è testuale e contiene un link  
convert_url_handler = MessageHandler(Filters.text & Filters.entity(MessageEntity.URL) & Filters.regex(regex_url_single_video),convert_url)
dispatcher.add_handler(convert_url_handler)

#    (4)    #
unknown_text_handler = MessageHandler(Filters.text,unknown_text)
dispatcher.add_handler(unknown_text_handler)

#   !!!!!!  L'HANDLER UNKNOWN COME ULTIMO !!!!!          #
unknown_command_handler = MessageHandler(Filters.command,unknown_command) 
dispatcher.add_handler(unknown_command_handler)
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!#
#    (FINE)   #

#AVVIO IL BOT
updater.start_polling()
clear_env() #pulisco il file di log ogni WAIT_SECONDS secondi
logging.info("SERVER STARTED")
updater.idle() #permette di fermare il bot tramite CTRL+C o altri segnali inviati ovvero esegue il comando updater.stop() quando arriva il segnale
