# -*- coding: utf-8 -*-
import os, unicodedata, urllib2
from .agent_base import AgentBase, get_sort_key

Core = Core # Framework.core.FrameworkCore
parallelize = parallelize # Framework.api.threadkit._parallelize_decorator
task = task # Framework.api.threadkit._task_decorator
Log = Log # type: Framework.api.logkit.LogKit
Regex = Regex # type: Framework.api.utilkit.RegexKit
MetadataSearchResult = MetadataSearchResult # type: Framework.objects.MetadataSearchResult
Datetime = Datetime # Framework.api.utilkit.DatetimeKit
Proxy = Proxy # type: Framework.api.modelkit.ProxyKit
HTTP = HTTP # type: Framework.api.networkkit.HTTPKit
Prefs = Prefs # type: Framework.api.runtimekit.PrefsKit
JSON = JSON # type: Framework.api.parsekit.JSONKit
String = String # type: Framework.api.utilkit.StringKit
unicode = unicode

class ModuleFtv(AgentBase):
    module_name = 'ftv'

    def search(self, results, media, lang, manual):
        try:
            code = self.get_code_from_folderpath(media)
            if code != None and code.startswith('MT'):
                code = code.replace('MT', 'FT')
            if code != None and code.startswith('F'):
                meta = MetadataSearchResult(id=code, name=code, year=1900, score=200, thumb="", lang=lang)
                results.Append(meta)
                if not manual:
                    return
        except Exception as e:
            Log.Exception(str(e))

        try:
            if manual and media.show is not None:
                if media.show.startswith('K'):
                    return False
                elif media.show.startswith('FT'):
                    code = media.show
                    meta = MetadataSearchResult(id=code, name=code, year='', score=100, thumb="", lang=lang)
                    results.Append(meta)
                    return

            if self.is_read_json(media):
                if manual:
                    self.remove_info(media)
                else:
                    info_json = self.get_info_json(media)
                    if info_json is not None:
                        # ftv에서 ktv json을 사용하려고할때 에러
                        if 'show' in info_json:
                            code = info_json['show']['code']
                            meta = MetadataSearchResult(id=code, name=info_json['show']['title'], year=info_json['show']['year'], score=100, thumb="", lang=lang)
                            results.Append(meta)
                            return


            media.show = unicodedata.normalize('NFC', unicode(media.show)).strip()
            Log('SEARCH : %s' % media.show)
            keyword = media.show
            Log('>> [%s] [%s] [%s]' % (self.module_name, keyword, media.year))
            search_data = self.send_search(self.module_name, keyword, manual, year=media.year)

            if not search_data:
                return False

            for item in search_data:
                meta = MetadataSearchResult(id=item['code'], name=item['title'], year=item['year'], score=item['score'], thumb=item['image_url'], lang=lang)
                meta.summary = self.change_html(item['desc']) + self.search_result_line() + item['site'] + ' 원제 : %s' % item['title_original']
                meta.type = "movie"
                results.Append(meta)


            return

        except Exception as e:
            Log.Exception(str(e))



    def update(self, metadata, media, lang):
        #self.base_update(metadata, media, lang)
        try:
            seasons_to_update = JSON.ObjectFromString(Prefs['seasons_to_update']) or {}
        except Exception:
            seasons_to_update = {}
        Log("[%s] seasons to update: %s", media.id, seasons_to_update)

        guid_parts = self.parse_guid(metadata.guid)
        if guid_parts.get('is_episode'):
            Log.Debug("[%s] Update episode: %s", media.id, guid_parts.get('episode'))
            Log.Debug("[%s] 에피소드만 메타데이터 새로고침하면 에피소드 전용 번들 폴더에 저장됨", media.id)
            return

        meta_info = None
        info_json = None
        is_write_json = self.is_write_json(media)

        if self.is_read_json(media):
            info_json = self.get_info_json(media)
            if isinstance(info_json, dict):
                meta_info = info_json.get('show')
        if not meta_info:
            meta_info = self.send_info(self.module_name, metadata.id)
            if isinstance(meta_info, dict) and is_write_json:
                self.save_info(media, {'show' : meta_info})
        #Log(json.dumps(meta_info, indent=4))
        section_id = self.get_section_id(media.id)
        try:
            self.update_info(metadata, meta_info, media, section_id)
        except Exception:
            Log.Exception("기본 정보 업데이트 실패")
        @parallelize
        def UpdateSeasons():
            index_list = sorted(media.seasons.keys(), key=get_sort_key)
            Log.Debug('[%s] Season indexes: %s', media.id, index_list)

            for media_season_index in index_list:
                Log.Debug('[%s] Current season index: %s', media.id, media_season_index)
                try:
                    """
                    2026-03-17 halfaider
                    사용자 설정값에서 지정한 시즌만 업데이트
                    """
                    if media.id in seasons_to_update and int(media_season_index) not in (seasons_to_update.get(media.id) or ()):
                        Log.Info("[%s] 업데이트 건너뛰기: %s", media.id, media_season_index)
                        continue
                    #if media_season_index == '0':
                    #    continue

                    media_season_index_for_meta = self.convert_season_index(media_season_index)
                    season_code = '%s_%s' % (metadata.id, media_season_index_for_meta)
                    if isinstance(info_json, dict) and season_code in info_json:
                        season_meta_info = info_json.get(season_code)
                    else:
                        season_meta_info = self.send_info(self.module_name, season_code)
                        if isinstance(season_meta_info, dict) and is_write_json:
                            self.append_info(media, season_code, season_meta_info)

                    @task
                    def UpdateSeason(metadata=metadata, media=media, media_season_index=media_season_index, season_meta_info=season_meta_info, media_season_index_for_meta=media_season_index_for_meta, section_id=section_id):
                        metadata_season = metadata.seasons[media_season_index]
                        self.update_season(media_season_index, metadata_season, season_meta_info, media, media_season_index_for_meta, section_id)

                    # 에피소드 업데이트
                    meta_info_episodes = season_meta_info.get('episodes') or {}
                    media_episodes = media.seasons[media_season_index].episodes
                    metadata_episodes = metadata.seasons[media_season_index].episodes

                    count_metadata = len(metadata_episodes)
                    count_media = len(media_episodes)
                    count_api = len(meta_info_episodes)
                    Log.Debug("[%s] Episode count: API=%s Metadata=%s Media=%s Missing=%s", media.id, count_api, count_metadata, count_media, count_api - max(count_metadata, count_media))

                    for media_episode_index in media_episodes:
                        metadata_episode = metadata_episodes[media_episode_index]
                        meta_info_episode = meta_info_episodes.get(media_episode_index)

                        @task
                        def UpdateEpisode(metadata_episode=metadata_episode, meta_info_episode=meta_info_episode, media_season_index=media_season_index, media_episode_index=media_episode_index):
                            Log('UpdateEpisode : %s - %s', media_season_index, media_episode_index)
                            self.reset_episode_metadata(metadata_episode)
                            try:
                                if meta_info_episode:
                                    try: metadata_episode.originally_available_at = Datetime.ParseDate(meta_info_episode['premiered']).date()
                                    except Exception: pass
                                    metadata_episode.title = meta_info_episode.get('title') or ''
                                    metadata_episode.summary = meta_info_episode.get('plot') or ''
                                    try:
                                        valid_names = set()
                                        arts = meta_info_episode.get('art')
                                        if isinstance(arts, list) and len(arts) > 0:
                                            image_url = arts[-1]
                                            self.set_http_data(image_url, metadata_episode.thumbs, valid_names)
                                        metadata_episode.thumbs.validate_keys(valid_names)
                                    except Exception as e:
                                        Log.Exception(str(e))
                                    for name in meta_info_episode.get('writer') or ():
                                        metadata_episode.writers.new().name = name
                                    for name in meta_info_episode.get('director') or ():
                                        metadata_episode.directors.new().name = name
                                    for name in meta_info_episode.get('guest') or ():
                                        metadata_episode.guest_stars.new().name = name
                            except Exception as e:
                                Log.Exception(str(e))
                except Exception:
                    Log.Exception("[%s] 시즌 업데이트 실패: %s", media.id, media_season_index)





    def update_info(self, metadata, meta_info, media, section_id):
        metadata.title = meta_info.get('title') or ''
        metadata.original_title = meta_info.get('originaltitle') or ''

        try:
            url = 'http://127.0.0.1:32400/library/sections/%s/all?type=2&id=%s&originalTitle.value=%s' % (section_id, media.id, String.Quote(metadata.original_title.encode('utf8')))
            request = PutRequest(url, headers={'X-Plex-Token': self.get_token()})
            response = urllib2.urlopen(request)
            status_code = response.getcode()
            if not status_code == 200:
                Log("[%s] TV Show 정보 업데이트 실패: status %s", media.id, status_code)
        except Exception as e:
            Log.Exception(str(e))
        metadata.title_sort = unicodedata.normalize('NFKD', metadata.title)
        studio = meta_info.get('studio')
        if isinstance(studio, list):
            metadata.studio = studio[0] if studio else ''
        else:
            metadata.studio = studio or ''
        try: metadata.originally_available_at = Datetime.ParseDate(meta_info['premiered']).date()
        except Exception: pass
        metadata.content_rating = meta_info.get('mpaa') or ''
        metadata.summary = meta_info.get('plot') or ''

        metadata.genres.clear()
        for tmp in meta_info.get('genre') or ():
            metadata.genres.add(tmp)
        #if meta_info['episode_run_time'] > 0:
        #    metadata.duration = meta_info['episode_run_time']

        # 부가영상
        self.set_extras(metadata, meta_info)

        # rating
        for item in meta_info.get('ratings') or ():
            name = item.get('name')
            rating = item.get('value')
            if name == 'tmdb' and rating is not None:
                metadata.rating = rating
                metadata.audience_rating = 0.0
                metadata.rating_image = 'imdb://image.rating'

        # role
        metadata.roles.clear()
        self.set_roles(metadata, meta_info)

        # clear logo, slug
        self.plex_exclusive(media.id, section_id)
        self.update_logo(media.id, section_id, meta_info.get('art') or ())

        # poster
        art_map = {'poster': [metadata.posters, set()], 'landscape' : [metadata.art, set()], 'banner':[metadata.banners, set()]}
        for item in sorted(meta_info.get('art') or (), key=lambda k: k.get('score') or 0, reverse=True):
            image_url = item.get('value') or item.get('thumb')
            aspect = item.get('aspect') or 'poster'
            target = art_map.get(aspect)
            if target is None or not image_url or image_url in target[1]:
                continue
            try:
                self.set_http_data(image_url, target[0], target[1], preview=item.get('thumb'))
            except Exception as e:
                Log.Exception(str(e))
        metadata.posters.validate_keys(art_map['poster'][1])
        metadata.art.validate_keys(art_map['landscape'][1])
        metadata.banners.validate_keys(art_map['banner'][1])

        # 테마
        valid_names = []
        if meta_info.get('use_theme'):
            tvdb_id = None
            for tmp in meta_info.get('code_list') or ():
                if len(tmp) > 1 and tmp[0] == 'tvdb_id':
                    tvdb_id = tmp[1]
                    break
            self.set_themes(metadata, meta_info, valid_names, tvdb_id)
        metadata.themes.validate_keys(valid_names)


    def update_season(self, season_no, metadata_season, meta_info, media, media_season_index_for_meta, section_id):
        #Log(json.dumps(meta_info, indent=4))
        templates = {
            'poster': (metadata_season.posters, set()),
            'landscape' : (metadata_season.art, set()),
            'banner':[metadata_season.banners, set()]
        }
        Log.Debug('[%s] 업데이트 시즌: %s as %s', media.id, season_no, media_season_index_for_meta)
        for item in sorted(meta_info.get('art') or (), key=lambda k: k.get('score') or 0, reverse=True):
            image_url = item.get('value') or item.get('thumb')
            aspect = item.get('aspect') or 'poster'
            process = templates.get(aspect)
            if not process or not image_url or image_url in process[1]:
                continue
            try:
                self.set_http_data(image_url, process[0], process[1], preview=item.get('thumb'))
            except Exception:
                Log.Exception('시즌 포스터 다운로드 중 오류')

        metadata_season.summary = meta_info.get('plot') or ''
        metadata_season.title = meta_info.get('season_name') or ''
        for _, containers in templates.items():
            containers[0].validate_keys(containers[1])

        # 2022-05-12
        if True or int(season_no) > 100:
            # 시즌 title, summary
            try:
                filepath = media.seasons[season_no].all_parts()[0].file
                tmp = os.path.basename(os.path.dirname(filepath))
                season_title = metadata_season.title

                match = Regex(r'^(Season|시즌)\s(?P<force_season_num>\d{1,8})((\s|\.)(?P<season_title>.*?))?$', Regex.IGNORECASE).search(tmp)
                #match = Regex(r'(?P<season_num>\d{1,8})\s*(?P<season_title>.*?)$').search(tmp)
                if match:
                    if match.group('force_season_num') == season_no and match.group('season_title') is not None:
                        season_title = match.group('season_title')

                url = 'http://127.0.0.1:32400/library/sections/%s/all?type=3&id=%s&title.value=%s&summary.value=%s' % (section_id, media.seasons[season_no].id, String.Quote(season_title.encode('utf8')), String.Quote(metadata_season.summary.encode('utf8')))
                request = PutRequest(url, headers={'X-Plex-Token': self.get_token()})
                response = urllib2.urlopen(request)
                status_code = response.getcode()
                if not status_code == 200:
                    Log("[%s] 시즌 정보 업데이트 실패: status %s", media.id, status_code)
            except Exception as e:
                Log.Exception(str(e))

        else:
            # 시즌 title, summary
            try:
                url = 'http://127.0.0.1:32400/library/metadata/%s' % media.id
                data = JSON.ObjectFromURL(url)
                section_id = data['MediaContainer']['librarySectionID']
                url = 'http://127.0.0.1:32400/library/sections/%s/all?type=3&id=%s&title.value=%s&summary.value=%s' % (section_id, media.seasons[season_no].id, String.Quote(metadata_season.title.encode('utf8')), String.Quote(metadata_season.summary.encode('utf8')))
                request = PutRequest(url, headers={'X-Plex-Token': self.get_token()})
                response = urllib2.urlopen(request)
            except Exception as e:
                Log.Exception(str(e))


class PutRequest(urllib2.Request):
    def __init__(self, *args, **kwargs):
        return urllib2.Request.__init__(self, *args, **kwargs)

    def get_method(self, *args, **kwargs):
        return 'PUT'
