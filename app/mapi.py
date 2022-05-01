import requests
from re import match, findall
from json import loads

def error_getter(func):
    def function(*arg, **args):
        for i in range(3):
            result = None
            try:
                result = func(*arg, **args)
            except GetError.PaidError:
                raise GetError.PaidError('PaidError')
            except:
                continue
            else:
                break
                
        if not result:
            raise GetError.GetError('GetError')

        return result

    return function

class GetError(Exception):
    class PaidError(Exception):
        pass
    
    class GetError(Exception):
        pass

class Base:
    headers = {'user-agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36 Edg/91.0.864.59'}

    def search(kw):  
        return [['', # 歌名
                 '', # 歌手名
                 '', # 专辑名
                 '', # 时长
                 '', # 图片1
                 '', # 图片2
                 ''  # 歌曲唯一标识，格式：'引擎:信息'，如酷我：'kuwo:12345678'
                 ]]

    def get_music_lrc(data):
        return [['无歌词', 0]] # [[歌词, 毫秒], ...]

class EngineKuwo(Base):
    name = '酷我音乐'
    pre = 'kuwo'

    search_url = 'http://www.kuwo.cn/api/www/search/searchMusicBykeyWord'
    search_params = {
        'key': 'str',   # 查找关键字
        'pn': '1',  # 页数
        'rn': '20', # 项数
        'httpsStatus': '1',
        'reqId': '6e028fc0-db8f-11eb-b6f5-ff7d54a57f2b'
    }
    search_headers = {
        'Referer': 'http://www.kuwo.cn/search/list?key=',
        'Cookie': '_ga=GA1.2.1165960666.1627019800; Hm_lvt_cdb524f42f0ce19b169a8071123a4797=1628332286,1628477107,1629264430,1629644110; Hm_lpvt_cdb524f42f0ce19b169a8071123a4797=1629644110; _gid=GA1.2.1066572338.1629644110; kw_token=I12NX0YH48',
        'csrf': 'I12NX0YH48',
    }

    from_url = 'http://www.kuwo.cn/api/v1/www/music/playUrl'  
    from_params = {
        'mid': 'id', # 歌曲 id
        'type': 'music',
        'httpsStatus': '1',
        'reqId': '4487eb50-3e8a-11ec-9946-6f9a32ec6994'
    }

    lrc_params = {
        'musicId': 'rid'
    }
    lrc_url = 'http://m.kuwo.cn/newh5/singles/songinfoandlrc'

    rank_url = 'http://www.kuwo.cn/api/www/bang/bang/musicList'
    rank_id = {
        'soaring': '93',
        'new': '17',
        'hot': '16',
        'douyin': '158'
    }
    rank_params = {
        'bangId': 'id',# 榜 ID
        'pn': '1',# 页数
        'rn': '30',# 项数
        'httpsStatus': '1',
        'reqId': '2f504510-54bb-11ec-8e5d-ed38ea716540'
    }
    rank_headers = {
        'Cookie': '_ga=GA1.2.1165960666.1627019800; Hm_lvt_cdb524f42f0ce19b169a8071123a4797=1628332286,1628477107,1629264430,1629644110; Hm_lpvt_cdb524f42f0ce19b169a8071123a4797=1629644110; _gid=GA1.2.1066572338.1629644110; kw_token=I12NX0YH48',
        'csrf': 'I12NX0YH48',
        }

    @staticmethod
    @error_getter
    def search(kw: str):
        '''搜索'''
        
        params = EngineKuwo.search_params
        params['key'] = kw
        url = EngineKuwo.search_url
        headers = {**EngineKuwo.headers, **EngineKuwo.search_headers}
        
        response = requests.get(url, params=params, headers=headers, timeout=5).json()
        datas = response['data']['list']

        if not datas:
            raise GetError.GetError('获取出错，请重试。')

        pre = EngineKuwo.pre + ':'

        result = [[r.get('name', ''),
                   r.get('artist', ''),
                   r.get('album', ''),
                   r.get('songTimeMinutes', ''),
                   pre + r.get('pic', ''),
                   pre + r.get('pic120', ''),
                   pre + str(r.get('rid', ''))]
                  for r in datas]

        return result

    @staticmethod
    @error_getter
    def get_music_url(rid):
        '''获取歌曲 URL''' 
        
        from_url = EngineKuwo.from_url

        from_params = EngineKuwo.from_params
        from_params['mid'] = rid

        headers = EngineKuwo.headers

        data = requests.get(from_url, params=from_params, headers=headers, timeout=5).json() 
        
        if data['success']:
            url = data['data']['url']
        elif '付费' in data['msg']:
            raise GetError.PaidError('PaidError')

        return url

    @staticmethod
    @error_getter
    def get_music_content(url):
        '''获取歌曲内容'''

        headers = EngineKuwo.headers

        content = requests.get(url, headers=headers, timeout=5).content

        return content

    @staticmethod
    @error_getter
    def get_music_lrc(rid):
        '''获取歌词'''    
            
        default_lrc = [['无歌词', 0]]
        
        lrc_url = EngineKuwo.lrc_url
        
        lrc_params = EngineKuwo.lrc_params
        lrc_params.update({'musicId': rid})
        
        headers = EngineKuwo.headers

        lrc_data = requests.get(lrc_url, params=lrc_params, headers=headers, timeout=5).json()            
        lrc_list = lrc_data['data']['lrclist']

        if not lrc_list:
            return default_lrc

        result = []
        for lrc in lrc_list:
            result.append([lrc['lineLyric'], str_to_msec(lrc['time'])]) # [['歌词', '时间']]

        return result

    @staticmethod
    @error_getter
    def get_pic(url):
        '''获取图片'''

        headers = EngineKuwo.headers

        pic = requests.get(url, headers=headers).content
        #raise GetError.GetError('获取出错，请重试。')
        
        return pic
    
    '''@staticmethod
    def get_rank(bang_id):
        rank_params['bangId'] = rank_id[bang_id]

        try:
            rank = requests.get(rank_url, 
                                params=rank_params, 
                                headers={**headers, **rank_headers}
                                ).json()
        except:
            raise GetError.GetError('获取出错，请重试。')
        
        if rank['msg'] != 'success':
            raise GetError.GetError('获取排行榜出错，请重新尝试。')
        
        result = [[r.get('name', ''),
                   r.get('artist', ''),
                   r.get('album', ''),
                   r.get('songTimeMinutes', ''),
                   r.get('pic', ''),
                   r.get('pic120', ''),
                   r.get('rid', '')]
                  for r in rank['data']['musicList']]
        
        return result'''

class EngineKugou:
    name = '酷狗音乐'
    pre = 'kugou'
    '''
    search_url = 'https://complexsearch.kugou.com/v2/search/song'
    search_params = {
        'callback': 'callback123',
        'keyword': '',
        'page': 1,
        'pagesize': 30,
        'bitrate': 0,
        'isfuzzy': 0,
        'tag': 'em',
        'inputtype': 0,
        'platform': 'WebFilter',
        'userid': 0,
        'clientver': 2000,
        'iscorrection': 1,
        'privilege_filter': 0,
        'token': '',
        'srcappid': '2919',
        'clienttime': '1643027335259',
        'mid': '1643027335259',
        'uuid': '1643027335259',
        'dfid': '-',
        'signature': 'E998FD50C73E8A1F449F6888C8965DD6'
    }
    '''
    search_url = 'https://songsearch.kugou.com/song_search_v2?callback=jQuery11240251602301830425_1548735800928&keyword={}&page=1&pagesize=20&userid=-1&clientver=&platform=WebFilter&tag=em&filter=2&iscorrection=1&privilege_filter=0&_=1548735800930'

    from_url = 'https://wwwapi.kugou.com/yy/index.php'
    from_params = {
        'r': 'play/getdata',
        'callback': 'jQuery19109980750651170855_1643020128428',
        'hash': '',
        'dfid': '4XT5qJ40Ei4A3sJkO74EjGLh',
        'appid': 1014,
        'mid': '2ed42e297130a873c2c80493261494e4',
        'platid': 4,
        'album_id': 0,
        '_': 1643020128429
    }

    @staticmethod
    @error_getter
    def search(kw: str):
        url = EngineKugou.search_url
        # params = EngineKugou.search_params
        # params['keyword'] = kw
        url = url.format(kw)

        response = requests.get(url).text
        
        json = loads(match('.*?({.*})', response).group(1))
        datas = json['data']['lists']

        pre = EngineKugou.pre + ':'
            
        result = [[data['SongName'].replace('<em>', '').replace('</em>', ''),
                   data['SingerName'].replace('<em>', '').replace('</em>', ''),
                   data['AlbumName'].replace('<em>', '').replace('</em>', ''),
                   sec_to_str(data['Duration']),
                   *[pre + data['FileHash'] + ',' + data['AlbumID']] * 3]
                  for data in datas]

        return result

    @staticmethod
    @error_getter
    def get_music_url(sign):
        datas = EngineKugou.get_music_data(sign)
        music_url = datas['play_url']

        content = requests.get(music_url, timeout=1).content

        file = f'datas/cache/kugou-{sign}.mp3'

        with open(file, 'wb') as f:
            f.write(content)

        return file

    @staticmethod
    @error_getter
    def get_pic(sign):
        datas = EngineKugou.get_music_data(sign)
        pic_url = datas['img']

        pic_content = requests.get(pic_url, timeout=1).content

        return pic_content

    @staticmethod
    @error_getter
    def get_music_content(url):
        with open(url, 'rb') as f:
            content = f.read()

        return content

    @staticmethod
    @error_getter
    def get_music_lrc(sign):
        datas = EngineKugou.get_music_data(sign)
        lrc_str = datas['lyrics'].replace('\r', '')

        return format_lrc(lrc_str)

    @staticmethod
    def get_music_data(sign):
        #data = sign.split(':')[1]
        hash_, album_id = sign.split(',')

        from_url = EngineKugou.from_url
        from_params = EngineKugou.from_params
        from_params.update({'hash': hash_, 'album_id': album_id})

        response = requests.get(from_url, params=from_params).text
        json = loads(match('.*?({.*})', response).group(1))
        datas = json['data']

        return datas

class EngineCloud(Base):
    name = '网易云音乐'
    pre = 'cloud'

    url = 'http://www.lxytv.top/api.php?callback=jQuery1113020694660004537435_1646205326739'
    search_datas = {
        'types': 'search',
        'count': 20,
        'source': 'netease',
        'pages': 1,
        'name': ''
    }

    from_datas = {
        'types': 'url',
        'id': '',
        'source': 'netease'
    }

    pic_datas = {
        'types': 'pic',
        'id': '',
        'source': 'netease'
    }

    content_datas = {
        'types': 'url',
        'id': '',
        'source': 'netease'
    }

    lrc_datas = {
        'types': 'lyric',
        'id': '',
        'source': 'netease'
    }

    headers = {
        'Accept': '*/*',
        'Accept-Encoding': 'identity;q=1, *;q=0',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
        'Connection': 'keep-alive',
        'Host': 'm8.music.126.net',
        'Range': 'bytes=0-',
        'Referer': 'http://www.lxytv.top/',
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36 Edg/98.0.1108.62'
    }

    @staticmethod
    @error_getter
    def search(kw: str):
        url = EngineCloud.url
        datas = EngineCloud.search_datas
        datas['name'] = kw

        response = requests.post(url, data=datas).text
        datas = loads(match('.*?\((\[.*\])\)', response).group(1))

        pre = EngineCloud.pre + ':'

        result = [[data['name'],
                   ' '.join(data['artist']),
                   data['album'],
                   '',
                   pre + data['pic_id'],
                   pre + data['pic_id'],
                   pre + str(data['id'])]
                  for data in datas]

        return result

    @staticmethod
    @error_getter
    def get_music_url(id):
        url = EngineCloud.url
        datas = EngineCloud.from_datas
        datas['id'] = id

        response = requests.post(url, data=datas).text
        datas = loads(match('.*?\((.*)\)', response).group(1))

        content_url = datas['url']

        content = requests.get(content_url, timeout=1).content

        file = f'datas/cache/cloud-{id}.mp3'

        with open(file, 'wb') as f:
            f.write(content)

        return file

    @staticmethod
    @error_getter
    def get_pic(id):
        url = EngineCloud.url
        datas = EngineCloud.pic_datas
        datas['id'] = id

        response = requests.post(url, data=datas, timeout=1).text
        datas = loads(match('.*?\((.*)\)', response).group(1))

        pic_url = datas['url']

        pic_content = requests.get(pic_url, timeout=1).content

        return pic_content

    @staticmethod
    @error_getter
    def get_music_content(url):
        with open(url, 'rb') as f:
            content = f.read()

        return content

    @staticmethod
    @error_getter
    def get_music_lrc(id):
        url = EngineCloud.url
        datas = EngineCloud.lrc_datas
        datas['id'] = id

        response = requests.post(url, data=datas).text
        datas = loads(match('.*?\((.*)\)', response).group(1))

        lrcs = datas['lyric']

        result = format_lrc(lrcs)

        return result

def sec_to_str(sec):
    minute = sec // 60
    second = sec % 60

    return '{:0>2,d}:{:0>2,d}'.format(minute, second)

def str_to_msec(string):
    strs = string.split(':')[::-1]
    result = [float('.'.join(r.split('.')[:2])) * (60 ** i) for i, r in enumerate(strs)]

    return sum(result) * 1000

def format_lrc(lrc_str: str):
    lrc_strs = list(zip(*findall('((\[[.:\d]+\])+[^\[\]]+)', lrc_str)))[0]
    result = []

    for lrc_str in lrc_strs:
        lrc_str = lrc_str.replace('[', '').replace('\n', '')
        *times, word = lrc_str.split(']')

        for time in times:
            result.append([word, str_to_msec(time)])

    return sorted(result, key=lambda x: x[1])

# 调试用
if __name__ == '__main__':
    datas = EngineCloud.search('孤勇者')[0][6].split(':')[1]
    print(datas)
    content = EngineCloud.get_music_url(datas)
    print(content)