from karaopy_guts import *
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.uix.button import Button
from kivy.properties import StringProperty
from kivy.properties import ObjectProperty
from kivy.utils import escape_markup
from kivy.factory import Factory
from kivy.config import Config
Config.set('kivy', 'window_icon', "KaraoPy256.png")
Config.set('graphics', 'minimum_width', '800')
Config.set('graphics', 'minimum_height', '600')

with open("KaraoPyUTF8.kv", encoding='utf-8') as f:
    Builder.load_string(f.read())

class InterfaceWidget(BoxLayout):
    
    #Definitions for properties of the UI. I know, it is a lot.
    FONT_NAME_1 = StringProperty('fonts\\NotoSansCJKjp-Medium.otf') #Change the fonts if your language is not displayed correctly
    FONT_NAME_2 = StringProperty('fonts\\NotoSansMonoCJKjp-Regular.otf')
    current_title_prop = ObjectProperty(None)
    current_artist_prop = ObjectProperty(None)
    playlist_list_prop = ObjectProperty(None)
    results_list_prop = ObjectProperty(None)
    search_bar_prop = ObjectProperty(None)
    play_button_prop = ObjectProperty(None)
    stop_button_prop = ObjectProperty(None)
    restart_button_prop = ObjectProperty(None)
    remove_button_prop = ObjectProperty(None)
    search_title_button_prop = ObjectProperty(None)
    search_artist_button_prop = ObjectProperty(None)
    current_time_prop = ObjectProperty(None)
    current_duration_prop = ObjectProperty(None)
    youtube_status_prop = ObjectProperty(None)
    counter_prop = ObjectProperty(None)
    add_button_prop = ObjectProperty(None)

    already_focused = False
    search_enabled = False
    instanced = False
    selected_index = None
    result_buttons_list = []
    buttons = []

    def update(self, dt):

        if self.instanced == False: # Will run only the once when this class is instaced. Kivy and __init__ do not like each other. 
            self.karaoke = KaraokeGuts()
            self.database = Database()
            self.database.check_new_files() # Compares database with files in SONGS folder.
            self.instanced = True

        self.get_add_title() # Verifies if it should add new music to playlist.
        self.get_search() # Gets the search results to display in UI.
        self.get_state() # Gets the state of current video, if any.
        self.karaoke.next_music() # Plays next music in playlist, if any.

        self.update_title() #Self-explanatory methods.
        self.update_artist()
        self.update_duration()
        self.update_time()
        self.update_playlist()
        self.update_download_status()
        self.update_search_bar()
        self.update_search_results()
        self.update_counter()
        self.update_buttons()

    def update_title(self):

        if self.karaoke.current_music != None:
            self.current_title_prop.text = self.karaoke.current_music['Title']
        
        else:
            self.current_title_prop.text = ''
    
    def update_artist(self):
       
        if self.karaoke.current_music != None:
            self.current_artist_prop.text = self.karaoke.current_music['Artist']
       
        elif self.karaoke.timer_flag == False:
            self.current_artist_prop.text = 'Fila vazia: adicione uma música para começar'

        elif self.karaoke.timer_flag == True:
            self.current_artist_prop.text = 'Próxima música em {:2.1f} segundo(s)'.format(self.karaoke.remaining_time)

    def update_duration(self):

        length = self.karaoke.get_length()

        if self.karaoke.internal_state not in ('playing', 'paused') or length in ('', -1):
            self.current_duration_prop.text = ''

        else:
            self.current_duration_prop.text = self.karaoke.format_seconds(length / 1000)

    def update_time(self):

        elapsed = self.karaoke.get_time()

        if self.karaoke.internal_state not in ('playing', 'paused') or elapsed in ('', -1):
            self.current_time_prop.text = ''

        else:
            self.current_time_prop.text = self.karaoke.format_seconds(elapsed / 1000)

    def update_playlist(self):

        playlist_aux2 = ''

        for i in self.karaoke.playlist:
            playlist_aux = playlist_aux2 + '[size=20][color=#FFFFFF][font=NotoSansCJKjp-Medium.otf]' + escape_markup(i['Title']) + '[/color][/size][/font]' + '\n'
            playlist_aux = playlist_aux + '[size=15][color=#c5cacd][font=NotoSansCJKjp-Medium.otf]' + escape_markup(i['Artist']) + ' ' +  escape_markup('[') + self.karaoke.format_seconds(i['Length']) + escape_markup(']') + '[/color][/size][/font]' + '\n\n'
            playlist_aux2 = playlist_aux
        
        self.playlist_list_prop.text = playlist_aux2

    def update_download_status(self):

        status = self.karaoke.get_download_status()

        if status == None:
            try:
                if time.time() - self.status_clock > 60:
                    self.youtube_status_prop.text = ''
            except:
                pass

        
        else:
            percent = status['percent']
            eta = status['eta']

            if percent == 'DOWNLOAD_ERROR':
                status_message = 'Um erro ocorreu ao baixar o vídeo =('
                self.status_clock = time.time()
                
            elif percent == 'UNKNOWN_FILESIZE':
                status_message = 'Baixando, mas tamanho desconhecido'

            elif percent == 'DOWNLOAD_COMPLETED':
                status_message = 'Vídeo baixado!'
                self.status_clock = time.time()

            else:
                if eta == None:
                    status_message = 'Baixando: {:2.1f}% | ETA: Desconhecido'.format(percent)
                else:
                    status_message = 'Baixando: {:2.1f}% | ETA: {}'.format(percent, self.karaoke.format_seconds(eta))

            self.youtube_status_prop.text = status_message

    def update_search_bar(self):

        if self.already_focused == False:
            self.search_bar_prop.do_cursor_movement('cursor_home')
            self.search_bar_prop.text = 'Digite um termo de busca ou cole um link'
            self.add_button_prop.disabled = True

    def update_search_results(self):
        pass

    def update_counter(self):
        self.counter_prop.text = str(self.karaoke.playlist_counter)    

    def update_buttons(self):

        if self.karaoke.internal_state not in ('playing','paused'):
            self.play_button_prop.disabled = True
            self.stop_button_prop.disabled = True
            self.restart_button_prop.disabled = True
       
        else:
            self.play_button_prop.disabled = False
            self.stop_button_prop.disabled = False
            self.restart_button_prop.disabled = False
        
        if self.karaoke.playlist_counter == 0:
            self.remove_button_prop.disabled = True
        else:
            self.remove_button_prop.disabled = False

        if self.search_bar_prop.text == '':
            self.add_button_prop.disabled = True
        
    def get_add_title(self):

        add_result = self.karaoke.get_add_title()

        if add_result == 'ERROR':
            title_btn = Factory.ResultsButtonTitle()
            self.results_list_prop.add_widget(title_btn)
            title_btn.text = 'Erro ao adicionar URL'

        elif add_result == 'INVALID_URL':
            title_btn = Factory.ResultsButtonTitle()
            self.results_list_prop.add_widget(title_btn)
            title_btn.text = 'URL inválida'

    def search(self):

        self.results_list_prop.clear_widgets()
        self.result_buttons_list = []
        self.buttons = []
        self.add_button_prop.disabled = False

        if self.search_enabled != False and self.search_bar_prop.text != '':
            self.karaoke.search(self.search_bar_prop.text, self.search_enabled)

    def get_search(self):

        search_result = self.karaoke.get_search()
        

        if search_result != None:

            if search_result == 'SEARCH_NOT_FOUND':
                
                title_btn = Factory.ResultsButtonTitle()
                self.results_list_prop.add_widget(title_btn)
                title_btn.text = 'Busca não encontrada =('

            else:
                title_btn = Factory.ResultsButtonTitle()
                spacing_btn = Factory.ButtonSpacing()
                artist_btn = Factory.ResultsButtonArtist()
                self.results_list_prop.add_widget(title_btn)
                self.results_list_prop.add_widget(artist_btn)
                self.results_list_prop.add_widget(spacing_btn)
                title_btn.text = search_result['Title']
                artist_btn.text = search_result['Artist'] + ' [' + self.karaoke.format_seconds(search_result['Length']) + ']'
                self.result_buttons_list.append(search_result)
                self.buttons.append({'title_btn': title_btn, 'artist_btn': artist_btn})
                index = len(self.result_buttons_list) - 1
                title_btn.bind(on_press = lambda x: self.choiced(index, 'title'))
                artist_btn.bind(on_press = lambda x: self.choiced(index, 'artist'))

    def choiced(self, index, category):
 
        for i in range(len(self.buttons)):

            if i != index:
                self.buttons[i]['title_btn'].state = 'normal'
                self.buttons[i]['artist_btn'].state = 'normal'
            
            else:

                if category == 'title':
                    self.buttons[index]['artist_btn'].state = 'down'
                
                else:
                    self.buttons[index]['title_btn'].state = 'down'

        self.selected_index = index
        
    def add_title(self):

        if self.search_enabled != False and self.selected_index != None:
            self.karaoke.add_title(self.result_buttons_list[self.selected_index], add_type = 'database')
        
        elif self.search_bar_prop.text != '': 
            self.results_list_prop.text = ''
            input_text = self.search_bar_prop.text
            self.karaoke.add_title(input_text, add_type = 'youtube')
            #title_btn.text = 'Processando...'
        
        self.search_selection_reset()
        self.already_focused = False
        self.update_search_bar()
        self.results_list_prop.clear_widgets()
        self.result_buttons_list = []
        self.selected_index = None
        
    def remove_title(self):
        
        self.karaoke.remove_title()
    
    def stop(self):
        
        self.karaoke.stop()
    
    def play(self):

        self.karaoke.play()
        
        if self.karaoke.internal_state == 'paused':
            self.play_button_prop.background_normal = "buttons\\play.png"
            self.play_button_prop.background_down = "buttons\\play_clicked.png"
        
        else:
            self.play_button_prop.background_normal = "buttons\\pause.png"
            self.play_button_prop.background_down = "buttons\\pause_clicked.png"
      
    def restart(self):
        
        self.karaoke.restart()
        self.play_button_prop.background_normal = "buttons\\pause.png"
        self.play_button_prop.background_down = "buttons\\pause_clicked.png"

    def get_state(self):

        state = self.karaoke.get_state()
        return state

    def search_bar_focused(self, focus):

        if focus == True:
            self.search_bar_prop.text = ''
            self.already_focused = True

    def search_selection(self, search_type):
        
        if search_type == 'Title':
            self.search_artist_button_prop.state = 'normal'
            self.search_enabled = 'Title'

        elif search_type == 'Artist':
            self.search_title_button_prop.state = 'normal'
            self.search_enabled = 'Artist'

        if self.search_title_button_prop.state == 'normal' and self.search_artist_button_prop.state == 'normal':
            self.search_enabled = False

        self.already_focused = True
        self.search_bar_prop.text = ''
        self.search()

    def search_selection_reset(self):
        
        self.search_title_button_prop.state = 'normal' 
        self.search_artist_button_prop.state = 'normal'
        self.search_enabled = False

class KaraoPyApp(App):
    def build(self):
        iw = InterfaceWidget()
        Clock.schedule_interval(iw.update, 0)
        return iw

if __name__ == '__main__':
    KaraoPyApp().run()