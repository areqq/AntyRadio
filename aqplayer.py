#!/usr/bin/python -u
# -*- coding: UTF-8 -*-

from Screens.Screen import Screen
from Components.Label import Label
from Components.ActionMap import ActionMap
from Components.ServiceEventTracker import ServiceEventTracker
from Components.config import config
from Screens.ChoiceBox import ChoiceBox
from Screens.MessageBox import MessageBox
from twisted.internet import reactor
from twisted.web.client import getPage
import os, os.path, re, struct, json
from time import time
from enigma import eActionMap, eServiceReference, iServiceInformation, iPlayableService, eTimer, eDVBVolumecontrol
from urllib import quote
import version
reload(version)

class AQPlayer(Screen):
   s = ''
   szer = 300
   for page in xrange(4):
      for i in xrange(1,11):
          s+= '<widget name="p%i" position="%i, %i" size="%i,42" font="Regular;20"/>\n' % (page * 10 + i, 10 + (page * szer), (50 *i), szer) 
      s+= '<widget name="page%i" position="%i, 560" size="%i,20" font="Regular;20"/>\n' % (page, 40 +(szer * page), szer) 

   skin = """
   <screen name='AQPlayer' position="50, 50" size="1190,610" title="AQPlayer" flags="wfNoBorder">
    <widget name="vol" position="5, 5" size="75,28" font="Regular;22" halign="left" backgroundColor="blue"/>
    <widget name="info" position="80, 5" size="1100,28" font="Regular;22" halign="center" backgroundColor="blue"/>
   %s
   <eLabel text="Konfiguracja" position="0,585" size="150,30" zPosition="2" font="Regular;22" halign="center" backgroundColor="red" />
   <eLabel text="MPD" position="170,585" size="150,30" zPosition="2" font="Regular;22" halign="center" backgroundColor="blue" />
   <eLabel text="EXIT" position="450,585" size="50,30" zPosition="2" font="Regular;22" halign="center"  />
   <eLabel text="AntyRadio by Areq (2015)" position="930,585" size="270,30" zPosition="2" font="Regular;22" halign="left" backgroundColor="green" />

   </screen>"""  % s

   def __init__(self, session):
        Screen.__init__(self, session)
        u = version.Update(session)
        self.audiotrack = None
        self.played = 0
        self.mp3 = None
        self.page = 0
        self.p_title0 = ''
        self.p_title = ''
        self.prevseek = 0
        self.rds = 0
        self.rdsurl = ''
        self.inactiveCount = 0
        self.pl = [['mpd','mpd']]
        for l in open('/usr/lib/enigma2/python/Plugins/Extensions/AntyRadio/playlist.txt'):
            try:
                if len(l) > 4 and l[0] != '#':
                    z = l.strip().strip('\r').split('|')
                    if z[0] != '//': 
                        for i in xrange(len(z), 4):
                            z.append('')
                        self.pl.append(z)
                    else:
                        try:
                            dirs = sorted(os.listdir(z[1]))
                            for i in range( min( len(dirs), 41 - len(self.pl) )):
                                self.pl.append( [dirs[i].replace('.',' '), z[1] + dirs[i], '', '' ] )
                        except:
                            pass
            except:
                pass
        self["info"] = Label(" ")
        self["vol"] = Label(" ")

        for i in xrange(4):
            self["page%i" % i] = Label("")

        for i in xrange(1, min( len(self.pl), 41)):
            self["p%i" % i] = Label("%i. %s" % (i, self.pl[i][0]) )
        for i in xrange(min( len(self.pl), 41), 41):
            self["p%i" % i] = Label("")
        self.updatePage(0)
        self.session.nav.event.append(self.__event)
        self.onClose.append(self.__onClose)
        self.volctrl = eDVBVolumecontrol.getInstance()
        v = int(config.plugins.antyradio.startvol.value)
        if v > 0:
            print "AQplayer setvolume", v
            self.volctrl.setVolume(v, v)
        self.__event_tracker = ServiceEventTracker(screen=self, eventmap=
        {
            iPlayableService.evUpdatedInfo: self.__evUpdatedInfo,
            iPlayableService.evEOF: self.__evEOF,
            iPlayableService.evSOF: self.__evSOF,
            iPlayableService.evUser+10: self.__evAudioDecodeError,
            iPlayableService.evUser+12: self.__evPluginError
        })
        self.oldService = self.session.nav.getCurrentlyPlayingServiceReference()
        self.session.nav.stopService()
        if config.plugins.antyradio.runmpd.value:
            self.mpd('play')
        else:
            ps = int(config.plugins.antyradio.startpos.value)
            if ps > 0:
                self.page = ps // 10
                self.play(ps)
            else:
                self.play(1)
        self["myActionMap"] = ActionMap(["AQPlayerActions"],
        {
#         "ok": self.cancel,
         "cancel": self.cancel,
         "power": self.cancel,
         "red": self.red,
         "blue": self.blue,
         "up": self.up,
         "down": self.down,
         "zapdown": self.zapdown,
         "zapup": self.zapup,
         "right": self.right,
         "left": self.left,
         "halt": self.halt,
         "aqvolumeUp": self.volumeUp,
         "aqvolumeDown": self.volumeDown,
         "aqvolumeMute": self.volumeMute,
         "0": self.number0,
         "1": self.number1,
         "2": self.number2,
         "3": self.number3,
         "4": self.number4,
         "5": self.number5,
         "6": self.number6,
         "7": self.number7,
         "8": self.number8,
         "9": self.number9,
         "keytv": self.nic_nie_robie   # key wołany z timera by autoshutdown oszukać
        }, -1)
        self.amap = eActionMap.getInstance()
        self.timer = eTimer()
        self.timer.callback.append(self.timerEvent)
        self.timer.start(500, False)

   def nic_nie_robie(self, cos = None):
      pass

   def mpd(self, co):
        os.system("killall nc; echo %s | nc 127.0.0.1 6600 &" % co)
        os.system("sleep 3; killall nc")

   def volumeUp(self):
      self._keyPressed()
      self.volctrl.volumeUp()
      self["vol"].setText("V:%i" % self.volctrl.getVolume())

   def volumeDown(self):
      self._keyPressed()
      self.volctrl.volumeDown()
      self["vol"].setText("V:%i" % self.volctrl.getVolume())

   def volumeMute(self):
      self._keyPressed()
      self.volctrl.volumeToggleMute()

   def updatePage(self, nr):
      q = self.page
      self["page%i" % self.page].setText('')
      if 0 <= self.page + nr < 4:
        self.page += nr
      self["page%i" % self.page].setText('^^^')
      if q != self.page:
         self.play( (10 * self.page) + 1)

   def zapdown(self):
      self._keyPressed()
      self.updatePage(1)

   def zapup(self):
      self._keyPressed()
      self.updatePage(-1)
 
   def left(self):
      self._keyPressed()
      if self.mp3:
         self.play_mp3(-1)
      else:
         self.updatePage(-1)
   def right(self):
      self._keyPressed()
      if self.mp3:
         self.play_mp3(1)
      else:
         self.updatePage(1)

   def timerEvent(self):
     if self.rds:
        if self.rds > 30:
#          print "AQPlayer timerEvent RDS", self.rdsurl 
          getPage(self.rdsurl).addCallback(self.parseRDS).addErrback(self.getPageError)
          self.rds = 1
        else:
          self.rds = self.rds + 1

     if self.inactiveCount > 2*10*60:
        self.hdmiStandby()
        self.inactiveCount = 0
     else:
        self.inactiveCount += 1
     service = self.session.nav.getCurrentService()
     if service:
        seek = service.seek()
        if seek:
            s = seek.getPlayPosition()[1]
            l = seek.getLength()[1]
#            print "QQQQQQQQQQQQ: seek", s, l, l - s, s - self.prevseek, (s/90000)%60
            self.prevseek = s
     if (self.inactiveCount % (2*60*60)) == 0:
         self.amap.keyPressed('dreambox advanced remote control (native)', 377, 0)
         self.amap.keyPressed('dreambox advanced remote control (native)', 377, 1)

   def getPageError(self, error = None):
    print "AQplayer getPageError:", error

   def parseRDS(self, html):
      a, t = ('', '')
      try:
        r = html.replace('\n','')
        if r.startswith('rdsData('): # antyradio
                d = json.loads(r[8:-1])
                if d.has_key('now'):
                        t = d['now'].get('title', '')
                        a = d['now'].get('artist', '')
        elif r.startswith('{"emisja"'): # zet
                d = json.loads(r)
                if d.has_key('emisja'):
                        t = d['emisja'][0].get('tytul', '')
                        a = d['emisja'][0].get('wykonawca', '')
        elif r.startswith('{"artist"'): #zlote przeboje
                d = json.loads(r)
                t = d.get('title', '')
                a = d.get('artist', '')
                if t == '':
                  t = d.get('broadcast', '')
        elif r.startswith('[{"order"'): #rmf
                for d in json.loads(r):
                        if int(d.get('order', '')) == 0:
                          if int(d.get('timestamp', 0)) + int(d.get('lenght', 0)) > time():
                                t = d.get('title', '')
                                a = d.get('author', '')
      except:
        pass
      s = '%s-%s' % (a, t)
      print "AQPlayer parseRDS:", s
      if self.p_title != s:
        self.p_title = s
#        print "xxxxxxxxxxxxxxxx", s
        self.info_update()

   def selectSatTrack(self,id):
        service = self.session.nav.getCurrentService()
        audio = service and service.audioTracks()
        if audio is not None and service is not None:
                if audio.getNumberOfTracks() > id and id >= 0:
                        audio.selectTrack(id)
                        print "AQplayer selectSatTrack set", id

   def __event(self, ev):
      if ev not in [17, 18]:
#        print "qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq event:", ev
        pass
   def __onClose(self):
      self.timer.stop()
      self.session.nav.event.remove(self.__event)
      print "AQPlayer: __onClose "
      self.session.nav.playService(self.oldService)

   def __evUpdatedInfo(self):
      currPlay = self.session.nav.getCurrentService()
      sTagTrackNumber = currPlay.info().getInfo(iServiceInformation.sTagTrackNumber)
      sTagTrackCount = currPlay.info().getInfo(iServiceInformation.sTagTrackCount)
      sTagTitle = currPlay.info().getInfoString(iServiceInformation.sTagTitle)
      sTagArtist = currPlay.info().getInfoString(iServiceInformation.sTagArtist)
      sTagAlbum = currPlay.info().getInfoString(iServiceInformation.sTagAlbum)
      sTagGenre = currPlay.info().getInfoString(iServiceInformation.sTagGenre)

      s = "%s %s %s" % (sTagArtist, sTagAlbum, sTagTitle)
      if len(s) > 4:
        self.p_title = s 
        self.info_update()
      print "AQPlayer [__evUpdatedInfo] title %d of %d (%s)" % (sTagTrackNumber, sTagTrackCount, sTagTitle)
      if self.audiotrack:
        print "AQplayer __evUpdatedInfo audiotrack"
        self.selectSatTrack(self.audiotrack)

   def __evAudioDecodeError(self):
      currPlay = self.session.nav.getCurrentService()
      sTagAudioCodec = currPlay.info().getInfoString(iServiceInformation.sTagAudioCodec)
      print "QQQQQQQQQQQQQQ [__evAudioDecodeError] audio-codec %s can't be decoded by hardware" % (sTagAudioCodec)

   def __evPluginError(self):
      currPlay = self.session.nav.getCurrentService()
      message = currPlay.info().getInfoString(iServiceInformation.sUser+12)
      print "QQQQQQQQQQQQQQ [__evPluginError]" , message

   def __evSOF(self):
     print "QQQQQQQQQQQQQQQQaaa __evSOF"

   def __evEOF(self):
      print "QQQQQQQQQQQQQQQQaaa__evEOF"
      if self.mp3:
         self.play_mp3(1)
      else:
         self.play(1)

   def _keyPressed(self, key = None):
      self.inactiveCount = 0

   def number0(self):
         self.number(10)
   def number1(self):
         self.number(1)
   def number2(self):
         self.number(2)
   def number3(self):
         self.number(3)
   def number4(self):
         self.number(4)
   def number5(self):
         self.number(5)
   def number6(self):
         self.number(6)
   def number7(self):
         self.number(7)
   def number8(self):
         self.number(8)
   def number9(self):
         self.number(9)

   def number(self, nr):
      self._keyPressed()
      self.play( self.page*10 + nr)

   def info_update(self):
     m = ''
     if self.mp3:
        m = "%i/%i " % (self.mp3id + 1, len(self.mp3) )
     s = str(self.p_title0 + ' ' +  m + self.p_title)
     print "aaaaaa", s
     self.setTitle(s)
     self["info"].setText(s)

   def play_mp3(self, plus = 1):
      print "AQPlay play_mp3", plus, self.mp3id
      self.mp3id = max(0, min(self.mp3id + plus, len(self.mp3) - 1 ))

      print "AQPlay play_mp3", plus, self.mp3id
      esr = "4097:0:0:0:0:0:0:0:0:0:" + self.mp3[self.mp3id]
      fileRef = eServiceReference(esr)
      self.session.nav.playService(fileRef)
      self.p_title = self.mp3[self.mp3id].split('/')[-1]
      self.info_update()

   def play(self,id):
      self.mp3 = None
      self.mpd("stop")
      if (id < 0) or (id >= len(self.pl)):
        id = 1
      if len(self.pl[id][1]) < 3:
         id = 1
      fn = self.pl[id][1]

      self.audiotrack = None
      print "AQplayer play:", fn
      if fn[0] == '/':
         if os.path.isdir(fn): # katalog z mp3
            self.mp3 = self.searchMusic(fn)
            if len(self.mp3) > 0:
               esr = "4097:0:0:0:0:0:0:0:0:0:" + self.mp3[0]
               self.mp3id = 0
         else:
            esr = "4097:0:0:0:0:0:0:0:0:0:" + fn
      elif fn.startswith('http://'):
        esr = "4097:0:0:0:0:0:0:0:0:0:" + quote(fn)
      elif fn.startswith('1:0:'):
        esr, audiotrack = fn.split('?')
        self.audiotrack = int(audiotrack)
      print "AQplayer play esr:", esr
      fileRef = eServiceReference(esr)
      if self.played == id:
         self.session.nav.stopService()
      self.played = id
      self.prevseek = 0
      self.session.nav.playService(fileRef)

      self.p_title0 = "%i.%s" % (id, self.pl[id][0])
      self.p_title = ''
      self.info_update()

      if self.audiotrack:
        self.selectSatTrack(self.audiotrack)

      if len(self.pl[self.played][2]) > 5:
        self.rdsurl = self.pl[self.played][2]
        self.rds = 40
      else:
        self.rdsurl = ''
        self.rds = 0
      print "AQPlayer rds:", self.rds, self.rdsurl 

   def up(self):
      self._keyPressed()
      if self.played + 1 < len(self.pl):
          self.play(self.played + 1)
      else:
          self.play(1)

   def down(self):
      self._keyPressed()
      if self.played - 1 > 0:
          self.play(self.played - 1 )
      else:
          self.play(len(self.pl))

   def blue(self):
      self.session.nav.stopService()
      self.mpd('play')

   def cancel(self):
      config.plugins.antyradio.startpos.setValue(self.played)
      config.plugins.antyradio.startpos.save()
      self.close(None)

   def hdmi1(self):
        try:
          from enigma import eHdmiCEC
          cmd = struct.pack('BBB', int("82",16),int("10",16),0)
          addressvaluebroadcast = int("0F",16)
          eHdmiCEC.getInstance().sendMessage(addressvaluebroadcast, len(cmd), str(cmd))
          cmd = struct.pack('B', int("85",16))
          eHdmiCEC.getInstance().sendMessage(addressvaluebroadcast, len(cmd), str(cmd))
        except:
          pass
   def hdmiWakeup(self):
      try:
        import Components.HdmiCec
        Components.HdmiCec.hdmi_cec.wakeupMessages()
      except:
        pass
      try:
          from enigma import eHdmiCEC
          addressvalue = int("0",16)
          wakeupmessage = int("04",16)
          cmd = struct.pack('B', wakeupmessage)
          eHdmiCEC.getInstance().sendMessage(addressvalue, len(cmd), str(cmd))
          reactor.callLater(1, self.hdmi1)
      except:
          pass

   def hdmiStandby(self):
      try:
        import Components.HdmiCec
        Components.HdmiCec.hdmi_cec.standbyMessages()
      except:
        pass
      try:
          from enigma import eHdmiCEC
          addressvalue = int("0",16)
          standbymessage=int("36",16)
          cmd = struct.pack('B', standbymessage)
          eHdmiCEC.getInstance().sendMessage(addressvalue, len(cmd), str(cmd))
          print "gooooooooo Standby"
      except:
          pass

   def halt(self):
        self.session.nav.stopService()

   def red(self):
        try:
            import configure
            reload(configure)
            self.session.open(configure.ConfigScreen)
        except:
            import traceback
            traceback.print_exc()

   def searchMusic(self, dir):
      m = []
      for root, dirs, files in os.walk(dir):
         for name in sorted(files):
            if name.lower().endswith((".mp3", ".mp2", ".ogg", ".wav", ".flac", ".m4a")):
               m.append(os.path.join(root, name))
      return m 
