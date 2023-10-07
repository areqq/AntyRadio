# -*- coding: utf-8 -*-
from twisted.internet.reactor import callInThread
import requests
def getURL2(url, callback, error):
    try:
        r = requests.get(url, timeout = 5)
        if r.status_code == 200:
            callback(r.content)
            return
    except:
        print(f"aqtools: getURL2 error {url} except!")
    if error:
        error()

def getURL(url, callback, error = None):
    callInThread(getURL2,url, callback, error)

