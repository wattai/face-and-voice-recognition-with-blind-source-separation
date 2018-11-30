#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Oct  8 13:53:27 2016

@author: wattai
"""

import pyaudio
import time
import wave
import numpy as np
import sys
import audioop
import math
import threading
import os
import soundfile as sf
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '/../bss')
import stft_iva_istft as iva
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '/../docomo_API')
import docomo_stt

class AudioRecordThread(threading.Thread):
    def __init__(self):
        super(AudioRecordThread, self).__init__()

        # 各種設定　#########################
        self._flag_recogRepeat = False  # 音声認識を繰り返し行う場合　Trueにする
        self._EXIT_WORD = u"(音声認識を終了します|ちちんぷいぷい|さようなら)"  # 音声認識を終了させる合言葉
        self._LANG_CODE = 'ja-JP'  # a BCP-47 language tag
        
        self._RATE = 16000  # サンプリングレート
        self._CHANNELS = 2  # 録音チャンネル数
        
        self._RECORD_SEC = 5  # 録音時間(sec)
        self._DEV_INDEX = 0  # デバイスを指定
        
        self._FRAME_SEC = 0.250  # 1フレームの時間（秒）　（0.1sec = 100ms）
        self._CHUNK = int(self._RATE * self._FRAME_SEC)  # 1フレーム内のサンプルデータ数
        
        self._SLEEP_SEC = self._FRAME_SEC / 4  # メインループ内でのスリープタイム（秒）
        self._BUF_SIZE = self._CHUNK * 2  # 音声のバッファ・サイズ（byte）
        
        self._DECIBEL_THRESHOLD_START = -30  # 録音開始のための閾値（dB)
        self._DECIBEL_THRESHOLD_END = -35  # 録音終了のための閾値（dB)
        self._START_FRAME_LEN = 2  # 録音開始のために，何フレーム連続で閾値を超えたらいいか
        self._END_FRAME_LEN = 256*4  # 録音終了のために，何フレーム連続で閾値を超えたらいいか
        self._START_BUF_LEN = 4  # 録音データに加える，閾値を超える前のフレーム数　（START_FRAME_LENの設定によって，促音の前の音が録音されない問題への対処用）
        
        # Google のサンプルプログラムより (Keep the request alive for this many seconds)
        self._DEADLINE_SECS = 8 * 60 * 60
        self._SPEECH_SCOPE = 'https://www.googleapis.com/auth/cloud-platform'
        
        # バッファ用変数 #####################
        self._frames = []
        self._frames_startbuf = []
        
        self._flag_RecordStart = False  # 音量が規定フレーム分，閾値を超え続けたらTRUE
        self._flag_RecogEnd = False  # 音声認識が終わったらTrueにする
        
        self._recog_result = ""  # 音声認識結果
        
        # 基本設定
        self._FRAMES_PER_BUFFER = self._CHUNK
        
        # 保存先ファイルを用意
        self._origin_file_name = 'pyaudiotest'
        """
        self._wf = wave.open(self._origin_file_name,'w')
        self._wf.setnchannels(self._CHANNELS) # CHANNNELS
        self._wf.setsampwidth(2) #16bits
        self._wf.setframerate(self._RATE)
        """
        
        
        self._frames = []

        # 録音時間
        self._RECORD_SECONDS = 5
        
        self._cont = 0
        
        # 音声ファイル書き込み終了フラグ
        self._flag_VoiceCatch = False
        
        # 画像処理部から来た顔の数を格納用
        self._n_face = 0
        
        # stt結果の格納用
        self._speechtxt_oneman = ""
        self._speechtxt_origin = []
        self._speechtxt_iva = []

        self._flag_FinishVoiceRecog = False

        self._audiowave = [[],[]]
        
    # コールバック関数
    def callback(self, in_data, frame_count, time_info, status):
        # wavに保存する
        #wf.writeframes(in_data)
        self._frames.append(in_data)
        return (None, pyaudio.paContinue)
 

    def run(self):
        
        # pyaudioオブジェクトを作成
        p = pyaudio.PyAudio()
        
        # ストリームを開始
        stream = p.open(format = pyaudio.paFloat32,
                        channels = self._CHANNELS,
                       rate = self._RATE,
                       input_device_index = self._DEV_INDEX,
                       input = True,
                       output = False,
                       frames_per_buffer = self._FRAMES_PER_BUFFER,
                       stream_callback = self.callback)
        #print("")
        #print(p.get_format_from_width(self._wf.getsampwidth()))
        
        self._cont = 0
        while True:
            # フラグ初期化 ##################################
            self._flag_RecordStart = False  # 音量が規定フレーム分，閾値を超え続けたらTRUE
            self._flag_RecogEnd = False  # 音声認識が終わったらTrueにする
            self._frames_startbuf = []
            self._frames = []
            """
            # 保存先ファイルを用意
            self._wf = wave.open(self._origin_file_name,'w')
            self._wf.setnchannels(self._CHANNELS) # CHANNNELS
            self._wf.setsampwidth(2) #16bits
            self._wf.setframerate(self._RATE)
            """
            
            # 録音開始までの処理 ##############################
            while not self._flag_RecordStart:
                time.sleep(self._SLEEP_SEC)
            
                # 促音用バッファが長過ぎたら捨てる（STARTフレームより更に前のデータを保存しているバッファ）
                if len(self._frames_startbuf) > self._START_BUF_LEN:
                    #try:
                    #    rms_buff = np.sqrt(np.average(np.fromstring(self._frames_startbuf[0][0], np.float32)**2))
                    #except:
                    #    rms_buff = np.sqrt(np.average(np.fromstring(self._frames_startbuf[-1], np.float32)**2))
                        
                    #decibel_buff = 20 * np.log10(rms_buff) if rms_buff > 0 else 0
                    #self._DECIBEL_THRESHOLD_START = np.average(decibel_buff) + 1.0*np.std(decibel_buff, ddof=0)
                    #self._DECIBEL_THRESHOLD_END = np.average(decibel_buff) - 0.5*np.std(decibel_buff, ddof=0)
                    del self._frames_startbuf[0:len(self._frames_startbuf) - self._START_BUF_LEN]
    
                # バッファにデータが溜まったら，録音開始するべきか判定 ---------
                if len(self._frames) > self._START_FRAME_LEN:
                    # 1フレーム内の音量計算--------------------------------
                    for i in range(self._START_FRAME_LEN):
                        
                        data = self._frames[i]
                        #rms = audioop.rms(data, 2)
                        #if self._n_face == 1:
                        #    data = np.fromstring(data, np.float32)
                        #elif self._n_face >= 2:
                        data = np.fromstring(data, np.float32)[::2]
                        rms = np.sqrt(np.average(data**2))
                        
                        decibel = 20 * np.log10(rms) if rms > 0 else 0
                        sys.stdout.write("\rrms %f decibel %f, State: WAITING" %(rms,decibel))
                        sys.stdout.flush()
    
                        #self._frames_startbuf.append(self._frames[0:i + 1])
                        # 音量が閾値より小さかったら，データを捨てループを抜ける ----
                        if decibel < self._DECIBEL_THRESHOLD_START:
                            #self._frames_startbuf.append(self._frames[i])
                            #del self._frames[i]
                            #  self._frames_startbuf.append(self._frames[0:i + 1])
                            self._frames_startbuf = self._frames_startbuf + (self._frames[0:i + 1])
                            print("ADD!!!")
                            print("frame_length: " + str(len(self._frames_startbuf)))
                            del self._frames[0:i + 1]
                            break
      
                        # 全フレームの音量が閾値を超えていたら，録音開始！！ ----
                        # 更に，framesの先頭に，先頭バッファをプラス
                        # これをしないと「かっぱ」の「かっ」など，促音の前の音が消えてしまう
                        elif i == self._START_FRAME_LEN - 1:
                            self._flag_RecordStart = True
                            try:
                                #self._frames = (self._frames_startbuf[0]).extend(self._frames)
                                self._frames = (self._frames_startbuf[0]) + self._frames
                            except:
                                #self._frames = (self._frames_startbuf).extend(self._frames)
                                self._frames = (self._frames_startbuf) + self._frames
                            
            # ##############################################
    
            # 録音終了までの処理 ##############################
            self._flag_RecordEnd = False
            # バッファにデータが溜まったら，録音終了するべきか判定 ---------
            while not self._flag_RecordEnd:
                time.sleep(self._SLEEP_SEC)
                
                # 1フレーム内の音量計算--------------------------------
                for i in range(self._END_FRAME_LEN):
                    
                    data = self._frames[-1]
                    #rms = audioop.rms(data, 2)
                    #if self._n_face <= 1:
                    #    data = np.fromstring(data, np.float32)
                    #elif self._n_face >= 2:
                    data = np.fromstring(data, np.float32)[::2]
                    
                    rms = np.sqrt(np.average(data**2))
                    
                    decibel = 20 * np.log10(rms) if rms > 0 else 0
                    sys.stdout.write("\rrms %f decibel %f" %(rms,decibel))
                    sys.stdout.flush()
    
                    # 音量が閾値より大きかったら，ループを抜ける ----
                    if decibel > self._DECIBEL_THRESHOLD_END:
                        sys.stdout.write("\rrms %f decibel %f, State: RECORDING" %(rms,decibel))
                        sys.stdout.flush()
                        break
      
                    # 全フレームの音量が閾値を下回っていたら，録音終了！！ ----
                    elif i == self._END_FRAME_LEN - 1:
                        self._flag_RecordEnd = True
                        print("")
                        print(i)
            # ##############################################
                        
            # 録音終了まで待つ
            #time.sleep(RECORD_SECONDS)
            
            # 文字データから数値データに変換
            for i in range(len(self._frames)):
                if self._CHANNELS == 1:
                    #self._wf.writeframes(self._frames[i])
                    self._audiowave[:][0].extend(np.fromstring(self._frames[i], np.float32))
                elif self._CHANNELS == 2:
                    self._audiowave[:][0].extend(np.fromstring(self._frames[i], np.float32)[::2])
                    self._audiowave[:][1].extend(np.fromstring(self._frames[i], np.float32)[1::2])
                    
            #self._wf.close() # wavファイルを閉じる
            #print(np.fromstring(self._frames[i], np.float32).shape)

            # ファイル書き込み終了フラグ
            self._flag_VoiceCatch = True

            """
            if self._n_face == 1:
                # 音声認識API ---------------------------------------------------------------
                VOICE_FILE_PATH = './' + self._origin_file_name
                self._speechtxt_oneman = (docomo_stt.stt(VOICE_FILE_PATH))
            
                print("Result of Speech to TEXT")
                print("Origin File:")
                print( ' 「' + self._speechtxt_oneman + '」')
                # --------------------------------------------------------------------------
        
            elif self._n_face > 1:
                # ファイルを再び読み込みIVA開始
                origin, samplerate = sf.read(self._origin_name)
                separated = iva.IVA(origin, N=20, fftLen=1024*(2**1), n_components=self._n_face, fs=samplerate)
                for i in range(separated.shape[1]):
                    sf.write('iva_file%d.wav' % i, separated[:, i], samplerate, 'PCM_16')
            
                # 音声認識API ---------------------------------------------------------------
                #for i in range(origin.shape[1]):
                #    path = ('./origin_file%d.wav' % i)
                #    speechtxt_origin.append(docomo_stt.stt(path))
                for i in range(separated.shape[1]):
                    VOICE_FILE_PATH = ('./iva_file%d.wav' % i)
                    self._speechtxt_iva.append(docomo_stt.stt(VOICE_FILE_PATH))
            
                print("Result of Speech to TEXT")
                #print("Origin File:")
                #for i in range(origin.shape[1]):
                #    print(str(i) + ' 「' + self._speechtxt_origin[:][i] + '」')
                print("IVAed File:")
                for i in range(separated.shape[1]):
                    print(str(i) + ' 「' + self._speechtxt_iva[:][i] + '」')
                # --------------------------------------------------------------------------
            """
            #self._flag_RecogEnd = True
                
            break
            #cont += 1 # 仮に2回繰り返せば終わるようにしてる
            #if self._cont>=1: break
         
        # ストリームを止める
        stream.stop_stream()
        stream.close()
        
        # wavファイルを閉じる
        #wf.close()
        
        # pyaudioオブジェクトを終了
        p.terminate()
        
if __name__ == '__main__':
    
    #while True:
    
    if(threading.activeCount() >= 0):
        th = AudioRecordThread()
        th.start()
        
            #frameを表示
            #th.join() # いったん Thread を止める
            #cv2.imshow('camera capture', th._frame)