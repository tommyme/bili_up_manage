import asyncio
from bilibili_api import video, Credential, user
from pprint import pprint
import requests as r
import json
from bili.manager import Bilibili_user_basic, Up_manager
import httpx
"""
THIS FILE IS DEPRECATED, AND MAY BE REMOVED IN FUTURE VERSION
BECAUSE BILI_USER IS A BETTER SOLUTION
THIS FILE IS CURRENTLY WORK FOR GUI.PY
"""

ybw = Bilibili_user_basic()
u = ybw.user
manager = Up_manager(u)
credential = u.credential
uid = u.uid

# over
async def unfollow(sid):
    print('unfollow: ', sid)
    u.uid = sid
    await u.modify_relation(user.RelationType.UNSUBSCRIBE)
    u.uid = uid

# over
async def classify(uids, groupids):
    resp = await user.set_subscribe_group(uids, groupids, credential)
    print(resp)

# over 这个函数是因为当时classify函数有时候有bug, aiohttp会报错,所以我就写了一个sync的函数
def classify2(uids, groupids):
    if groupids == []:
        # 啥也没选
        print("warning: 你啥也没选")
        groupids = [0]
    elif 0 in groupids and len(groupids)>0:
        # 既在默认分组 又在其他分组
        print("warning: 既在默认分组 又在其他分组,已经帮你删去默认分组")
        groupids.remove(0)
    url = "https://api.bilibili.com/x/relation/tags/addUsers?cross_domain=true"
    cookies = credential.get_cookies()
    headers = {"Referer": "https://www.bilibili.com"}
    data = {'fids': ','.join([str(i) for i in uids]), "tagids": ','.join([str(i) for i in groupids]),
            'csrf': credential.bili_jct}
    resp = r.post(url, headers=headers, cookies=cookies, data=data).text
    resp = json.loads(resp)
    return resp

# over
async def del_group(groupid):
    await user.delete_subscribe_group(groupid, credential)

# over
async def new_group(name):
    await user.create_subscribe_group(name, credential)

# over
def get_groups():
    url = "https://api.bilibili.com/x/relation/tags?jsonp=jsonp&callback=__jp3"
    cookies = credential.get_cookies()
    headers = {"referer": "https://space.bilibili.com/{}/fans/follow".format(uid)}
    resp = r.get(url, headers=headers, cookies=cookies).text[6:-1]
    print(resp)
    resp = json.loads(resp)['data']
    return resp

# over
# get_followings = manager.get_followings
async def get_followings():
    await manager.get_followings()
    return manager.followings_mini

async def get_faces():
    async with httpx.AsyncClient() as client:
        res = await asyncio.gather(*[client.get(i['face']) for i in manager.followings_mini])
    faces = {i['mid']: j.content for i,j in zip(manager.followings_mini, res)}
    return faces

if __name__ == '__main__':
    # respp = asyncio.get_event_loop().run_until_complete(unfollow(389170767))
    # respp = unfollow(389170767)
    gpids = [-10]
    uids = [46880349]
    respp = classify2(uids,gpids)
    pprint(respp)
