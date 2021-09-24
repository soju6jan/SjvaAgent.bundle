# -*- coding: utf-8 -*-
import os, traceback, json, urllib, re, unicodedata, time
# /:/plugins/com.plexapp.agents.sjva_agent/function/version?X-Plex-Token=%s' % (server_url, server_token)

@route('/version') 
def version():
    from .version import VERSION
    return VERSION


@route('/kakao') 
def kakao(content_id):
    #content_id = '414068276'
    try:
        url = 'https://tv.kakao.com/katz/v2/ft/cliplink/{}/readyNplay?player=monet_html5&profile=HIGH&service=kakao_tv&section=channel&fields=seekUrl,abrVideoLocationList&startPosition=0&tid=&dteType=PC&continuousPlay=false&contentType=&{}'.format(content_id, int(time.time()))
        data = JSON.ObjectFromURL(url)
        video_url = data['videoLocation']['url']
        Log('Kakao : %s', video_url)
        return Redirect(video_url)
    except Exception as e: 
        Log('Exception:%s', e)
        Log(traceback.format_exc())

@route('/wavve') 
def wavve(sjva_url):
    try:
        #autoAdjustQuality=0&hasMDE=1&location=lan&mediaBufferSize=74944
        #content_id = '414068276'
        Log('111111111111111111111')
        Log(sjva_url)
        data = JSON.ObjectFromURL(sjva_url)
        url = data['url']
        Log('url : %s', url)
        data = JSON.ObjectFromURL(url)
        Log(data)
        #video_url = data['playurl'].replace('chunklist5000.m3u8', '5000/chunklist.m3u8')
        video_url = data['playurl']
        Log('mmmmmmmmmmmmmmmmmmmmmmmmmmm')
        Log(video_url)
        return Redirect(video_url)

        #https://vod.cdn.wavve.com/hls/M01/M_1003704100074100000.1/2/chunklist5000.m3u8?authtoken=MwqNqlFFcEaupkQpVUA-IEHhqAPlgeh-Y7pAGdoE9nk5NDEXjKZUz5XMRqiaYcuVO6_SZolp7ebchKtzrU8xeA5-I77dFrcHCEw3C_WxBECY4_2Lp_rwqAHdhUQ57iNYtxTq8xbhGThobXbBij5hXavNkavwZGXIrn66AVWXDEeAIDV_9VIyQiSsrNyhoa06U2QA_u0B1i7BnX3gNBo


        #5000/chunklist.m3u8?authtoken=MwqNqlFFcEaupkQpVUA-IEHhqAPlgeh-Y7pAGdoE9nk5NDEXjKZUz5XMRqiaYcuVO6_SZolp7ebchKtzrU8xeA5-I77dFrcHCEw3C_WxBECY4_2Lp_rwqAHdhUQ57iNYtxTq8xbhGThobXbBij5hXavNkavwZGXIrn66AVWXDEeAIDV_9VIyQiSsrNyhoa06U2QA_u0B1i7BnX3gNBo

        return
        url = 'https://tv.kakao.com/katz/v2/ft/cliplink/{}/readyNplay?player=monet_html5&profile=HIGH&service=kakao_tv&section=channel&fields=seekUrl,abrVideoLocationList&startPosition=0&tid=&dteType=PC&continuousPlay=false&contentType=&{}'.format(content_id, int(time.time()))
        data = JSON.ObjectFromURL(url)
        video_url = data['videoLocation']['url']
        Log('Kakao : %s', video_url)
        return Redirect(video_url)
    except Exception as e: 
        Log('Exception:%s', e)
        Log(traceback.format_exc())