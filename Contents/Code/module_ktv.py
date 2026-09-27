# -*- coding: utf-8 -*-
import os, json, unicodedata, urllib2
from .agent_base import AgentBase, PutRequest, get_sort_key

Core = Core # Framework.core.FrameworkCore
parallelize = parallelize # Framework.api.threadkit._parallelize_decorator
task = task # Framework.api.threadkit._task_decorator
Log = Log # type: Framework.api.logkit.LogKit
Regex = Regex # type: Framework.api.utilkit.RegexKit
MetadataSearchResult = MetadataSearchResult # type: Framework.objects.ObjectFactory
Datetime = Datetime # Framework.api.utilkit.DatetimeKit
Proxy = Proxy # type: Framework.api.modelkit.ProxyKit
HTTP = HTTP # type: Framework.api.networkkit.HTTPKit
Prefs = Prefs # type: Framework.api.runtimekit.PrefsKit
JSON = JSON # type: Framework.api.parsekit.JSONKit
String = String # type: Framework.api.utilkit.StringKit


class ModuleKtv(AgentBase):
    module_name = 'ktv'

    def get_year(self, media):
        try:
            data = AgentBase.my_JSON_ObjectFromURL('http://127.0.0.1:32400/library/metadata/%s/children' % media.id)
            # 시즌.
            Log(json.dumps(data, indent=4))
            filename = data['MediaContainer']['Metadata'][0]['Media'][0]['Part'][0]['file']
            ret = os.path.splitext(os.path.basename(filename))[0]
            match = Regex(r'(?P<date>\d{6})').search(ret)
            if match:
                return match.group('date')
        except Exception as e:
            Log.Exception(str(e))

    def search(self, results, media, lang, manual):
        try:
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

            # 2021-12-13 닥터 슬럼프 리메이크 FT105262
            if manual and media.show is not None and media.show.startswith('FT'):
                code = media.show
                meta = MetadataSearchResult(id=code, name=code, year='', score=100, thumb="", lang=lang)
                results.Append(meta)
                return

            if manual and media.show is not None and media.show.startswith('K'):
                # 2022-11-18 KBS 같은 경우
                try:
                    code, title = media.show.split('|')
                    if code != 'KTV':
                        meta = MetadataSearchResult(id=code, name=title, year='', score=100, thumb="", lang=lang)
                        results.Append(meta)
                        return
                except Exception:
                    pass

            # KTV|수당영웅
            Log('SEARCH 0: %s' % media.show)
            if manual and media.show is not None and media.show.startswith('KTV'):
                keyword = media.show.replace('KTV|', '')

            else:
                Log('SEARCH : %s' % media.show)
                keyword = media.show
                Log('>> %s : %s %s' % (self.module_name, keyword, manual))
            Log('KEYWORD : %s', keyword)
            use_json = False
            search_data = None
            search_key = u'search|%s' % keyword
            if self.is_read_json(media) and manual == False:
                info_json = self.get_info_json(media)
                if info_json is not None and search_key in info_json:
                    search_data = info_json[search_key]
                    use_json = True
            if search_data is None:
                search_data = self.send_search(self.module_name, keyword, manual)
                if search_data is not None and self.is_write_json(media):
                    self.save_info(media, {search_key:search_data})
                    #self.append_info(media, search_key, search_data)

            if search_data is None:
                return
            #Log(json.dumps(search_data, indent=4))
            # 2021-07-07
            # 다음 차단-> 차단상태에서 ott search data 저장 -> 점수 미달 -> 새로고침 안됨
            max_score = 0
            daum_max_score = 100
            equal_max_score = 100
            if 'daum' in search_data:
                data = search_data['daum']
                has_multiple_seasons = False
                if getattr(media, 'seasons', None) and len(media.seasons) > 1:
                    for media_season_index in media.seasons:
                        try:
                            if int(media_season_index) > 1:# and int(media_season_index) < 1900:
                                has_multiple_seasons = True
                                break
                        except Exception:
                            pass

                # 미디어도 시즌, 메타도 시즌
                if has_multiple_seasons and len(data['series']) > 1:
                    # 마지막 시즌 ID
                    code = data['series'][-1]['code']
                    msr = MetadataSearchResult(
                        id=code,
                        name=u'%s | 시리즈' % keyword,
                        year=data['series'][-1]['year'],
                        score=100, lang=lang, thumb=data['series'][-1]['thumb'])
                    msr.type = "show"
                    msr.summary = ", ".join(show.get('title') for show in data['series'] if show.get('title'))
                    results.Append(msr)

                # 미디어 단일, 메타 시즌
                elif len(data['series']) > 1:
                    #reversed
                    for index, series in enumerate(reversed(data['series'])):
                        if series['year'] is not None:
                            score = 95-(index*5)
                            if media.year == series['year']:
                                score = 100
                            if score < 20:
                                score = 20
                            if 'status' in series and series['status'] == 0:
                                score = score -40
                            max_score = max(max_score, score)
                            msr = MetadataSearchResult(id=series['code'], name=series['title'], year=series['year'], thumb=series.get('thumb'), score=score, lang=lang)
                            msr.type = 'show'
                            msr.summary = series.get('code') + " "  + series.get('studio') or ''
                            results.Append(msr)
                # 미디어 단일, 메타 단일 or 미디어 시즌, 메타 단일
                else:
                    # 2019-05-23 미리보기 에피들이 많아져서 그냥 방송예정도 선택되게.
                    #if data['status'] != 0:
                    # 2021-06-27 동명 컨텐츠중 년도 매칭되는것을 100으로 주기위해 99로 변경
                    if 'equal_name' in data and len(data['equal_name']) > 0:
                        score = daum_max_score = 99
                        #나의 아저씨 동명 같은 년도
                        if data['year'] == media.year:
                            score = daum_max_score = 100
                            equal_max_score = 99
                    else:
                        score = 100
                    meta = MetadataSearchResult(id=data['code'], name=data['title'], year=data['year'], thumb=data['image_url'], score=score, lang=lang)
                    tmp = data['extra_info'] + ' '
                    if data['status'] == 0:
                        tmp = tmp + u'방송예정'
                    elif data['status'] == 1:
                        tmp = tmp + u'방송중'
                    elif data['status'] == 2:
                        tmp = tmp + u'방송종료'
                    tmp = tmp + self.search_result_line() + data['desc']
                    meta.summary = tmp
                    meta.type = 'movie'
                    max_score = max(max_score, score)
                    results.Append(meta)

                if 'equal_name' in data:
                    for index, program in enumerate(data['equal_name']):
                        if program['year'] == media.year:
                            score = min(equal_max_score, 100 - (index))
                            max_score = max(max_score, score)
                            sr = MetadataSearchResult(id=program['code'], name='%s | %s' % (program['title'], program['studio']), year=program['year'], thumb=program['thumb'], score=score, lang=lang)
                            sr.type = "show"
                            sr.summary = program.get('code') + " " + program.get('studio') or ""
                            results.Append(sr)
                        else:
                            score = min(equal_max_score, 80 - (index*5))
                            max_score = max(max_score, score)
                            sr = MetadataSearchResult(id=program['code'], name='%s | %s' % (program['title'], program['studio']), year=program['year'], thumb=program['thumb'], score=score, lang=lang)
                            sr.type = "show"
                            sr.summary = program.get('code')  + " " + program.get('studio') or ""
                            results.Append(sr)
            def func(show_list):
                for idx, item in enumerate(show_list):
                    score = min(daum_max_score, item['score'])
                    meta = MetadataSearchResult(id=item['code'], name=item['title'], score=score, thumb=item['image_url'], lang=lang)
                    meta.summary = item['site'] + ' ' + item['studio']
                    meta.type = "movie"
                    results.Append(meta)
                    return score
            if 'tving' in search_data:
                score = func(search_data['tving'])
                max_score = max(max_score, score)
            if 'wavve' in search_data:
                score = func(search_data['wavve'])
                max_score = max(max_score, score)
            if 'watcha' in search_data:
                score = func(search_data['watcha'])
                max_score = max(max_score, score)
            if use_json and max_score < 85:
                self.remove_info(media)
                self.search(results, media, lang, manual)

        except Exception as e:
            Log.Exception(str(e))

    def update_info(self, metadata, media, remote_metadata, data_urls, has_multiple_seasons, section_id):
        if media.title:
            metadata.title = media.title.split('|')[0].strip()
        else:
            metadata.title = ''
        if not has_multiple_seasons:
            metadata.title = remote_metadata.get('title') or metadata.title
        metadata.original_title = metadata.title
        metadata.title_sort = unicodedata.normalize('NFKD', metadata.title)
        metadata.studio = remote_metadata.get('studio') or ''
        metadata.content_rating = remote_metadata.get('mpaa') or ''
        metadata.summary = remote_metadata.get('plot') or ''
        try:
            metadata.originally_available_at = Datetime.ParseDate(remote_metadata['premiered']).date()
        except Exception:
            pass

        # 장르
        metadata.genres.clear()
        for tmp in remote_metadata.get('genre') or ():
            metadata.genres.add(tmp)

        # clear logo, slug
        self.plex_exclusive(media.id, section_id)
        self.update_logo(media.id, section_id, remote_metadata.get('thumb') or ())

        # poster
        poster_templates = {
            'poster': metadata.posters,
            'landscape': metadata.art,
            'banner': metadata.banners
        }
        for item in sorted(remote_metadata.get('thumb') or (), key=lambda k: k.get('score') or 0, reverse=True):
            image_url = item.get('value') or item.get('thumb')
            aspect = item.get('aspect') or 'poster'
            container = poster_templates.get(aspect)
            if container is None or not image_url or image_url in data_urls[aspect]:
                continue
            try:
                self.set_http_data(image_url, container, data_urls[aspect], preview=item.get('thumb'))
            except Exception as e:
                Log.Exception(str(e))

        # 부가영상
        self.set_extras(metadata, remote_metadata)

        # rating
        for item in remote_metadata.get('ratings') or ():
            name = item.get('name')
            rating = item.get('value')
            if name == 'tmdb' and rating is not None:
                metadata.rating = rating
                metadata.audience_rating = 0.0

        # role
        metadata.roles.clear()
        self.set_roles(metadata, remote_metadata, role_types=('actor', 'director', 'credits'))

        # 테마
        tvdb_id = self.get_tvdb_id(remote_metadata)
        if tvdb_id:
            Log.Debug("metadata_id='%s' : TVDB_ID='%s'", metadata.id, tvdb_id)
        self.set_themes(metadata, remote_metadata, data_urls['theme'])

    def update_season(self, metadata, remote_metadata, data_urls, media_season_index):
        metadata_season = metadata.seasons[media_season_index]
        season_index = self.convert_season_index(media_season_index)
        Log.Debug("업데이트: %s - 시즌 %s as %s", metadata.title, media_season_index, season_index)
        metadata_season.summary = remote_metadata.get('plot') or ''

        # poster
        ProxyClass = Proxy.Preview
        season_valid_names = set()
        poster_templates = {
            'poster': (metadata.posters, metadata_season.posters),
            'landscape': (metadata.art, metadata_season.art),
            'banner': (metadata.banners, metadata_season.banners)
        }
        for item in sorted(remote_metadata.get('thumb') or (), key=lambda k: k.get('score') or 0, reverse=True):
            image_url = item.get('value') or item.get('thumb')
            aspect = item.get('aspect') or 'poster'
            process = poster_templates.get(aspect)
            """
            2026-03-12 halfaider
            기존의 Info.xml에 있던 url은 metadata.posters 등에 등록되어 에이전트로 넘어옴
            이 dict-like 목록을 갱신해서 데이터를 넣어줘야 함
            url만 넣고 데이터를 넣어주지 않으면 None 으로 저장되는 듯
            예를 들어 Info.xml에 A URL이 있었고 metadata.posters 에 등록되었는데
            새로운 포스터 목록에 A URL이 없으면 다운로드하지 못 한채 None으로 파일이 저장됨
            그래서 validate_keys()로 다운로드하지 못한 url은 삭제해 줘야 함
            validate_keys()는 Preview는 적용 안되고 Media만 적용되는 것으로 보임
            """
            if not process or not image_url:
                continue
            if image_url in data_urls[aspect]:
                continue
            try:
                image_data = HTTP.Request(image_url).content
                if not image_data or len(image_data) < 16:
                    Log.Warn("유효하지 않은 이미지 데이터: %s", image_url)
                    continue
                # sort_order 때문에 검사
                if image_url not in data_urls[aspect]:
                    process[0][image_url] = ProxyClass(image_data, sort_order=len(data_urls[aspect]) + 1)
                    data_urls[aspect].add(image_url)
                # 시즌 번호가 2 이상인 경우 각 시즌에 포스터가 저장되도록
                if image_url not in season_valid_names:
                    process[1][image_url] = ProxyClass(image_data, sort_order=len(season_valid_names) + 1)
                    season_valid_names.add(image_url)
            except Exception as e:
                Log.Exception(str(e))
        """
        2026-03-11 halfaider
        validate_keys()는 보유중인 모든 키가 입력받은 기준 목록에 있는지 검사함
        만약 기준 목록에 없으면 삭제
        for 문 안에서 각 시즌마다 metadata.posters.validate_keys()를 하면 마지막 시즌에서 작업한 포스터만 남으니 주의
        """
        metadata_season.posters.validate_keys(season_valid_names)
        metadata_season.art.validate_keys(season_valid_names)
        metadata_season.banners.validate_keys(season_valid_names)

        # 부가영상
        self.set_extras(metadata, remote_metadata)

        # role
        #self.set_roles(metadata, remote_metadata)

        # 테마
        tvdb_id = self.get_tvdb_id(remote_metadata)
        if tvdb_id:
            Log.Debug("metadata_id='%s' : TVDB_ID='%s'", metadata.id, tvdb_id)
        self.set_themes(metadata, remote_metadata, data_urls['theme'], tvdb_id)

    def get_tvdb_id(self, remote_metadata):
        tvdb_id = None
        # Get the TVDB id from the Movie Database Agent
        tmdb_id = (remote_metadata.get('extra_info') or {}).get('tmdb_id')
        if tmdb_id:
            tvdb_id = Core.messaging.call_external_function(
                'com.plexapp.agents.themoviedb',
                'MessageKit:GetTvdbId',
                kwargs = {"tmdb_id": tmdb_id}
            )
        return tvdb_id

    def update_episode(self, show_epi_info, episode, info_json, is_write_json, meta_code, frequency=None):
        site_orders = ['daum', 'tving', 'wavve', 'tmdb']
        if isinstance(meta_code, str) and len(meta_code) > 1:
            if meta_code[1] == "W":
                site_orders.sort(key=lambda x: x != "wavve")
            elif meta_code[1] == "V":
                site_orders.sort(key=lambda x: x != "tving")
            elif meta_code[1] == "T":
                site_orders.sort(key=lambda x: x != "tmdb")

        def get_daum_episode_info(code, info_json, is_write_json, module_name, send_episode_info_func):
            if not code:
                return None
            if info_json and code in info_json:
                daum_episode_info = info_json[code]
            else:
                daum_episode_info = send_episode_info_func(module_name, code)
                if daum_episode_info and is_write_json:
                    info_json[code] = daum_episode_info
            return daum_episode_info

        def set_episode_thumb(thumb_url, episode, valid_thumb_names, preview=None):
            if not thumb_url or thumb_url in valid_thumb_names:
                return
            self.set_http_data(thumb_url, episode.thumbs, valid_thumb_names, preview=preview)

        valid_thumb_names = set()
        daum_episode_info = None
        daum_code = (show_epi_info.get('daum') or {}).get('code') or ''
        for site in site_orders:
            try:
                if site not in show_epi_info:
                    continue
                if site == 'daum':
                    daum_episode_info = daum_episode_info or get_daum_episode_info(daum_code, info_json, is_write_json, self.module_name, self.send_episode_info)
                    if not daum_episode_info:
                        continue
                    for thumb in sorted(daum_episode_info['thumb'], key=lambda k: k.get('score') or 0, reverse=True):
                        set_episode_thumb(thumb.get('value') or thumb.get('thumb'), episode, valid_thumb_names, thumb.get('thumb'))
                else:
                    set_episode_thumb(show_epi_info[site].get('value') or show_epi_info[site].get('thumb'), episode, valid_thumb_names, show_epi_info[site].get('thumb'))
            except Exception:
                Log.Exception('')
            if valid_thumb_names:
                break
        episode.thumbs.validate_keys(valid_thumb_names)

        for site in site_orders:
            try:
                if site not in show_epi_info:
                    continue
                if site == 'daum':
                    daum_episode_info = daum_episode_info or get_daum_episode_info(daum_code, info_json, is_write_json, self.module_name, self.send_episode_info)
                    if not daum_episode_info:
                        continue
                    epi_info = daum_episode_info
                    if not episode.title and epi_info.get('title'):
                        episode.title = epi_info['title']
                else:
                    epi_info = show_epi_info[site]
                    if not episode.title and epi_info.get('title'):
                        episode.title = epi_info['title'] or epi_info.get('premiered') or ''
                        if frequency and episode.title:
                            episode.title = u'%s회 (%s)' % (frequency, episode.title)
                parsed_date = Datetime.ParseDate(epi_info.get('premiered') or '')
                if parsed_date:
                    episode.originally_available_at = parsed_date.date()
                if not episode.summary and epi_info.get('plot'):
                    episode.summary = epi_info['plot']
                for guest in (epi_info.get('extra_info') or {}).get('guests') or ():
                    name = guest.get('name') or ''
                    if name:
                        # 디렉터, 작가는 표시되는데 게스트는 표시 안 됨
                        guest_star = episode.guest_stars.new()
                        guest_star.name = name
                        guest_star.photo = guest.get('image') or ''
                        guest_star.role = '본인'
            except Exception:
                Log.Exception('')
            if episode.originally_available_at and episode.title and episode.summary:
                break

        daum_episode_info = daum_episode_info or get_daum_episode_info(daum_code, info_json, is_write_json, self.module_name, self.send_episode_info)
        if daum_episode_info:
            for item in daum_episode_info.get('extras') or ():
                try:
                    url = 'sjva://sjva.me/playvideo/%s|%s' % (item['mode'], item['content_url'])
                    episode.extras.add(self.extra_map[item['content_type'].lower()](url=url, title=self.change_html(item['title']), originally_available_at=Datetime.ParseDate(item['premiered']).date(), thumb=item['thumb']))
                except Exception:
                    Log.Exception('')

    def update(self, metadata, media, lang):
        # 시즌이 2개 이상이고 시즌 번호가 1, 0만 있는지 검사
        has_multiple_seasons = False
        if getattr(media, 'seasons', None) and len(media.seasons) > 1:
            for index_ in media.seasons:
                try:
                    if int(index_) > 1:
                        has_multiple_seasons = True
                        break
                except Exception:
                    pass

        search_key = u'search|%s' % media.title
        search_data = None
        info_json = {}
        is_write_json = self.is_write_json(media)
        if self.is_read_json(media):
            tmp = self.get_info_json(media)
            # info.json에 지난 검색결과가 있으면 사용
            if tmp and search_key in tmp:
                search_data = tmp[search_key]
                info_json = tmp
        # info.json에 검색결과가 없으면 검색 후 저장
        search_data = search_data or self.send_search(self.module_name, media.title, False)
        if search_data or is_write_json:
            info_json[search_key] = search_data

        module_prefs = self.get_module_prefs(self.module_name)
        try:
            seasons_to_update = JSON.ObjectFromString(Prefs['seasons_to_update']) or {}
        except Exception:
            seasons_to_update = {}
        Log("[%s] seasons to update: %s", media.id, seasons_to_update)

        # 사용할 메타데이터 인포
        search_code = metadata.id
        search_title = media.title.replace(u'[종영]', '')
        search_title = search_title.split('|')[0].strip()
        main_meta_info = self.get_data_from_info_json(search_code, search_title, info_json, is_write_json)
        Log.Debug("[%s] metadata code: %s", media.id, main_meta_info.get('code'))
        Log.Debug("[%s] metadata title: %s", media.id, main_meta_info.get('title'))
        Log.Debug("[%s] metadata summary: %s", media.id, main_meta_info.get('plot'))
        Log.Debug("[%s] metadata season: %s", media.id, main_meta_info.get('season'))

        """
        2026-03-17 halfaider
        메타데이터 새로고침의 대상은 TV show 혹은 Episode
        TV show:
            metadata.id: KD51256 TV 쇼의 메타데이터 ID
            metadata.guid: com.plexapp.agents.sjva_agent://KD51256?lang=ko
            media.guid: com.plexapp.agents.sjva_agent://KD51256?lang=ko
            media.id: TV쇼의 DB id
            media.seasons: TV 쇼의 모든 즌 {'200801': <Framework.api.agentkit.MediaTree object at 0xf303eb065bd0>, ...}
        에피소드:
            metadata.id: KD51256 TV 쇼의 메타데이터 ID
            metadata.guid: com.plexapp.agents.sjva_agent://KD51256/200801/172?lang=ko
            media.guid: com.plexapp.agents.sjva_agent://KD51256?lang=ko
            media.id: 에피소드의 DB id
            media.seasons: 에피소드의 부모 시즌 {'200801': <Framework.api.agentkit.MediaTree object at 0xf303eb065bd0>}
        """
        guid_parts = self.parse_guid(metadata.guid)
        if guid_parts.get('is_episode'):
            Log.Debug("[%s] Update episode: %s", media.id, guid_parts.get('episode'))
            Log.Debug("[%s] 에피소드만 메타데이터 새로고침하면 에피소드 전용 번들 폴더에 저장됨", media.id)
            metadata_episode = metadata.seasons[guid_parts.get('season')].episodes[guid_parts.get('episode')]
            media_episode = media.seasons[guid_parts.get('season')].episodes[guid_parts.get('episode')]
            #self.reset_episode_metadata(metadata_episode)
            #metadata_episode.title = "테스트"
            return

        # 미디어 초기화용 목록
        data_urls = {
            'poster': set(),
            'landscape': set(),
            'banner': set(),
            'theme': set()
        }

        section_id = self.get_section_id(media.id)

        # 메타데이터 초기화
        try:
            self.update_info(metadata, media, main_meta_info, data_urls, has_multiple_seasons, section_id)
        except Exception:
            Log.Exception("기본 정보 업데이트 실패")

        series_data = (search_data.get('daum') or {}).get('series') or ()

        @parallelize
        def UpdateSeasons():
            index_list = sorted(media.seasons.keys(), key=get_sort_key)
            Log.Debug('[%s] Season indexes: %s', media.id, index_list)

            main_meta_info_episodes_by_date = {}
            for media_season_index in index_list:
                try:
                    """
                    2026-03-17 halfaider
                    사용자 설정값에서 지정한 시즌만 업데이트
                    """
                    if media.id in seasons_to_update and int(media_season_index) not in (seasons_to_update.get(media.id) or ()):
                        Log.Info("[%s] 업데이트 건너뛰기: %s", media.id, media_season_index)
                        continue

                    season_media = media.seasons[media_season_index]
                    try:
                        sample_season_path = season_media.all_parts()[0].file
                    except Exception:
                        sample_season_path = ''
                    Log.Debug("[%s] sample_season_path: %s", media.id, sample_season_path)
                    # 2022-04-05
                    search_media_season_index = self.convert_season_index(media_season_index)
                    if search_media_season_index in ['0', '00']:
                        continue

                    search_title = media.title.replace(u'[종영]', '')
                    search_title = search_title.split('|')[0].strip()
                    # 신과함께3 단일 미디어파일이면 search_media_season_index 1이여서 시즌1이 매칭됨.
                    # 단일 미디어 파일에서는 사용하지 않도록함.
                    # 어짜피 여러 시즌버전을 넣는다면 신과함꼐3도 시즌3으로 바꾸어야함.
                    search_code = metadata.id
                    only_season_title_show = False
                    if has_multiple_seasons and series_data:
                        try: #사당보다 먼 의정부보다 가까운 3
                            Log.Debug("[%s] search_series_size: %s", media.id, len(series_data))
                            search_title = series_data[int(search_media_season_index)-1]['title']
                            search_code = series_data[int(search_media_season_index)-1]['code']
                        except Exception:
                            only_season_title_show = True
                    if has_multiple_seasons and sample_season_path:
                        try:
                            """
                            2026-03-16 halfaider
                            만약 시즌 경로명에 {daum-12345} 다음 id 정보가 있으면 매칭
                            """
                            match = Regex(r'\{daum-(?P<daum_id>\d+)\}').search(sample_season_path)
                            if match:
                                daum_id = match.group('daum_id')
                                Log.Debug("[%s] Search series Daum id: %s", media.id, daum_id)
                                search_code = "KD" + daum_id
                                only_season_title_show = False
                        except Exception:
                            Log.Exception('')

                    Log.Debug('[%s] has_multiple_seasons: %s', media.id, has_multiple_seasons)
                    Log.Debug('[%s] search_title: %s', media.id, search_title)
                    Log.Debug('[%s] search_code: %s', media.id, search_code)
                    Log.Debug('[%s] media_season_index: %s', media.id, media_season_index)
                    Log.Debug('[%s] search_media_season_index: %s', media.id, search_media_season_index)
                    Log.Debug('[%s] only_season_title_show: %s', media.id, only_season_title_show)

                    if not only_season_title_show:
                        if search_code == main_meta_info.get('code'):
                            meta_info = main_meta_info
                        else:
                            meta_info = self.get_data_from_info_json(search_code, search_title, info_json, is_write_json)

                        Log.Debug("[%s] TITLE: %s", media.id, meta_info.get('title'))
                        Log.Debug("[%s] SUMMARY: %s", media.id, meta_info.get('plot'))
                        Log.Debug("[%s] METAINFO_CODE: %s", media.id, meta_info.get('code'))
                        Log.Debug("[%s] METAINFO_SEASON: %s", media.id, meta_info.get('season'))

                        if not has_multiple_seasons and meta_info.get('status') == 2 and module_prefs.get('end_noti_filepath'):
                            end_noti_filepath = (module_prefs.get('end_noti_filepath') or '').split('|')
                            for tmp in end_noti_filepath:
                                if tmp and (tmp in sample_season_path):
                                    metadata.title = u'[종영]%s' % metadata.title
                                    break

                        metadata_season = metadata.seasons[media_season_index]
                        """
                        2026-03-19 halfaider
                        모든 시즌 포스터에 1시즌의 포스터가 중복 저장되어 있을 경우 초기화
                        """
                        metadata_season.posters.validate_keys([])
                        metadata_season.art.validate_keys([])
                        metadata_season.banners.validate_keys([])

                        if meta_info.get('code') != main_meta_info.get('code'):
                            # Daum 시리즈로 매칭 시 각 시즌의 정보를 적용
                            @task
                            def UpdateSeason(metadata=metadata, meta_info=meta_info, data_urls=data_urls, media_season_index=media_season_index):
                                self.update_season(metadata, meta_info, data_urls, media_season_index)

                        # 에피소드 업데이트
                        meta_info_episodes = (meta_info.get('extra_info') or {}).get('episodes') or {}
                        media_episodes = media.seasons[media_season_index].episodes
                        metadata_episodes = metadata.seasons[media_season_index].episodes
                        """
                        2026-03-23 halfaider
                        각 시즌별로 날짜별 에피소드 색인
                        """
                        if meta_info.get('code') != main_meta_info.get('code'):
                            meta_info_episodes_by_date = {}
                        else:
                            meta_info_episodes_by_date = main_meta_info_episodes_by_date
                        if not meta_info_episodes_by_date:
                            for key, value in meta_info_episodes.items():
                                for site in ('daum', 'tving', 'wavve'):
                                    site_data = value.get(site)
                                    if site_data:
                                        premiered = site_data.get('premiered')
                                        if isinstance(premiered, str) and premiered[0].isdigit():
                                            meta_info_episodes_by_date[premiered] = (key, value)

                        count_metadata = len(metadata_episodes)
                        count_media = len(media_episodes)
                        count_api = len(meta_info_episodes)
                        Log.Debug("[%s] Episode count: API=%s Metadata=%s Media=%s Missing=%s", media.id, count_api, count_metadata, count_media, count_api - max(count_metadata, count_media))

                        for media_episode_index in media_episodes:
                            media_episode = media_episodes[media_episode_index]
                            metadata_episode = metadata_episodes[media_episode_index]
                            @task
                            def UpdateEpisode(media_episode=media_episode, metadata_episode=metadata_episode, media_episode_index=media_episode_index, media=media, meta_info_episodes=meta_info_episodes, info_json=info_json, is_write_json=is_write_json, meta_code=meta_info.get('code') or metadata.id, meta_info_episodes_by_date=meta_info_episodes_by_date):
                                originally_available_at = metadata_episode.originally_available_at or ''
                                # 에피소드 정보 초기화
                                self.reset_episode_metadata(metadata_episode)
                                meta_info_episode = meta_info_episodes.get(media_episode_index) or {}
                                if meta_info_episode and media_episode_index.isdigit():
                                    self.update_episode(meta_info_episode, metadata_episode, info_json, is_write_json, meta_code)
                                else:
                                    # 에피 번호로 검색이 안 되면 날짜로 매칭 시도
                                    path_date = ""
                                    try:
                                        episode_path = media_episode.all_parts()[0].file
                                        match = Regex(r'\.(?P<date>\d{6})\.').search(episode_path)
                                        if match:
                                            six = match.group('date')
                                            year = six[:2]
                                            if int(year) > 50:
                                                year = '19' + year
                                            else:
                                                year = '20' + year
                                            path_date = year + '-' + six[2:4] + '-' + six[4:]
                                    except Exception:
                                        Log.Exception('')
                                    date_texts = []
                                    for date_text in (path_date, originally_available_at, media_episode_index):
                                        if isinstance(date_text, str) and len(date_text) > 5:
                                            date_texts.append(date_text)
                                    #Log.Debug("[%s] candidates for matching date: %s", media.id, date_texts)
                                    for text in date_texts:
                                        match = Regex(r'(\d{4}-\d{2}-\d{2})').search(text)
                                        if match:
                                            media_premiered = match.group(1)
                                            if media_premiered in meta_info_episodes_by_date:
                                                epi_index, epi_value = meta_info_episodes_by_date[media_premiered]
                                                Log.Debug("[%s] '%s' match with '%s'", media.id, media_premiered, epi_index)
                                                self.update_episode(epi_value, metadata_episode, info_json, is_write_json, meta_code, frequency=epi_index)
                                                break
                                    else:
                                        Log.Debug("[%s] No episode info. found: %s", media.id, media_episode_index)
                                    #Log.Debug("[%s] episode %s: %s", media.id, media_episode_index, metadata_episode.title)

                    # 시즌 title, summary
                    if is_write_json and only_season_title_show == False:
                        self.save_info(media, info_json)

                    # 2021-09-15 주석처리함. 임의의 시즌으로 분할하는 경우를 고려
                    #if not has_multiple_seasons:
                    #    return

                    token = self.get_token()
                    for media_season_index in media.seasons:
                        Log.Debug('[%s] media_season_index: %s', media.id, media_season_index)
                        if media_season_index == '0':
                            continue
                        try:
                            filepath = media.seasons[media_season_index].all_parts()[0].file
                            tmp = os.path.basename(os.path.dirname(filepath))
                            season_title = None
                            if tmp != metadata.title:
                                Log.Debug("[%s] season path title: %s", media.id, tmp)
                                match = Regex(r'(?P<season_num>\d{1,8})\s*(?P<season_title>.*?)(?:\s(?P<meta_id>\{.*?\}))?$').search(tmp)
                                Log.Debug('[%s] MATCH: %s', media.id, match.groups())
                                if match and (tmp.startswith(u'시즌 ') or tmp.startswith(u'Season ')):
                                    Log.Debug('[%s] media_season_index: %s', media.id, media_season_index)
                                    Log.Debug('[%s] FORCE season_num: %s', media.id, match.group('season_num'))
                                    Log.Debug('[%s] FORCE season_title: %s', media.id, match.group('season_title'))
                                    if int(match.group('season_num')) == int(media_season_index) and match.group('season_title'):
                                        season_title = match.group('season_title')
                            metadata_season = metadata.seasons[media_season_index]
                            Log.Debug("[%s] final season title: %s", media.id, season_title)
                            Log.Debug("[%s] final season summary: %s", media.id, metadata_season.summary)
                            url = 'http://127.0.0.1:32400/library/sections/%s/all?type=3&id=%s&X-Plex-Token=%s' % (section_id, media.seasons[media_season_index].id, token)
                            if season_title:
                                url = url + "&title.value=%s" % String.Quote(season_title.encode('utf8'))
                            if metadata_season.summary:
                                url = url + "&summary.value=%s" % String.Quote(metadata_season.summary.encode('utf8'))
                            if season_title or metadata_season.summary:
                                request = PutRequest(url)
                                response = urllib2.urlopen(request)
                                status_code = response.getcode()
                                if not status_code == 200:
                                    Log("[%s] 시즌 정보 업데이트 실패: status %s", media.id, status_code)
                        except Exception as e:
                            Log.Exception(str(e))
                except Exception:
                    Log.Exception("[%s] 시즌 업데이트 실패: %s", media.id, media_season_index)

        """
        2026-03-12 halfaider
        이걸 해줘야 고아 파일이 안 생김
        """
        for data_type, urls in data_urls.items():
            if data_type == 'poster':
                bucket = metadata.posters
            elif data_type == 'landscape':
                bucket = metadata.art
            elif data_type == 'banner':
                bucket = metadata.banners
            elif data_type == 'theme':
                bucket = metadata.themes
            else:
                continue
            bucket.validate_keys(urls)

    def get_data_from_info_json(self, search_code, search_title, info_json = None, is_write_json = False):
        meta_info = {}
        if info_json and search_code in info_json:
            # 방송중이라면 저장된 정보를 무시해야 새로운 에피를 갱신
            if info_json[search_code]['status'] == 2:
                meta_info = info_json[search_code]
        if not meta_info:
            if search_code.startswith('FT'):
                module_name = 'ftv'
            else:
                module_name = self.module_name
            meta_info = self.send_info(module_name, search_code, title=search_title)
            if meta_info and is_write_json:
                info_json[search_code] = meta_info
        return meta_info
