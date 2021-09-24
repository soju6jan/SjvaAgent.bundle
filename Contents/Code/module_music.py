# -*- coding: utf-8 -*-
import os, traceback, json, urllib, re, unicodedata, random
from .agent_base import AgentBase

class ModuleMusicArtist(AgentBase):
    module_name = 'music'
    
    def search(self, results, media, lang, manual, **kwargs):
        pass

    def update(self, metadata, media, lang):
        pass


class ModuleMusicAlbum(AgentBase):
    module_name = 'music'
    
    def search(self, results, media, lang, manual, **kwargs):
        pass

    def update(self, metadata, media, lang):
        pass
    