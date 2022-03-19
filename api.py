import asyncio
from bilibili_api import video, Credential, user
from pprint import pprint
import requests as r
import json
from bili_user import Bilibili_user_basic


ybw = Bilibili_user_basic(uid=306062555)
u = ybw.get_user()
credential = u.credential
uid = u.uid


async def unfollow(sid):
    print('unfollow: ', sid)
    u.uid = sid
    await u.modify_relation(user.RelationType.UNSUBSCRIBE)
    u.uid = uid


async def classify(uids, groupids):
    resp = await user.set_subscribe_group(uids, groupids, credential)
    print(resp)


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


async def del_group(groupid):
    await user.delete_subscribe_group(groupid, credential)


async def new_group(name):
    await user.create_subscribe_group(name, credential)


def get_groups():
    url = "https://api.bilibili.com/x/relation/tags?jsonp=jsonp&callback=__jp3"
    cookies = credential.get_cookies()
    headers = {"referer": "https://space.bilibili.com/{}/fans/follow".format(uid)}
    resp = r.get(url, headers=headers, cookies=cookies).text[6:-1]
    print(resp)
    resp = json.loads(resp)['data']
    return resp


async def get_followings():
    followings = []
    i = 1
    while True:
        info = await u.get_followings(i)
        if info['list']:
            i += 1
            followings += info['list']
        else:
            break
    return followings


if __name__ == '__main__':
    # respp = asyncio.get_event_loop().run_until_complete(unfollow(389170767))
    # respp = unfollow(389170767)
    gpids = [-10]
    uids = [46880349]
    respp = classify2(uids,gpids)
    pprint(respp)
