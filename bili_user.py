import qrcode_terminal
import requests
import pickle
import re
import time
import asyncio
import requests as r
import itertools
import os
from collections import defaultdict as ddict
from tag import Addict
import httpx
import json
from bilibili_api import video, Credential, user
from utils import filter, load_pickle, dump_pickle, dict2dict, copyColInTable, table2dict
import pandas as pd

# bili-api doc at https://bili.moyu.moe/
# 由于pandas查询的限制 我们暂时规定: 
#       每个up主只有一个tag 
#       这个分组数据是从bili-api获取的
#       后期我们自己掌管数据的时候我们就可以重新设计一下结构
## pandas的限制是 我们想用它的filter table[xxId in table['tag']]
## 但是table['tag']是一个list 而且你不能用`in`
## 我们采取了一个折中的方法: 把table['tag']转换成str, 然后用pandas str的contains
urlConvert = lambda url: f'http://localhost:8000/pic?url={url}'

class Bilibili_user_basic():
    """
    uid: get it from https://space.bilibili.com/<uid>/
    """
    GET_LOGIN_URL = "https://passport.bilibili.com/qrcode/getLoginUrl"
    GET_LOGIN_INFO_URL = "https://passport.bilibili.com/qrcode/getLoginInfo"
    GET_LOGIN_buvid3_URL = "https://api.bilibili.com/x/frontend/finger/spi"
    SESSDATA, bili_jct, buvid3, uid, info_dict = None, None, None, None, None
    _user = None

    def __init__(self, qrcode_Force=False):
        self.session = requests.Session()
        if (not self.load_info_from_file()) or qrcode_Force:
            self.login()
            while not self.get_info():
                time.sleep(1)
                print("Waiting for login...")
            self.get_buvid3()
            self.dump_info()
        print("登录成功")
        print(self.SESSDATA, self.bili_jct, self.buvid3, self.uid)

    def load_info_from_file(self):
        try:
            info = load_pickle("user_secret.pkl")
            self.SESSDATA = info["SESSDATA"]
            self.bili_jct = info["bili_jct"]
            self.buvid3   = info["buvid3"]
            self.uid      = info["uid"]
            return True
        except Exception as e:
            print(e)
            print("====================")
            print("加载缓存失败，请扫码登录")
            return False

    def login(self):
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:85.0) Gecko/20100101 Firefox/85.0"
        }
        self.session.headers.update(headers)
        resp = self.session.get(self.GET_LOGIN_URL).json()
        self.oauthkey = resp["data"]["oauthKey"]
        qrcode_terminal.draw(resp["data"]["url"])
    
    def get_info(self):
        resp = self.session.post(
            self.GET_LOGIN_INFO_URL,
            data={
                "oauthKey": self.oauthkey,
                "gourl": "https://www.bilibili.com/"
            }
        ).json()
        if resp["status"]:
            self.uid = re.findall(r"DedeUserID=[0-9]+", resp["data"]["url"])[0].split("=")[1]
            self.info_dict = self.session.cookies.get_dict()
            self.SESSDATA = self.session.cookies.get("SESSDATA")
            self.bili_jct = self.session.cookies.get("bili_jct")
            print("扫码登录成功")
            return True
        else:
            return False
    
    def get_buvid3(self):
        resp = self.session.get(self.GET_LOGIN_buvid3_URL, 
            cookies={"SESSDATA": self.SESSDATA}
        ).json()
        self.buvid3 = resp["data"]["b_3"]

    def dump_info(self):
        with open("user_secret.pkl","wb") as f:
            data = {
                "uid": self.uid,
                "SESSDATA": self.SESSDATA,
                "bili_jct": self.bili_jct,
                "buvid3": self.buvid3
            }
            pickle.dump(data, f)
    
    @property
    def user(self):
        if not self._user:
            credential = Credential(sessdata=self.SESSDATA, bili_jct=self.bili_jct, buvid3=self.buvid3)
            self._user = user.User(uid=self.uid, credential=credential)
        return self._user


class Up_manager():
    """
    用于管理tagging system和获取follow信息 目前还有一些取关和group管理的功能
    """
    followings = None
    followings_mini = None
    groups = None
    PICKLE_ROOT = "./taging_sys"
    tables: dict[str, pd.DataFrame] = {}

    def __init__(self, user_module):
        self.user_module: user.User = user_module
        self.num_fl = r.get(
            f"https://api.bilibili.com/x/relation/stat?vmid={user_module.uid}"
        ).json()['data']['following']
        self.taging_sys = self.load_taging_sys_from_pkl()
    
    async def init(self):
        await self.get_followings()
        await self.get_groups()

    async def get_followings(self):
        num_pages = self.num_fl // 20 
        task_list = [asyncio.create_task(self.user_module.get_followings(i)) for i in range(1, num_pages+2)]
        done, pending = await asyncio.wait(task_list)
        res = [i.result() for i in done]
        res = [i['list'] for i in res]
        self.followings = list(itertools.chain(*res))
        useful_keys = ["mid","tag","uname","face","sign"]
        self.followings_mini = [filter(i, useful_keys) for i in self.followings]

    async def get_groups(self):
        url = "https://api.bilibili.com/x/relation/tags?jsonp=jsonp&callback=__jp3"
        cookies = self.user_module.credential.get_cookies()
        headers = {"referer": "https://space.bilibili.com/{}/fans/follow".format(self.user_module.uid)}
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, cookies=cookies, headers=headers)
            resp = resp.text[6:-1]
        resp = json.loads(resp)['data']
        self.groups = resp

    def load_taging_sys_from_pkl(self):
        if os.path.exists(self.PICKLE_ROOT):
            return load_pickle(self.PICKLE_ROOT)
        else:
            return Addict()
    
    def tag_item(self, uid, Tag_list: list):
        """
        args:
            Tag_list:   ["#daily/study/math", "#web/vue"]
            uid:        12345678
        """
        # 1. check tag list is valid
        # 2. tag item 
        #   - split
        #   - check if in tag sys (omitted by Addict)
        #   - add uid to tag.elements
        for Tag in Tag_list:
            Tag_splited = [i[1:] for i in re.findall("(#|/)[a-z]*")]
            p = self.taging_sys
            for tag in Tag_splited:
                p = p[tag]  # 利用Addict的特性
            p.elements.append(uid)  
        
        self.dump_tag_sys()
        
    def dump_tag_sys(self):
        dump_pickle(self.taging_sys, self.PICKLE_ROOT)

    async def set_subscribe_group(self, uids, groupids):
        return await user.set_subscribe_group(uids, groupids, self.user_module.credential)
    
    async def delete_subscribe_group(self, groupid):
        return await user.delete_subscribe_group(groupid, self.user_module.credential)

    async def create_subscribe_group(self, name):
        return await user.create_subscribe_group(name, self.user_module.credential)

    async def unfollow(self, sid):
        uid, self.user_module.uid = self.user_module.uid, sid
        res = await self.user_module.modify_relation(user.RelationType.UNSUBSCRIBE)
        self.user_module.uid = uid
        return res
    
    def trans2webTreeNodeFormat(self):
        TreeData: list[dict] = []
        key_dict_group = {
            "name":"label",
            "tagid": "mid",
        }
        for i in range(len(self.groups)):
            TreeData.append(dict2dict(self.groups[i], key_dict_group))


class TableManager():
    """主要负责向外提供数据
    """
    def __init__(self, up_manager: Up_manager):
        self.groups = pd.DataFrame(up_manager.groups)
        colMap = {'name': 'label'}
        copyColInTable(self.groups, colMap)
        # mid in table `groups` will be like "t:12345678"
        self.groups.loc[:, "mid"] = self.groups['tagid'].apply(lambda x:f"t:{x}")
        self.groups.loc[:, 'lazy'] = True
        # neg value indecates it's a group.

        self.followings_mini = pd.DataFrame(up_manager.followings_mini)
        colMap = {'uname': 'label'}
        copyColInTable(self.followings_mini, colMap)
        self.followings_mini["avatar"] = self.followings_mini["face"].apply(urlConvert)
        # url convert

    def _get_up_in_group(self, groupid):
        # pandas 是真滴快
        groupstr = "None" if groupid == 0 else str(groupid) # 默认分组没有tagId
        table = self.followings_mini
        res = table[table['tag'].astype(str).str.contains(groupstr)]
        return res
    
    def get_treeNode_data(self, tree_key):
        """provide data for web TreeNode
        params:
        tree_key: string "t:xxxxx", map to `mid` in table `groups`
        """
        groupid = int(tree_key[2:])
        return table2dict(self._get_up_in_group(groupid))
    
    def get_treeGroups(self):
        return table2dict(self.groups) # no children
    
    async def get_videos(self, mid):
        up = user.User(mid)
        res = await up.get_videos()
        res = res['list']['vlist'][:20]
        useful = ['comment', 'pic', 'title', 'created', 'length','bvid','play']
        table = pd.DataFrame(res)[useful]
        table['pic'] = table['pic'].apply(urlConvert)
        return table2dict(table)




class ActionManager():
    pass






if __name__ == "__main__":

    async def main():
        ybw = Bilibili_user_basic(qrcode_Force=False)
        manager = Up_manager(ybw.user)
        await asyncio.gather(
            manager.get_followings(),
            manager.get_groups(),
        )
        print(manager.followings_mini[0])

    asyncio.run(main())

