# -*- encoding: utf-8 -*-
import vlc
import youtube_dl
import threading as th
import queue
import multiprocessing as mp 
import csv
import time
import os
import hashlib
from pathlib import Path
from collections import deque

# This should be in a config file, not implemented. Change it to reflect your desired configuration.
CSV_HEADER = ['Title','Artist','Length','Path','MD5']
DATABASE_FILE = 'karaoke_database.csv'
SONGS_PATH = 'songs'
VLC_PATH = 'F:\\VLC\\vlc.exe'
WAIT_TO_NEXT_SONG = 10 # In seconds. Change it to 0 to play the next on playlist immediately.

# Media class (and others) are run in separate PROCESS. Kivy and threads don't like each other.
class Media(mp.Process):

    states = {
            0: 'nothing',
            1: 'opening',
            2: 'buffering',
            3: 'playing',
            4: 'paused',
            5: 'stopped',
            6: 'ended',
            7: 'error',
             }

    def __init__(self, q_get = None, q_put = None):

        mp.Process.__init__(self)

        if q_get != None and q_put != None:
            self.q_put = q_put
            self.q_get = q_get
            #self.__create_vlc()

            self.send_response = {'state': '', 'time': '', 'length': ''}

        else:
            raise Exception('You should put both queues.')

    def run(self):
        
        self.__create_vlc()

        while 1:
            q = self.q_get.get()
            self.__vlc_control(file_path = q[0], command = q[1])
            self.q_put.put(self.send_response)
            self.send_response = {'state': '', 'time': '', 'length': ''}

    def __create_vlc(self):
        
        import vlc
        self.media = vlc.MediaPlayer()
        self.media.set_fullscreen(False)

    def __vlc_control(self, file_path = '', command = ''):

        if file_path != '' and command != '':
            
            if command == 'play':
                self.media.set_mrl(file_path)
                self.media.play()
                
        elif file_path == '' and command != '':

            if command == 'pause':
                self.media.pause()
            
            elif command == 'play':
                self.media.play()
            
            elif command == 'stop':
                self.media.stop()
            
            elif command == 'get_state':
                state = self.states[self.media.get_state()]
                self.send_response['state'] = state
            
            elif command == 'get_time':
                elapsed = self.media.get_time()
                self.send_response['time'] = elapsed
            
            elif command == 'get_length':
                length = self.media.get_length()
                self.send_response['length'] = length

            elif command == 'get_info': # It is redundant, I used it for a test but will be difficult to change back.
                elapsed = self.media.get_time()
                state = self.states[self.media.get_state()]

                if state in ('ended', 'error'):
                    self.media.stop()

                length = self.media.get_length()
                self.send_response.update({'time': elapsed, 'state': state, 'length': length})

        else:
            raise Exception('File path without commands, or both argumens empty.')

class Database():

    def database_read(self):

        try:
            with open(DATABASE_FILE, 'r', encoding = 'utf-8') as f:
                csv_dict = csv.DictReader(f, delimiter = '|') # Don't worry, fields with | will be escaped with quotes around the field.
                
                if csv_dict.fieldnames != CSV_HEADER:
                    raise Exception('The file is not a valid database.')
       
        except FileNotFoundError:
            print('Database not found; will be created.')
            self.__create_csv()
            csv_dict = None

        finally:
            csv_buffer = []

            try:
                with open(DATABASE_FILE, 'r', encoding = 'utf-8') as f:
                    csv_dict = csv.DictReader(f, delimiter = '|')

                    for row in csv_dict:
                        csv_buffer.append(dict(row))

            except:
                print('Something strange occured while reading the file.')
                return 'READ_ERROR'

            return csv_buffer

    def __create_csv(self):

        try:
            with open(DATABASE_FILE, 'w', encoding = 'utf-8') as f:
                csv_dict = csv.DictWriter(f, delimiter = '|', fieldnames = CSV_HEADER)
                csv_dict.writeheader()
        except:
            print('Something strange occured while writing on file.')

    # Important: this method will be run in separate and unkillable thread (while running), due safety. 
    # Do not use it other way, or database can become corrupted.
    def database_write(self, metadata, reset_db = False, q = None):
        ''' In this method, metadata should be a dict. 'reset_db' if you want to clear the database and
        populate with new metadatas. In 'q' you should put a queue if you want to execute it as
        thread or process.'''

        if reset_db == False:
            csv_dict = self.database_read()
            csv_dict.append(metadata)

        else:
            csv_dict = metadata

        try:
            with open(DATABASE_FILE, 'w', encoding = 'utf-8') as f:
                csv_object = csv.DictWriter(f, delimiter = '|', fieldnames = CSV_HEADER)
                csv_object.writeheader()
                csv_object.writerows(csv_dict)

                if q != None:
                    q.put('WRITE_OK')
                
        except Exception as e:
            print('Something strange occured while writing on file.', e)
            if q != None:
                q.put('WRITE_ERROR')
            #write_q.put('WRITE_ERROR')
            #return 'WRITE_ERROR'

    # This method is a modified version from imohash library function, because it was easy and fast do adapt.
    # Thanks, man!
    def hashfile(self, filepath, sample_threshold = 128 * 1024, sample_size = 16 * 1024): 
        '''This method returns MD5 from PARTS of the file, due speed, because a video file
        can have gigabytes.''' 

        size = os.path.getsize(filepath)

        with open(filepath, 'rb') as f:
            if size < sample_threshold or sample_size < 1:
                data = f.read()
            else:
                data = f.read(sample_size)
                f.seek(size//2)
                data += f.read(sample_size)
                f.seek(-sample_size, os.SEEK_END)
                data += f.read(sample_size)
            data += str(size).encode()

        return hashlib.md5(data).hexdigest()

    def sort_dict(self, data_to_be_sorted, dict_key):
        ''' This method only allows dicts to be sorted. '''

        sorted_dict = sorted(data_to_be_sorted, key = lambda x: x[dict_key].lower())
        return sorted_dict 
    
    def check_new_files(self):
        ''' This method scan the SONGS_PATH folder for files manually copied into, or if the database
        became "lost" and do not reflect the files in folder. '''

        songs_folder = Path(SONGS_PATH)
        filetypes = ['*.mpg','*.avi','*.mp4','*.mkv','*.webm','*.flv','*.3gp']
        exists_in_folder_not_in_db_list = []
        to_write = []
        search = SearchTools()

        csv_dict = self.database_read()

        if csv_dict != 'READ_ERROR':

            for i in csv_dict:
                pobj = Path(i['Path'])

                if pobj.exists() == True and i['MD5'] == self.hashfile(i['Path']):
                    to_write.append(i)

            sorted_path = self.sort_dict(csv_dict, 'Path')

            for i in filetypes:
                globbed = songs_folder.glob(i)
                
                for j in globbed:

                    result_gen = search.binary_search_gen(sorted_path, str(j), 'Path')
                    result = next(result_gen)

                    if result == 'SEARCH_NOT_FOUND':     
                        exists_in_folder_not_in_db_list.append(j)

            for i in exists_in_folder_not_in_db_list:
                media = vlc.MediaPlayer(str(i))
                metadata = media.get_media()
                metadata.parse()
                length = str(metadata.get_duration() / 1000)
                dict_elem = {fieldname: '' for fieldname in CSV_HEADER}
                md5 = self.hashfile(i)
                dict_elem['Title'] = i.stem
                dict_elem['Length'] = length
                dict_elem['Path'] = str(i)
                dict_elem['MD5'] = md5
                to_write.append(dict_elem)
                
            #write_q = queue.Queue()
            write_th = th.Thread(target=self.database_write, args=(to_write,), kwargs={'reset_db': True,})    
            write_th.start()
            #write_result = write_q.get()
            #self.database_write(to_write, reset_db = True)

class SearchTools():

    def binary_search_gen(self, dict_to_be_searched, search_term, key):
        ''''dict_to_be_sorted' must be, well, a dict. 'key' is the key to search in dict. Remember:
        this method returns a fucking generator. Use it in the right way.'''

        if len(dict_to_be_searched) == 0:
            yield 'SEARCH_NOT_FOUND'

        else:
            indexes = self.__search_bisect(dict_to_be_searched, search_term, key)

            if indexes == None:
                yield 'SEARCH_NOT_FOUND'

            else:
                for i in range(indexes[0], indexes[1] + 1):
                    yield dict_to_be_searched[i]    

    #Modified from python examples in their docs.
    def __search_bisect(self, dict_to_be_searched, term, key, low = 0, high = None):
        '''This method returns the indexes of first match and last match inside a ORDERED dict. Anything
        between them, inclusive them, is a match for the term searched.'''

        if low < 0:
            raise ValueError('low must be non-negative')
        if high == None:
            high = len(dict_to_be_searched) - 1
        
        length = len(dict_to_be_searched)
        term = term.lower()

        while low < high:
            mid = (low + high) // 2
            if term <= dict_to_be_searched[mid][key].lower():
                high = mid
            else:
                low = mid + 1
        
        if dict_to_be_searched[low][key].lower().startswith(term) == True: 
            first_match = low
        else:
            return None

        low = first_match
        high = length
        while low < high:
            mid = (low + high) // 2
            if dict_to_be_searched[mid][key].lower().startswith(term) == True:
                low = mid + 1
            else:
                high = mid
        last_match = low - 1

        return [first_match, last_match]          

# The youtube-dl blocks while downloading. It should be run in separate thread or process.
class VideoDownload(mp.Process):

    def __init__(self, q_get = None, q_put = None, q_status_put = None):
        
        mp.Process.__init__(self)

        if q_get != None and q_put != None and q_status_put != None:
            self.q_put = q_put
            self.q_get = q_get
            self.q_status_put = q_status_put
            self.search = SearchTools()
            self.download_status = {'percent': None, 'eta': None}
            self.database = Database()
            self.search = SearchTools()

        else:
            raise Exception('You should put all queues.')

    def run(self):
        
        while 1:

            try:
                url = self.q_get.get(block = False)

            except queue.Empty:
                pass
            
            else:

                metadata = self.__download(url)
                self.q_put.put(metadata)

    def __download_status(self, status):
        
        if status['status'] == 'downloading':
            downloaded_bytes = status['downloaded_bytes']
            total_bytes = status['total_bytes']
            eta = status['eta']

            if total_bytes == None:
                self.download_status['percent'] = 'UNKNOWN_FILESIZE'
                self.download_status['eta'] = None

            else:
                self.download_status['percent'] = downloaded_bytes / total_bytes * 100
                self.download_status['eta'] = eta

        elif status['status'] == 'finished':
            self.download_status['percent'] = 'DOWNLOAD_COMPLETED'
            self.download_status['eta'] = None
        
        elif status['status'] == 'error':
            self.download_status['percent'] = 'DOWNLOAD_ERROR'
            self.download_status['eta'] = None

        self.q_status_put.put(self.download_status)
  
    def __download(self, url):
        
        ydl_opts = {
                    'outtmpl': SONGS_PATH + '\\%(title)s.%(ext)s.temp', 
                    'progress_hooks': [self.__download_status]
                   }
        
        try:
            # The length of video from youtube and from vlc are different because from youtube
            # you get a int, from vlc, a float.
            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                metadata = ydl.extract_info(url, download = True)
                title = metadata.get('title')
                #length = metadata.get('duration')
                temp_path = ydl.prepare_filename(metadata)
                md5 = self.database.hashfile(temp_path)
                md5_db = self.database.database_read()
                md5_sorted = self.database.sort_dict(md5_db, 'MD5')
                md5_result_gen = self.search.binary_search_gen(md5_sorted, md5, key = 'MD5')
                md5_result = next(md5_result_gen)

                if md5_result == 'SEARCH_NOT_FOUND': #If the file doesn't exists in database. Here,
                    # I've compared only the hashes to verify if file exists.
                    path = os.path.splitext(temp_path)[0]
                    os.replace(temp_path, path)
                    media = vlc.MediaPlayer(str(path))
                    metadata = media.get_media()
                    metadata.parse()
                    length = str(metadata.get_duration() / 1000)
                    metadata = {'Title': title, 'Artist': '', 'Length': length, 'Path': path, 'MD5': md5}
                    write_q = queue.Queue()
                    write_th = th.Thread(target = self.database.database_write, args = (metadata,), kwargs = {'q': write_q,})
                    write_th.run()
                    write_result = write_q.get()
                    #write_result = self.database.database_write(metadata)

                    if write_result == 'WRITE_OK':
                        return metadata

                    else:
                        return 'ERROR'

                else: #If the file already exists.
                    os.remove(temp_path)
                    return md5_result

        except:
            return 'INVALID_URL'

# Again, it should run in separate thread or process because in large databases it could be
# take significative time to search.
class IncrementalSearch(mp.Process):

    def __init__(self, q_get = None, q_put = None):

        mp.Process.__init__(self)

        if q_get != None and q_put != None:
                self.q_put = q_put
                self.q_get = q_get
                self.search = SearchTools()
                self.database = Database()

        else:
            raise Exception('You should put both queues.')

    def run(self):

        while 1:

            try:
                search_parameters = self.q_get.get()

            except queue.Empty:
                pass

            else:
                input_text = search_parameters['search_term']
                search_by = search_parameters['search_by']
                data = self.database.database_read()
                sorted_data = self.database.sort_dict(data, search_by)
                search_gen = self.search.binary_search_gen(sorted_data, input_text, search_by)

                for i in search_gen:
                    self.q_put.put(i)

class KaraokeGuts():
    ''' This class is the core of the program. All UI objects should get info from a instance of it.'''

    youtube_list = deque()
    playlist = deque()
    current_music = None
    youtube_list_counter = 0
    playlist_counter = 0
    internal_state = None # This atributte compansate the delay in vlc actual state of the video.
    timer_flag = False
    pre_play = False
    remaining_time = WAIT_TO_NEXT_SONG

    def __init__(self):

        self.q_youtube_put = mp.Queue()
        self.q_youtube_get = mp.Queue()
        self.q_youtube_status_get = mp.Queue()
        self.q_search_put = mp.Queue()
        self.q_search_get = mp.Queue()
        self.q_vlc_put = mp.Queue()
        self.q_vlc_get = mp.Queue()

        self.video_download_p = VideoDownload(self.q_youtube_put, self.q_youtube_get, self.q_youtube_status_get)
        self.incremental_search_p = IncrementalSearch(self.q_search_put, self.q_search_get)
        self.media_p = Media(self.q_vlc_put, self.q_vlc_get)

        self.video_download_p.daemon = True
        self.incremental_search_p.daemon = True
        self.media_p.daemon = True

        self.video_download_p.start()
        self.incremental_search_p.start()
        self.media_p.start()
       
    def add_title(self, input_text, add_type = None):
        '''Puts new music in playlist. 'input_text' can be a dict (if 'add_type' is 'database') or
        a youtube (or other video service supported by youtube-dl) (str) url (if 'add_type' is 'youtube').'''

        if add_type == 'database':
            self.__add_from_database(input_text)
        
        elif add_type == 'youtube': 
            self.__add_from_youtube(input_text)

    def get_add_title(self):
        '''Gets the result of trying add a new title to playlist.'''
        try:
            metadata = self.q_youtube_get.get(block = False)

            if metadata not in ('ERROR', 'INVALID_URL'):
                self.playlist.append(metadata)
                self.playlist_counter += 1

            else:
                return metadata

        except queue.Empty:
            pass


    def remove_title(self):
        '''Removes a music from playlist.'''

        if self.playlist_counter > 0:
            self.playlist.pop()
            self.playlist_counter -= 1

        self.timer_flag = False
    
    def stop(self):
        '''Stops the current playing music.'''

        self.q_vlc_put.put(['', 'stop'])
        self.internal_state = 'stopped'

    def play(self, path = None):
        '''Change between play and pause states of current music. If 'path' is a valid path to a file,
        it will play such file.'''

        if path == None:

            if self.internal_state == 'paused':
                self.q_vlc_put.put(['', 'play'])
                self.internal_state = 'playing'

            elif self.internal_state == 'playing':
                self.q_vlc_put.put(['', 'pause'])
                self.internal_state = 'paused'
       
        else:
            self.q_vlc_put.put([path, 'play'], block = False)
            self.internal_state = 'playing'
 
    def restart(self):
        '''Restarts the current playing music.'''
        self.playlist.appendleft(self.current_music)
        self.playlist_counter += 1
        self.stop()
        self.current_music = None
           
    def get_download_status(self):
        '''Gets information about the download of the video from youtube.'''

        try:
            status = self.q_youtube_status_get.get(block = False)
            
        except queue.Empty:
            pass
        
        else:

            if status['percent'] in ('DOWNLOAD_COMPLETED', 'DOWNLOAD_ERROR'):
                #self.youtube_list.pop()
                self.youtube_list_counter -= 1

            return status

    def get_state(self):
        '''Gets the state of music. If playing, paused, stopped, etc.'''
 
        self.q_vlc_put.put(['', 'get_info'])
        state = self.q_vlc_get.get()

        if state['state'] != '':
            self.internal_state = state['state']

            if self.internal_state in ('playing', 'paused'):
                self.pre_play = False

        return state['state']


    def get_time(self):
        '''Gets the current time of the video.'''

        self.q_vlc_put.put(['', 'get_info'])
        elapsed = self.q_vlc_get.get()
        return elapsed['time']

    def get_length(self):
        '''Gets the duration of the video.'''

        self.q_vlc_put.put(['', 'get_info'])
        length = self.q_vlc_get.get()
        return length['length']


    def next_music(self):
        '''Plays the next on playlist, if any.'''

        if self.playlist_counter > 0 and self.internal_state not in ('playing','paused'):
            
            if self.timer_flag == True:
                self.remaining_time = self.timer()

            else:
                self.initial_time = time.time()

            self.timer_flag = True
            
            if self.remaining_time <= 0:
                self.timer_flag = False
                self.pre_play = True
                self.remaining_time = WAIT_TO_NEXT_SONG    
                self.play(path = self.playlist[0]['Path'])
                self.current_music = self.playlist[0]
                self.remove_title()

        elif self.playlist_counter == 0 and self.internal_state not in ('playing','paused') and self.pre_play == False:
            self.current_music = None

    def format_seconds(self, seconds):
        '''Transforms a int or float 'seconds' in a formatted string of the format hh:mm:ss.'''
        
        if isinstance(seconds, str) == True:
            seconds = float(seconds)

        days = 0

        if seconds >= 86400:
            days = int(seconds // 86400)
            seconds = seconds - days * 86400
        
        hours = int(seconds // 3600)
        seconds = seconds - hours * 3600

        minutes = int(seconds // 60)
        seconds = int(seconds - minutes * 60)

        if days > 0:
            formatted_time = '{} d {:02d}:{:02d}:{:02d}'.format(days, hours, minutes, seconds) 

        elif hours > 0:
            formatted_time = '{:02d}:{:02d}:{:02d}'.format(hours, minutes, seconds) 

        else:
            formatted_time = '{:02d}:{:02d}'.format(minutes, seconds) 

        return formatted_time

    def search(self, search_term, search_by):
        '''Searchs the str 'search_term' in category 'search_by'. The latter must be a valid key to
        a dict where 'search_term' will be, well, searched.'''

        search_parameters = {'search_term': search_term, 'search_by': search_by}
        self.q_search_put.put(search_parameters)

    def get_search(self):
        '''Gets the search result after method 'search' was called. Will return a dict or error message.'''

        try:
            search_result = self.q_search_get.get(block = False)
            
        except queue.Empty:
            pass

        else:

            return search_result

    def timer(self):
        '''Returns how much time until the next music on playlist will be played. Change the constant
        'WAIT_TO_NEXT_SONG' if you want... change this time.'''

        remaining_time = WAIT_TO_NEXT_SONG - (time.time() - self.initial_time)
        return remaining_time

        # initial_time = time.time()
        # self.remaining_time = WAIT_TO_NEXT_SONG

        # while self.remaining_time > 0:             
        #     self.remaining_time = WAIT_TO_NEXT_SONG - (time.time() - initial_time)

    def __add_from_youtube(self, url):
        
        try:
            self.q_youtube_put.put(url, block = False)
            #self.youtube_list.append(url)
            self.youtube_list_counter += 1
        
        except queue.Full:
            pass

    def __add_from_database(self, input_text):

        self.playlist.append(input_text)
        self.playlist_counter += 1




    
    


        


        






        
       
        
        
        
        
    