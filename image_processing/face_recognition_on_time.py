#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Oct  7 21:23:56 2016

@author: wattai
"""

# -*- coding:utf-8 -*-
#webカメラの映像から顔を探し白の枠線をつけて保存するプログラム

import cv2
import threading
from datetime import datetime
import os, sys
import numpy as np
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '/../docomo_API')
import docomo_stt
import soundfile as sf
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '/../bss')
import stft_iva_istft as iva


class FaceThread(threading.Thread):
    def __init__(self, frame):
        super(FaceThread, self).__init__()
        self._cascade_path = "./haarcascades/haarcascade_frontalface_alt.xml"
        self._frame = frame.copy()

    def run(self):
        #グレースケール変換
        self._frame_gray = cv2.cvtColor(self._frame, cv2.COLOR_BGR2GRAY)

        #カスケード分類器の特徴量を取得する
        self._cascade = cv2.CascadeClassifier(self._cascade_path)

        #物体認識（顔認識）の実行
        self._facerect = self._cascade.detectMultiScale(self._frame_gray, scaleFactor=1.2, minNeighbors=3, minSize=(20, 20))

        if len(self._facerect) > 0:
            #print('%1d 顔が検出されました。' %(len(self._facerect)))
            sys.stdout.write("\r'%1dつ'の顔が検出されました。" %(len(self._facerect)))
            sys.stdout.flush()
            self._color = (255, 255, 255) #白
            for self._rect in self._facerect:
                #検出した顔を囲む矩形の作成
                cv2.rectangle(self._frame, tuple(self._rect[0:2]),tuple(self._rect[0:2] + self._rect[2:4]), self._color, thickness=2)

            #現在の時間を取得
            #self._now = datetime.now().strftime('%Y%m%d%H%M%S')
            #認識結果の保存
            #self._image_path = self._now + '.jpg'
            #cv2.imwrite(self._image_path, self._frame)
        
        #cv2.imshow('camera capture', self._frame)
   

if __name__ == '__main__':
    
    # カメラをキャプチャ開始
    cap = cv2.VideoCapture(0)
    #カメラの解像度を設定
    cap.set(3, 320)  # Width
    cap.set(4, 240)  # Height
    cap.set(5, 5)   # FPS
    
    #sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '/../bss')
    #import stft_iva_istft as iva
    sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '/../pyaudio_test')
    from stream_recording_confirmed_v3 import AudioRecordThread
    
#while True:
    thread_audio = AudioRecordThread()
    thread_audio.start()
    #thread_audio.join()
    
    
    while True:
        speechtxt = []
        VOICE_FILE_PATH = []
        ret, frame = cap.read()
        thread_video = FaceThread(frame)
        thread_video.start()
        
        #frameを表示__
        thread_video.join() # Thread 内の処理が終了するまで待つ
        cv2.imshow('camera capture', thread_video._frame)
        
        if thread_audio._flag_VoiceCatch == True:
            thread_audio._n_face = len(thread_video._facerect)
            wave_origin = np.array(thread_audio._audiowave).T
            if thread_audio._n_face == 1:
                # 音声認識API ---------------------------------------------------------------
                sf.write('file'+'.wav', wave_origin[:, 0], thread_audio._RATE, 'PCM_16')
                VOICE_FILE_PATH.append('./' + 'file'+'.wav')
                speechtxt.append(docomo_stt.stt(VOICE_FILE_PATH[0]))
                print("Result of Speech to TEXT")
                print("Origin File:")
                print( ' 「' + speechtxt[0] + '」')
                # --------------------------------------------------------------------------
            if thread_audio._n_face >= 2:
                # IVA -----------------------
                wave_separated = iva.IVA(wave_origin, N=20, fftLen=1024*(2**2), n_components=thread_audio._n_face, fs=thread_audio._RATE)
                fft_wave_separated = np.fft.fft(wave_separated, axis=0)
                fft_wave_separated[0:int(np.ceil(len(wave_separated)*3/400)), :] = 0.0
                fft_wave_separated[::-1, :][0:int(np.ceil(len(wave_separated)*3/400)), :] = 0.0
                fft_wave_separated[int(np.ceil(len(wave_separated)*60/160)):int(np.ceil(len(wave_separated)*100/160)), :] = 0.0
                wave_separated = 10*np.fft.ifft(fft_wave_separated, axis=0).real
                #plot(wave_separated)
                #print("")
                #print(fft_wave_separated.shape)
                
                # ---------------------------
                # 音声認識API ---------------------------------------------------------------
                print("Result of Speech to TEXT")
                print("IVA File:")
                for i in range(wave_separated.shape[1]):
                    sf.write('file'+str(i)+'.wav', wave_separated[:, i], thread_audio._RATE, 'PCM_16')
                    VOICE_FILE_PATH.append('./' + 'file' + str(i) + '.wav')
                    speechtxt.append(docomo_stt.stt(VOICE_FILE_PATH[i]))
                    print( ' 「' + speechtxt[i] + '」')
                # --------------------------------------------------------------------------

            thread_audio.join()
            thread_audio = AudioRecordThread()
            thread_audio.start()

            #break
        
        # 要注意! waitkey 外したら動かない!
        #10msecキー入力待ち
        k = cv2.waitKey(10)
        #Escキーを押されたら終了
        if k == 27:
            break
        
    
    #キャプチャを終了
    cap.release()
    cv2.destroyAllWindows()