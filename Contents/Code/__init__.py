# -*- coding: utf-8 -*-
import os
import functools
import subprocess
import threading
from distutils.spawn import find_executable

import Framework

from .agent_movie import AgentMovie
from .agent_show import AgentShow
from .agent_music import AgentAlbum, AgentArtist
from .route_util import *

Log = Log # type: Framework.api.logkit.LogKit
Proxy = Proxy # type: Framework.api.modelkit.ProxyKit
HTTP = HTTP # type: Framework.api.networkkit.HTTPKit
Prefs = Prefs # type: Framework.api.runtimekit.PrefsKit

"""
if tmp == 'Jav Censored':
    from .agent_jav_censored import AgentJavCensored
    from .agent_jav_censored_ama import AgentJavCensoredAma

elif tmp == 'Jav Censored Ama':
    from .agent_jav_censored_ama import AgentJavCensoredAma
    from .agent_jav_censored import AgentJavCensored
"""

ORIGINAL_HTTP_REQUEST_FUNC = HTTP.Request
ORIGINAL_PROXY_PREVIEW_FUNC = Proxy.Preview
ORIGINAL_PROXY_MEDIA_FUNC = Proxy.Media
ORIGINAL_STORAGE_SAVE_FUNC = Framework.components.storage.Storage.save
FFMPEG_PATH = find_executable('ffmpeg', os.environ['PATH'])
DWEBP_PATH = find_executable('dwebp', os.environ['PATH'])


def Start():
    HTTP.Request = ORIGINAL_HTTP_REQUEST_FUNC
    HTTP.Request = request_wrapper(HTTP.Request)
    Proxy.Preview = ORIGINAL_PROXY_PREVIEW_FUNC
    Proxy.Preview = proxy_wrapper(Proxy.Preview)
    Proxy.Media = ORIGINAL_PROXY_MEDIA_FUNC
    Proxy.Media = proxy_wrapper(Proxy.Media)
    Framework.components.storage.Storage.save = ORIGINAL_STORAGE_SAVE_FUNC
    Framework.components.storage.Storage.save = storage_save_wrapper(Framework.components.storage.Storage.save)
    Log.Debug("ffmpeg 경로: %s", FFMPEG_PATH)
    Log.Debug("dwebp 경로: %s", DWEBP_PATH)


def d(data):
    import json
    return json.dumps(data, indent=4, ensure_ascii=False)


def kill_process(process):
    try:
        if process and process.poll() is None:
            process.kill()
    except Exception:
        Log.Error("FFmpeg 프로세스 종료 실패")


def convert_webp(webp_data):
    if DWEBP_PATH:
        cmd = [
            DWEBP_PATH,
            '-quiet',
            '-o', '-',
            '--', '-'
        ]
        mode = 'dwebp (WEBP -> PNG)'
    elif FFMPEG_PATH:
        cmd = [
            FFMPEG_PATH,
            '-hide_banner',
            '-loglevel', 'error',
            '-i', 'pipe:0',
            '-vframes', '1',
            '-f', 'image2pipe',
            '-vcodec', 'mjpeg',
            'pipe:1'
        ]
        mode = 'ffmpeg (WEBP -> JPEG)'
    else:
        return webp_data

    process = None
    timer = None
    try:
        process = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        timer = threading.Timer(30, kill_process, (process,))
        timer.daemon = True
        timer.start()

        out, err = process.communicate(input=webp_data)
        if process.returncode == 0 and out:
            Log.Debug(mode)
            return out
        else:
            error_message = err.decode('utf-8', 'ignore') if err else "No error message"
            Log.Error("%s 오류: %s", mode, error_message)
    except Exception as e:
        Log.Exception("%s 실패: %s", mode, str(e))
    finally:
        if timer:
            timer.cancel()
        kill_process(process)
    return webp_data


def is_webp(data):
    if not data or len(data) < 16:
        return False
    # .avi. .wav 등 도 RIFF
    if data[0:4] == b'RIFF' and data[8:12] == b'WEBP':
        return True
    return False


def request_wrapper(func):
    @functools.wraps(func)
    def wrapped(*args, **kwds):
        #kwds.setdefault('headers', {'Accept': 'image/webp,image/jpeg,image/png,image/*;q=0.8,*/*;q=0.5'})
        #이미지는 캐시 안 됨
        #kwds.setdefault('cacheTime', 300)
        if 'timeout' not in kwds:
            try:
                user_timeout = int(Prefs['timeout'])
            except Exception:
                user_timeout = 0
            kwds['timeout'] = user_timeout
        if 'format=webp' in args[0]:
            args = list(args)
            args[0] = args[0].replace('format=webp', 'format=jpeg')
        response = func(*args, **kwds)
        #if 'content-type' in response.headers:
        #    Log.Debug("%s - %s", args[0], response.headers['content-type'])
        return response
    return wrapped


def proxy_wrapper(func):
    @functools.wraps(func)
    def wrapped(*args, **kwds):
        try:
            if is_webp(args[0]):
                Log.Debug("WEBP 데이터 발견")
                args = list(args)
                args[0] = convert_webp(args[0])
        except Exception as e:
            Log.Exception(str(e))
        return func(*args, **kwds)
    return wrapped


def shorten_plex_path(full_path):
    norm_path = os.path.normpath(full_path)
    anchor = os.path.join("Library", "Application Support", "Plex Media Server")
    lower_path = norm_path.lower()
    lower_anchor = anchor.lower()
    idx = lower_path.find(lower_anchor)
    if idx != -1:
        after_anchor_idx = idx + len(lower_anchor)
        remaining = norm_path[after_anchor_idx:]
        remaining = remaining.lstrip(os.sep)
        return os.path.join('...', remaining)
    return norm_path


def storage_save_wrapper(func):
    @functools.wraps(func)
    def wrapped(*args, **kwds):
        # def save(self, filename, data, binary=True, mtime_key=None):
        filename = None
        shorten_filename = None
        data = None
        try:
            _, filename, data = args[:3]
            shorten_filename = shorten_plex_path(filename)
            if is_webp(data):
                Log.Debug("WEBP 데이터 발견: %s", shorten_filename)
                args = list(args)
                args[2] = convert_webp(data)
            #elif not data or len(data) < 16:
            #    Log.Debug("의심되는 데이터: %s (%d bytes)", shorten_filename, len(data))
        except Exception as e:
            Log.Exception(str(e))
        result = func(*args, **kwds)
        if shorten_filename:
            #Log.Debug('저장: %s (%d)', shorten_filename, len(data) if data else 0)
            pass
        return result
    return wrapped