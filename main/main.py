# -*- coding: utf-8 -*-
"""
Created on Tue Oct 11 10:26:44 2016

@author: wattai
"""
import cv2
import threading
from datetime import datetime
import os, sys
import numpy as np
import scipy as sp
from scipy import signal
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '/../docomo_API')
import docomo_stt
import soundfile as sf
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '/../bss')
import stft_iva_istft as iva
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '/../image_processing')
from face_recognition_on_time import FaceThread
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '/../pyaudio_test')
from stream_recording_confirmed_v3 import AudioRecordThread
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '/../pygame_music_play')
from pygame_music_play import MusicPlayThread
# sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '/../rospeex')
# from rospeex import get_tts

#スケールの書き込み関数
def make_scale(im,length=40,from_edge = 50,thick = 2,hight = 6, font_size = 10,pix_size = 10):

    w = im.shape[0]
    h = im.shape[1]
    #横線
    #cv2.line(im,(w-length-from_edge,h-from_edge),(w-from_edge,h-from_edge),(255,255,0),thick)
    #縦線左
    #cv2.line(im,(w-length-from_edge,h-from_edge-hight/2),(w-length-from_edge,h-from_edge+hight/2),(255,255,0),thick)
    #縦線右
    #cv2.line(im,(w-from_edge,h-from_edge-hight/2),(w-from_edge,h-from_edge+hight/2),(255,255,0),thick)
	
    #1ピクセルのサイズから長さを計算
    size = pix_size*length
    text = str(size) + 'micro m'
    #フォントの指定
    font = cv2.FONT_HERSHEY_PLAIN
    #文字の書き込み
    cv2.putText(im,text,(int(w-length-from_edge-5),int(h-from_edge-hight)),font, font_size,(255,255,0), 3, cv2.LINE_AA)

    return im
    
from PIL import Image, ImageDraw, ImageFont
def make_font(font_size):
    return ImageFont.truetype('./fonts/07Yasashisa/07Yasashisa.ttf', font_size)

class VoiceRecogThread(threading.Thread):
    def __init__(self, n_face, wave_origin, samplerate, speechtxt):
        super(VoiceRecogThread, self).__init__()
        self._n_face = n_face
        self._wave_origin = wave_origin.copy()
        self._samplerate = samplerate
        self._speechtxt = speechtxt
        self._VOICE_FILE_PATH = ["./file.wav", "./file0.wav", "./file1.wav"]
    
    def run(self):
        
        #thread_audio._n_face = len(thread_video._facerect)
        #wave_origin = np.array(thread_audio._audiowave).T

        if self._n_face == 1:
            # 音声認識API ---------------------------------------------------------------
            sf.write('file'+'.wav', self._wave_origin[:, 0], self._samplerate, 'PCM_16')
            #VOICE_FILE_PATH.append('./' + 'file'+'.wav')
            #self._speechtxt = ["", "", "", "", ""]
            self._speechtxt[0] = (docomo_stt.stt(self._VOICE_FILE_PATH[0]))
            print("Result of Speech to TEXT")
            print("Origin File:")
            print( ' 「' + self._speechtxt[0] + '」')
            # --------------------------------------------------------------------------
        if self._n_face >= 2:
            
            self._n_face = 2 # 現状マイクが2個までしかないので
            
            # IVA -----------------------
            wave_separated = iva.IVA(self._wave_origin, N=20, fftLen=1024*(2**2), n_components=self._n_face, fs=self._samplerate)
            #fft_wave_separated = np.fft.fft(wave_separated, axis=0)
            #fft_wave_separated[0:int(np.ceil(len(wave_separated)*3/400)), :] = 0.0
            #fft_wave_separated[::-1, :][0:int(np.ceil(len(wave_separated)*3/400)), :] = 0.0
            #fft_wave_separated[int(np.ceil(len(wave_separated)*40/160)):int(np.ceil(len(wave_separated)*120/160)), :] = 0.0
            #wave_separated = 5*np.fft.ifft(fft_wave_separated, axis=0).real
            """
            win = np.hanning(256)
            #  wave_separated[0:int(len(win)/2), :] = (wave_separated[0:int(len(win)/2), :].T * win[0:int(len(win)/2)]).T
            #  wave_separated[len(wave_separated)-int(len(win)/2):len(wave_separated), :] = (wave_separated[len(wave_separated)-int(len(win)/2):len(wave_separated), :].T * win[int(len(win)/2):len(win)]).T
            N_window = 4 # 16
            #  window = np.ones(N_window)/N_window
            for i in range(self._n_face):
            #      wave_separated[:, i] = sp.signal.fftconvolve(wave_separated[:, i], window, mode='same')
                sp.signal.wiener(im=wave_separated[:, i], mysize=N_window, noise=None)
            wave_separated[0:int(len(win)/2), :] = (wave_separated[0:int(len(win)/2), :].T * win[0:int(len(win)/2)]).T
            wave_separated[len(wave_separated)-int(len(win)/2):len(wave_separated), :] = (wave_separated[len(wave_separated)-int(len(win)/2):len(wave_separated), :].T * win[int(len(win)/2):len(win)]).T
            
            for i in range(self._n_face):
            #    sp.signal.medfilt(wave_separated[:, i], kernel_size=4)
                signal.medfilt(wave_separated[:, i], kernel_size=5)
            """
            #plot(wave_separated)
            #print("")
            #print(fft_wave_separated.shape)
            
            # ---------------------------
            # 音声認識API ---------------------------------------------------------------
            print("Result of Speech to TEXT")
            print("IVA File:")
            #self._speechtxt = ["", "", "", "", ""]
            for i in range(wave_separated.shape[1]):
                sf.write('origfile'+str(i)+'.wav', self._wave_origin[:, i], self._samplerate, 'PCM_16')
                sf.write('file'+str(i)+'.wav', wave_separated[:, i], self._samplerate, 'PCM_16')
                #self._VOICE_FILE_PATH.append('./' + 'file' + str(i) + '.wav')
                self._speechtxt[i] = (docomo_stt.stt(self._VOICE_FILE_PATH[i+1]))
                print( ' 「' + self._speechtxt[i] + '」')
            # --------------------------------------------------------------------------
        """
        # 音声合成API --------------------- rospeex on cloud がサービス終了した．
        for i in range(self._n_face):
            try:
                speech, wave = get_tts(speechtxt[i])
                sf.write("non-monologue.wav", wave, self._samplerate, 'PCM_16')
                thread_play_voice = MusicPlayThread("./non-monologue.wav")
                thread_play_voice.start()
                #th.join()
            except:
                print("Speech Error.")
                None
        # ---------------------------------
        """
if __name__ == '__main__':
    
    # カメラをキャプチャ開始
    cap = cv2.VideoCapture(0)
    #カメラの解像度を設定
    cap.set(3, 640)  # Width
    cap.set(4, 480)  # Height
    cap.set(5, 30)   # FPS
    
    
    thread_audio = AudioRecordThread()
    thread_audio.start()
    #thread_audio.join()
    
    font = cv2.FONT_HERSHEY_COMPLEX
    font_size = 20
    speechtxt = ["Hello!", "Hello!", "", "", ""]
    font = make_font(font_size)
    
    thread_audio._DECIBEL_THRESHOLD_START = -35  # 録音開始のための閾値（dB)
    thread_audio._DECIBEL_THRESHOLD_END = -38  # 録音終了のための閾値（dB)
    
    while True:
        VOICE_FILE_PATH = []
        ret, frame = cap.read()
        thread_video = FaceThread(frame)
        thread_video.start()
        
        
        #frameを表示__
        thread_video.join() # Thread 内の処理が終了するまで待つ
        if len(thread_video._facerect) > 0:
            pilImg = Image.fromarray(np.uint8(thread_video._frame))
            draw = ImageDraw.Draw(pilImg)
            for i in range(len(thread_video._facerect)):
                draw.text([thread_video._facerect[i][0], thread_video._facerect[i][1]-int(font_size)], speechtxt[i], fill=(255, int(255*i), 255), font=font)
            thread_video._frame = np.asarray(pilImg)
            thread_video._frame.flags.writeable = True
        
        cv2.imshow('camera capture', thread_video._frame)
        
        if thread_audio._flag_VoiceCatch == True:
            
            n_face = len(thread_video._facerect)
            wave_origin = np.array(thread_audio._audiowave).T
            thread_voice_recog = VoiceRecogThread(n_face, wave_origin, thread_audio._RATE, speechtxt)
            thread_voice_recog.start()

            
            thread_audio.join()
            thread_audio = AudioRecordThread()
            thread_audio.start()
            speechtxt = thread_voice_recog._speechtxt
            
        
        # 要注意! waitkey 外したら動かない!
        #10msecキー入力待ち
        k = cv2.waitKey(10)
        #Escキーを押されたら終了
        if k == 27:
            break
        
    #キャプチャを終了
    cap.release()
    cv2.destroyAllWindows()