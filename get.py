import requests

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

headers = {'user-agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36 Edg/91.0.864.59'}

class GetError(Exception):
    class PaidError(Exception):
        pass
    
    class GetError(Exception):
        pass

class Kuwo:    
    @staticmethod
    def search_kuwo(kw: str):
        '''搜索'''
        
        search_params.update({'key': kw})

        try:
            response = requests.get(search_url,
                                    params=search_params,
                                    headers={**headers, **search_headers},
                                    timeout=5,
                                   ).json()
        except:
            raise GetError.GetError('获取出错，请重试。')

        datas = response.get('data', {}).get('list', {})

        result = [[r.get('name', ''),
                   r.get('artist', ''),
                   r.get('album', ''),
                   r.get('songTimeMinutes', ''),
                   r.get('pic', ''),
                   r.get('pic120', ''),
                   r.get('rid', '')]
                  for r in datas]

        return result

    @staticmethod
    def get_music_content(rid):
        '''获取歌曲'''
        
        from_params['mid'] = rid

        try:
            data = requests.get(from_url, params=from_params, headers=headers, timeout=5).json() 
        except:
            raise GetError.GetError('获取出错，请重试。')
        
        if data['success']:
            url = data['data']['url']
        elif '付费' in data['msg']:
            raise GetError.PaidError('付费歌曲。')
        else:
            raise GetError.GetError('获取歌曲出错，请重新尝试。')

        try:
            content = requests.get(url, headers=headers, timeout=5).content
        except:
            raise GetError.GetError('获取出错，请重试。')

        return content

    @staticmethod
    def get_music_lrc(rid):
        '''获取歌词'''    
            
        default_lrc = [{'word': '无歌词', 'time': '0'}]
        lrc_params.update({'musicId': rid})

        try:
            lrc_data = requests.get(lrc_url, params=lrc_params, headers=headers, timeout=5).json()
        except:
            raise GetError.GetError('获取出错，请重试。')
        
        lrc_list = lrc_data.get('data', {})
        if lrc_list is None:
            lrc_list = {}
        
        lrc_list = lrc_list.get('lrclist', default_lrc)
        lrc = [list(l.values()) for l in lrc_list]

        return lrc

    @staticmethod
    def get_pic(url):
        '''获取图片'''

        try:
            pic = requests.get(url, headers=headers).content
        except:
            raise GetError.GetError('获取出错，请重试。')
        
        return pic
    
    @staticmethod
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
        
        return result
