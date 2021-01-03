# -*- coding: utf-8 -*-
import os, traceback, json, urllib, re, unicodedata
from .agent_base import AgentBase

class ModuleOttMovie(AgentBase):
    
    def search(self, results, media, lang, manual, **kwargs):
        try:
            Log('MMMMMMMMMMMMMMMMMMMMMMMMMMMMMMM')
            Log(kwargs)
            Log(media)
            Log(type(media))  # 
            Log(str(kwargs))


            Log('media.id : %s', media.id)
            Log('media.filename : %s', media.filename)

            #keyword = self.get_search_keyword(media, manual, from_file=True)
            #keyword = keyword.replace(' ', '-')
            #self.base_search(results, media, lang, manual, keyword)

            data = AgentBase.my_JSON_ObjectFromURL('http://127.0.0.1:32400/library/metadata/%s' % media.id)
            #Log(data)
            Log(json.dumps(data, indent=4))

            Log(media.name)
            Log(media.year)
            Log(media.guid)

            
            meta = MetadataSearchResult(id='OT', name=media.name, year=media.year, score=100, lang=lang)
            meta.summary = "test"
            meta.type = "movie"
            results.Append(meta)
            Log('>> append')
            Log(results)

        except Exception as exception: 
            Log('Exception:%s', exception)
            Log(traceback.format_exc())    


    def update(self, metadata, media, lang):
        try:
            Log(metadata.id)
            Log(type(metadata))

            Log(media.id)
            Log(type(media))  #<class 'Framework.api.agentkit.MediaTree'>
            
            Log(media.items)
            Log(media.settings)
            Log(media.children)

            Log(media.items[0].parts)



            data = media.all_parts()
            for tmp in data:
                Log(tmp)
                Log(type(tmp)) #<class 'Framework.api.agentkit.MediaPart'>  <Part>태그
                Log(tmp.streams)
                Log('IIIIIIIIIIIIID : %s', tmp.id)
                #Log(getattr(tmp, 'uuid'))
                #Log(getattr(tmp, 'file'))
                #Log(getattr(tmp, 'size'))
                #setattr(tmp, 'container', 'mpegts')
            #self.base_update(metadata, media, lang)

    
            url = 'sjva://sjva.me/video.mp4/https://cc3001.dmm.co.jp/litevideo/freepv/s/sni/snis00968/snis00968_dmb_w.mp4'
            metadata.extras.add(TrailerObject(url=url, title='aaa'))

            url = 'sjva://sjva.me/video.m3u8/https://gtm-spotv.brightcovecdn.com/abf18bbf3b3f4a0db4a41dd2af7f75c6/ap-northeast-1/5764318566001/playlist.m3u8?__nn__=5981484117001&hdnea=st=1609473600~exp=1609477200~acl=/abf18bbf3b3f4a0db4a41dd2af7f75c6/ap-northeast-1/5764318566001/*~hmac=c3bb618318ff15acae3ab441e3216e95a3e358a662d68f1a7e0d084b896145cb'
            metadata.extras.add(TrailerObject(url=url, title='bbb'))

            media.items.append(MediaObject(url=url, title='bbb'))
            

            return
        except Exception as exception: 
            Log('Exception:%s', exception)
            Log(traceback.format_exc())  

    #identifier, media_type, lang, manual, kwargs, version, primary=False):


"""
<Media id="69652" audioCodec="aac" videoCodec="h264" container="mp4">
<Part accessible="1" exists="1" id="75147" container="mp4" key="https://cc3001.dmm.co.jp/litevideo/freepv/1/118/118abw00043/118abw00043_mhb_w.mp4" optimizedForStreaming="1">
<Stream id="151818" streamType="1" codec="h264" index="0" displayTitle="알 수 없음 (H.264)" extendedDisplayTitle="알 수 없음 (H.264)"> </Stream>
<Stream id="151819" streamType="2" selected="1" codec="aac" index="1" channels="2" displayTitle="알 수 없음 (AAC Stereo)" extendedDisplayTitle="알 수 없음 (AAC Stereo)"> </Stream>
</Part>
</Media>
"""

