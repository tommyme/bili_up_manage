from bilibili_api import user
from bilibili_api.utils.network import request
from functools import partial
import requests as r
API = {
    "ploymer": "https://api.bilibili.com/x/polymer/web-dynamic/v1/feed/all"
}

class EnhancedUser(user.User):
    def __init__(self, uid: int, credential: user.Credential = None):
        super().__init__(uid, credential)
        self.fetcher = partial(request, method="GET", credential=self.credential)
        self.sync_fetcher = self.sync_request
        
    
    def sync_request(self, url, params):
        cookies = self.credential.get_cookies()
        return r.get(url, cookies=cookies, params=params).json()['data']

    def get_polymer_dynamic(self, page, offset=None):
        """
        获取自己关注up主的动态
        param:
        page: >= 1
        """
        params = {
            "page": page,
            "type": "video",
            "timezone_offset": -480
        }
        if offset: params['offset'] = offset 
        data = self.sync_fetcher(API['ploymer'], params)
        return data

