# -*- coding: UTF-8 -*-

from Components.config import config, getConfigListEntry
from Components.ConfigList import ConfigListScreen
from Components.ActionMap import ActionMap
from Components.Label import Label
from Screens.Screen import Screen
from enigma import getDesktop

class ConfigScreen(ConfigListScreen,Screen):
    screenWidth = getDesktop(0).size().width()
    if screenWidth and screenWidth == 1920:
        skin = """
            <screen position="center,center" size="840,600" title="Konfiguracja AntyRadio">
                <widget name="config" position="0,0" size="840,540" scrollbarMode="showOnDemand" font="Regular;32" itemHeight="54"/>
                <widget name="buttonred" position="20,520" size="220,60" valign="center" halign="center" zPosition="1"  transparent="1" foregroundColor="white" font="Bold;32" />
                <widget name="buttongreen" position="620,520" size="220,60" valign="center" halign="center" zPosition="1"  transparent="1" foregroundColor="white" font="Bold;32" />
                <ePixmap name="pred" position="20,520" size="220,60" zPosition="0" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on" />
                <ePixmap name="pgreen" position="620,520" size="220,60" zPosition="0" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on" />
            </screen>"""
    else:
        skin = """
            <screen position="center,cebter" size="550,400" title="Konfiguracja AntyRadio">
                <widget name="config" position="0,0" size="550,360" scrollbarMode="showOnDemand" />
                <widget name="buttonred" position="10,360" size="100,40" valign="center" halign="center" zPosition="1"  transparent="1" foregroundColor="white" font="Regular;18"/>
                <widget name="buttongreen" position="120,360" size="100,40" valign="center" halign="center" zPosition="1"  transparent="1" foregroundColor="white" font="Regular;18"/>
                <ePixmap name="pred" position="10,360" size="100,40" zPosition="0" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on"/>
                <ePixmap name="pgreen" position="120,360" size="100,40" zPosition="0" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on"/>
            </screen>"""
    def __init__(self, session):
        self.session = session
        Screen.__init__(self, session)
        self.list = []
        self.list.append(getConfigListEntry("Ustaw głośność przy starcie", config.plugins.antyradio.startvol))
        self.list.append(getConfigListEntry("Uruchom skrypt podczas usypiania/budzenia", config.plugins.antyradio.runscript))
        self.list.append(getConfigListEntry("Uruchom mpd przy starcie a nie radio", config.plugins.antyradio.runmpd))
        self.list.append(getConfigListEntry("Zmień kierunek klawiszy góra/dół", config.plugins.antyradio.invertkeys))
        if config.plugins.antyradio.useLibMedia.value:
            self.list.append(getConfigListEntry("Używaj do odtwarzania mediów biblioteki", config.plugins.antyradio.libMedia))

        ConfigListScreen.__init__(self, self.list)
        self["buttonred"] = Label(_("Cancel"))
        self["buttongreen"] = Label(_("Ok"))
        self["setupActions"] = ActionMap(["SetupActions"],
        {
            "green": self.save,
            "red": self.cancel,
            "save": self.save,
            "cancel": self.cancel,
            "ok": self.save,
        }, -2)
        self.onLayoutFinish.append(self.onLayout)

    def onLayout(self):
        # self.setTitle(_("Settings"))
        self.setTitle("Konfiguracja AntyRadio")

    def save(self):
        # print "saving"
        for x in self["config"].list:
            x[1].save()
        self.close(True)

    def cancel(self):
        # print "cancel"
        for x in self["config"].list:
            x[1].cancel()
        self.close(False)