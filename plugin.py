# -*- coding: utf-8 -*-
from enigma import eDVBVolumecontrol
from Components.ActionMap import ActionMap
from Components.AVSwitch import AVSwitch
from Components.ConfigList import ConfigListScreen
from Components.config import config, getConfigListEntry, ConfigSubsection, ConfigSelection, ConfigDirectory, NoSave, ConfigNothing, ConfigYesNo, ConfigText, ConfigInteger
from Components.Label import Label
from Components.Sources.StaticText import StaticText
from Components.SystemInfo import SystemInfo
from Plugins.Plugin import PluginDescriptor
from Screens.Screen import Screen
from Screens.Standby import Standby
import os

config.plugins.antyradio = ConfigSubsection()
config.plugins.antyradio.startvol = ConfigSelection(default="0", choices = [("0", "last"),("10", "10"), ("20", "20"), ("30", "30"), ("40", "40"), ("50", "50"), ("60", "60"), ("70", "70"), ("80", "80"), ("90", "90"), ("100", "100")])
config.plugins.antyradio.startpos = ConfigInteger(default = 1)
config.plugins.antyradio.runscript = ConfigYesNo(default = False)
config.plugins.antyradio.runmpd = ConfigYesNo(default = False)
config.plugins.antyradio.invertkeys = ConfigYesNo(default = False)
config.plugins.antyradio.useLibMedia = ConfigYesNo(default = False)
config.plugins.antyradio.libMedia = ConfigSelection(default='gst', choices=[('gst', 'GStreamer'), ('ep3', 'EPlayer3')])

fname = "/proc/%d/maps" % os.getpid()
libMediaTest = False
with open(fname) as f:
    for line in f:
        if 'libeplayer3' in line:
            libMediaTest = True
            break

if libMediaTest:
    if config.plugins.antyradio.useLibMedia.value == False:
        config.plugins.antyradio.useLibMedia.value = True
        config.plugins.antyradio.useLibMedia.save()
else:
    if config.plugins.antyradio.useLibMedia.value == True:
        config.plugins.antyradio.useLibMedia.value = False
        config.plugins.antyradio.useLibMedia.save()

StandbyScreen__init__ = None

def Plugins(**kwargs):
    return [
        PluginDescriptor(name = "AntyRadio", description = "Simple radio player by Areq", where = PluginDescriptor.WHERE_PLUGINMENU, icon="antyradio.png", fnc=startSetup),
        PluginDescriptor(name = "AntyRadio", description = "Simple radio player by Areq", where = PluginDescriptor.WHERE_EXTENSIONSMENU, fnc=startSetup),
        PluginDescriptor(where = PluginDescriptor.WHERE_SESSIONSTART, fnc = sessionstart),
        PluginDescriptor(where = PluginDescriptor.WHERE_AUTOSTART, fnc=autostart)]

atr_first = True

def sessionstart(reason, **kwargs):
    global atr_first
    if "session" in kwargs and atr_first:
        atr_first = False
        import version
        u = version.Update(kwargs["session"])

def autostart(reason, *args, **kwargs):
    if reason == 0:
        try:
            if not os.path.isfile('/usr/lib/enigma2/python/Plugins/Extensions/AntyRadio/playlist.txt'):
                s = open('/usr/lib/enigma2/python/Plugins/Extensions/AntyRadio/playlist.txt.example').read()
                open('/usr/lib/enigma2/python/Plugins/Extensions/AntyRadio/playlist.txt','w').write(s)
        except:
            pass
        StandbyScreenInit()

def StandbyScreenInit():
    global StandbyScreen__init__
    if StandbyScreen__init__ is None:
        StandbyScreen__init__ = Standby.__init__
    Standby.__init__ = AntyRadioStandby__init__
    Standby.toggleMute = ToggleMute
    Standby.volUp = VolUp
    Standby.volDown = VolDown
    Standby.leaveMute = LeaveMute
    Standby.toggleAntyRadio = ToggleAntyRadio
    Standby.__aqCallback = __aqCallback
    Standby.__aqPower = __aqPower
    Standby.aqwakeup = aqwakeup

def AntyRadioStandby__init__(self, session):
  StandbyScreen__init__(self, session)
  self.aqwakeup(False)
  self["actions"] = ActionMap( [ "StandbyActions", "GlobalActions", "OkCancelActions", "TvRadioActions"],
    {
      "power": self.__aqPower,
      "power_make": getattr(self, 'Power_make', 'Power'),
      "power_break": getattr(self, 'Power_break', 'Power'),
      "power_long": getattr(self, 'Power_log', 'Power'),
      "power_repeat": getattr(self, 'Power_repeat', 'Power'),
      "discrete_on": self.__aqPower,
      "volumeMute": self.toggleMute,
      "volumeDown": self.volDown,
      "volumeUp": self.volUp,
      "ok": self.toggleAntyRadio,
      "keyRadio": self.toggleAntyRadio
    }, -1)
  self.volctrl = eDVBVolumecontrol.getInstance()
  self.downmix_config = config.av.downmix_ac3.value
  self.AntyRadio_enabled = False
  #if config.plugins.antyradio.standby_autostart.value:
  #  self.toggleAntyRadio()


def aqwakeup(self, s = True):
    if config.plugins.antyradio.runscript.value:
        f = "/usr/lib/enigma2/python/Plugins/Extensions/AntyRadio/standby.sh"
        if s:
            f = "/usr/lib/enigma2/python/Plugins/Extensions/AntyRadio/wakeup.sh"
        import os, os.path
        if os.path.isfile(f):
            os.system("/bin/sh %s &" % f)

def __aqPower(self):
    self.aqwakeup(True)
    self.Power()

def VolUp(self):
    self.volctrl.volumeUp()

def VolDown(self):
    self.volctrl.volumeDown()

def ToggleAntyRadio(self):
    is_encoder = open("/proc/stb/avs/0/input", "r").read()[:-1].find("encoder") != -1
    is_mute = self.volctrl.isMuted()
    self.aqwakeup(not self.AntyRadio_enabled)
    if self.AntyRadio_enabled:
        self.AntyRadio_enabled = False
        config.av.downmix_ac3.value = self.downmix_config
        if not is_mute:
            self.volctrl.volumeToggleMute()
        if is_encoder:
            if SystemInfo["ScartSwitch"]:
                self.avswitch.setInput("SCART")
            else:
                self.avswitch.setInput("AUX")
    else:
        self.AntyRadio_enabled = True
        config.av.downmix_ac3.value = True
        if is_mute:
            self.volctrl.volumeToggleMute()
        if not is_encoder:
            self.avswitch.setInput("ENCODER")

        from Plugins.Extensions.AntyRadio.aqplayer import AQPlayer
        self.session.openWithCallback(self.__aqCallback, AQPlayer)

def __aqCallback(self, cos = None):
   self.AntyRadio_enabled = True
   self.toggleAntyRadio()

def ToggleMute(self):
    self.volctrl.volumeToggleMute()

def LeaveMute(self):
    config.av.downmix_ac3.value = self.downmix_config
    if self.volctrl.isMuted():
        eDVBVolumecontrol.getInstance().volumeToggleMute()

def startSetup(session, **kwargs):
    try:
        import aqplayer
        reload(aqplayer)
        session.open(aqplayer.AQPlayer)
    except:
        import traceback
        traceback.print_exc()
