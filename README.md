# KaraoPy
A simple software written in Python/Kivy focused on download (karaoke or not) videos from Youtube and make a automatic playlist from it. 

## Why did you make it?
After I could not make a reserve at a commercial karaoke with my friends, I made a party at home using a very simple Python/Kivy program to add URLs of karaoke videos from Youtube, download it, put in a playlist and play automatically in a TV connected do my notebook. I had time and energy to make it from a very small hobby project to a not-so-small-I-spend-too-much-time-on-this-help-me, resulting in this shit -- I mean, the beautifully constructed Python program. 

## Why should I use it?
If you don't want to download youtube videos, this program is not for you. You may just add your videos to a youtube playlist. But, if you want to save them in your PC, or use videos from other websites that do not support playlist (refer to youtube-dl repository to see a list of supported websites), this may be for you.

## Features
* Downloads video from Youtube (or any youtube-dl supported site), saves in a folder and puts in a playlist
* Uses VLC as player
* Simple csv database where the metadatas from videos are stored
* Integrated database search

## How to use

### Supported devices
This code was written in Python 3.6.4, using Kivy 1.10.0, in a Windows 10 64-bit machine. **I can not guarantee that this program will work even in such configuration. Freely make the necessary adaptations to run in your machine if you want.**

### External dependencies
This software needs the following external Python modules:
* Kivy
* youtube-dl
* vlc

Because I don't know how to carry this imports around, you should download it manually. Make sure to have your Python installation in `PATH` in your Windows. Open the command prompt and type:
* `py -m pip install kivy`
* `py -m pip install youtube-dl`
* `py -m pip install vlc`

### Before execute it
Just after the first imports of script, change the global variable `VLC_PATH` to the folder where the `vlc.exe` is installed. Remember to use double backslashes (\\) if you are in Windows. Moreover, I recommend you to change the global variable `WAIT_TO_NEXT_SONG` to a value that fit your desires.

### Known bugs
* Kivy
* No support for search using IME (eg. Japanese characters), due limitation of... Kivy. I discovered a half-assed workaround, but I have not implemented yet
* High CPU usage (~80% in my Core i5 2nd generation)
* High memory usage
* Me
* Have I already said Kivy?

## FAQ (Frequently Asked Questions)

### Can I manually copy videos to `songs` folder?
Yes. Every time the program executes, it checks the folder for new (or deleted) files and update the database accordingly.

### Can I manually delete videos from `songs` folder?
Yes, read question above.

### How do I modify the metadata of my videos?
Open the `karaoke_database.csv`, located in the folder you have put your `KaraoPy.py`. The fields are separated by a (not commom) vertical bar (|). Change the respective title and artist field for each entry. Do not change the others fields!

### Why does KaraoPy spawn three different processes?
Because Kivy. I searched a lot for a solution with no avail. If I use thread, the user interface become very, VERY laggy. I had to live with it.

### Why the fuck does KaraoPy uses 80% of my CPU?
Good question, I would like to know too. If you know how to solve, send me a message.

### Why the user interface display messages is in a strange language?
Because it is Hue lang-I mean, Portuguese. You can change that messages if you want. Almost all the variables in code are self-explanatory.

### KaraoPy... Kara oPy... oPy... hey, is it a innuendo?
Sure.







