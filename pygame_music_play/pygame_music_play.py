# -*- coding: utf-8 -*-
"""
Created on Wed Oct 12 10:05:45 2016

@author: wattai
"""

import pygame.mixer as mix
import threading
from time import sleep
import sys
import sounddevice as sd
import soundfile as sf

def mplay(path):
    #mix.init()#frequency = 16000, size = -16, channels = 1, buffer = int(1024/2)) # 初期化消さない!!!
    #mix.music.load(path)
    #mix.music.play()
    
    #sound = mix.Sound(path)
    #sound.play()
    
    wave, fs = sf.read(path)
    sd.play(wave, fs)

class MusicPlayThread(threading.Thread):
    def __init__(self, path):
        super(MusicPlayThread, self).__init__()
        self._mpath = path
        self._falg = False

    def run(self):
        mplay(self._mpath)
        self._flag = True
        
if __name__ == "__main__":
    
    th = MusicPlayThread("./I'm sorry by kagami.wav")
    th.start()
    
    sec = 0
    while True:
        sys.stdout.write("\rNow Playing... %d" %(sec))
        sys.stdout.flush()
        sleep(1)
        sec += 1
        #if th._flag == True:
        #    break
    