# -*- coding: utf-8 -*-
class SjvaAgentKtv(Agent.TV_Shows):
    name = u'SJVA 국내TV (dummy)'
    
    fallback_agent = 'com.plexapp.agents.sjva_agent'
    languages = [Locale.Language.Korean]
    primary_provider = True

    def search(self, results, media, lang, manual, **kwargs):
        pass
