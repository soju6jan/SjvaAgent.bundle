# -*- coding: utf-8 -*-
def Start():
    HTTP.Headers['Accept'] = 'text/html,application/json,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8'
    HTTP.Headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'
    HTTP.Headers['Accept-Language'] = 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7'


from .agent_movie import AgentMovie
from .agent_show import AgentShow
from .agent_music import AgentAlbum, AgentArtist
from .route_util import * 
     
"""
if tmp == 'Jav Censored':
    from .agent_jav_censored import AgentJavCensored
    from .agent_jav_censored_ama import AgentJavCensoredAma
    
elif tmp == 'Jav Censored Ama':
    from .agent_jav_censored_ama import AgentJavCensoredAma
    from .agent_jav_censored import AgentJavCensored
"""

