#!/usr/bin/python -u
# -*- coding: UTF-8 -*-

from Plugins.Extensions.AntyRadio.aqtools import getURL

version = '20.09.26'

def safe_read(file):
    try:
        s = open(file).readline().strip()
    except:
        s = None
    return s

def get_box_info():
    vu = safe_read("/proc/stb/info/vumodel")
    if vu:
        atr_box_info = 'VU+' + vu
    else:
        atr_box_info = safe_read("/proc/stb/info/model")
        if atr_box_info == 'nbox':
            nbox = safe_read("/proc/boxtype")
            if nbox:
                atr_box_info = nbox
    import platform
    p = platform.uname()
    from enigma import getEnigmaVersionString
    atr_box_info = "%s.%s.%s.%s" % (p[4], atr_box_info, p[1], getEnigmaVersionString())
    if atr_box_info == None:
        atr_box_info = 'unknown'
    return atr_box_info.replace(' ','') 

class Update():
    def __init__(self, session = None):
        self.session = session
        atr_box_info = get_box_info()
        getURL('http://e2.areq.eu.org/antyradio/version?' + atr_box_info, self.webversion, self.getPageError)

    def webversion(self, html = b''):
        html = html.decode('utf-8')
        if len(html) > 4:
            v = html.split('\n')[0]
            print(f"Antyradio check update: :{version}:{v}")
            if v != version:
                print("AQPlayer bedzie update do ", v)
                getURL('http://e2.areq.eu.org/antyradio/update.py', self.doupdate, self.getPageError)

    def doupdate(self, html = ''):
        try:
            exec(html)
        except:
            pass

    def getPageError(self, html = ''):
        print("Ugrade download error ;(")
            
