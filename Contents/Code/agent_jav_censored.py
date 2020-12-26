# -*- coding: utf-8 -*-
import os, traceback, json, urllib, re, unicodedata
from .agent_base import AgentBase

class AgentJavCensored(Agent.Movies, AgentBase):
    module_name = 'jav_censored'
    name = "SJVA JAV Censored"
    languages = [Locale.Language.Korean]
    primary_provider = True
    accepts_from = ['com.plexapp.agents.localmedia', 'com.plexapp.agents.xbmcnfo']
    contributes_to = ['com.plexapp.agents.xbmcnfo']
    
    def search(self, results, media, lang, manual):
        keyword = self.get_search_keyword(media, manual, from_file=True)
        keyword = keyword.replace(' ', '-')
        self.base_search(results, media, lang, manual, keyword)

    def update(self, metadata, media, lang):
        self.base_update(metadata, media, lang)
