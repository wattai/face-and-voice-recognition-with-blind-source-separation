# -*- coding: utf-8 -*-
"""
Created on Tue Oct  4 22:13:58 2016

@author: wattai
"""

import requests
import json

# enter your api-key
APIKEY = ""

def stt(path):
    
    # 音声認識API
    url = "https://api.apigw.smt.docomo.ne.jp/amiVoice/v1/recognize?APIKEY={}".format(APIKEY)
    files = {"a": open(path, 'rb'), "v":"on"}
    #print(files)
    r = requests.post(url, files=files)
    #print( r.json()['text'] )
    
    return r.json()['text']

if __name__ == '__main__':
    
    # 音声認識API
    path = './dev2_src_4.wav'
    speech_txt = stt(path)
    
    
    # 音声認識API
    path = './dev2_src_4.wav'
    url = "https://api.apigw.smt.docomo.ne.jp/amiVoice/v1/recognize?APIKEY={}".format(APIKEY)
    files = {"a": open(path, 'rb'), "v":"on"}
    print(files)
    r = requests.post(url, files=files)
    print( r.json()['text'] )
    

    # 雑談API
    print("雑談API")
    url = "https://api.apigw.smt.docomo.ne.jp/dialogue/v1/dialogue?APIKEY={}".format(APIKEY)
    payload = {
        "utt": "こんにちは",
        "context": "",
        "nickname": "光",
        "nickname_y": "ヒカリ",
        "sex": "女",
        "bloodtype": "B",
        "birthdateY": "1997",
        "birthdateM": "5",
        "birthdateD": "30",
        "age": "16",
        "constellations": "双子座",
        "place": "東京",
        "mode": "dialog",
    }
    r = requests.post(url, data=json.dumps(payload))
    print( r.json()['utt'] )
    