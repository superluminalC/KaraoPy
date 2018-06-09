# KaraoPy
A simple software written in Python/Kivy focused on download (karaoke or not) videos from Youtube and make a automatic playlist from it. 

## Why did you make it?
After I could not make a reserve at a commercial karaoke with my friends, I made a party at home using a very simple Python/Kivy program to add URLs of karaoke videos from Youtube, download it, put in a playlist and play automatically in a TV connected do my notebook. I had time and energy to make it from a very small hobby project to a not-so-small-I-spend-too-much-time-on-this-help-me, resulting in this shit -- I mean, the beautifully constructed Python program. 

## Why should I use it?
If you don't want to download youtube videos, this program is not for you. You may just add your videos to a youtube playlist. But, if you want to save them in your PC, or use videos from other websites that do not support playlist (refer to youtube-dl repository to see a list of supported websites), this may be for you. 

## Features
* Downloads video from Youtube (or any youtube-dl supported site), saves in a folder and puts in a playlist
* Uses vlc as player
* Simple csv database where the metadata from videos is stored
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
*    py -m pip install kivy
*    py -m pip install youtube-dl
*    py -m pip install vlc



