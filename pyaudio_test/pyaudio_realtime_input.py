# -*- coding: utf-8 -*-
"""
Created on Tue Aug 16 21:28:37 2016

@author: wattai
"""

# -*- coding:utf-8 -*-

import pyaudio

CHUNK=1024*2
RATE=16000
p=pyaudio.PyAudio()

stream=p.open(	format = pyaudio.paInt16,
              channels = 2,
              rate = RATE,
              frames_per_buffer = CHUNK,
              input = True,
              output = True) # inputとoutputを同時にTrueにする


def audio_trans(input):
    # なんかしらの処理
    
    ret = input  
    
    
    return ret

while stream.is_active():
    input = stream.read(CHUNK)

    input = audio_trans(input)
    
    output = stream.write(input)
	
stream.stop_stream()
stream.close()
p.terminate()

print("Stop Streaming")