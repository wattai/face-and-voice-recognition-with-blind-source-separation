# -*- coding: utf-8 -*-
"""
Created on Wed Aug 17 01:20:51 2016

@author: wattai
"""

import pyaudio
import wave
import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '/../bss')
import stft_iva_istft as iva
import numpy as np
import scipy as sp
import soundfile as sf


if __name__=="__main__":
    
    sw = 1
    if sw==0:
        
        CHUNK = 1024*2
        FORMAT = pyaudio.paInt16 # int16型
        CHANNELS = 1             # ステレオ
        RATE = 16000             # 16[kHz]
        RECORD_SECONDS = 10       # 5秒録音
        INPUT_FILENAME = "input2.wav"
        
        p = pyaudio.PyAudio()
        
        stream = p.open(format=FORMAT,
                        channels=CHANNELS,
                        rate=RATE,
                        input=True,
                        frames_per_buffer=CHUNK)
        
        print("* recording")
        
        frames = []
        
        for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
            data = stream.read(CHUNK)
            frames.append(data)
        
        print("* done recording")
        
        stream.stop_stream()
        stream.close()
        p.terminate()
        
        
        wf = wave.open(INPUT_FILENAME, 'wb')
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(p.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))
        wf.close()
        
    
    elif sw==1:
        # impulse response
        ir, fs_ir = sf.read("0079-impulse_0m_palisade_pommelte.wav")
        ir *= 1     
        """録音したファイルの読み込み"""
        #x, fs = sf.read(INPUT_FILENAME)
        a, fs = sf.read("input1.wav")
        b, fs = sf.read("input2.wav")
        x = np.c_[
                    sp.signal.fftconvolve(a, ir) + 0.8*sp.signal.fftconvolve(b, ir),
                    sp.signal.fftconvolve(b, ir) + 0.8*sp.signal.fftconvolve(a, ir)
                  ]
        #x, fs = sf.read("../bss/Outoroduction -Theme of Cafe Espresso-.wav")
        
        
        from sklearn.decomposition import FastICA
        ica = FastICA(n_components=x.shape[1])
        x_ica = ica.fit_transform(x)
        
        """独立ベクトル分析による分離処理"""
        N_iter = 10
        fftLen = 2048*2
        n_components = x.shape[1]
        x_iva = iva.IVA(x, N=N_iter, fftLen=fftLen, n_components=n_components, fs=fs)
        
        
        """書き込み作業"""
        for i in range(n_components):
            sf.write('iva_in_%d.wav' % i, x[:, i], fs, 'PCM_16')
            sf.write('ica_out_%d.wav' % i, x_ica[:, i], fs, 'PCM_16')
            sf.write('iva_out_%d.wav' % i, x_iva[:, i], fs, 'PCM_16')
