import qrcode_terminal
import requests
import pickle

# bili-api doc at https://bili.moyu.moe/

class Bilibili_user_basic():
    """
    uid: get it from https://space.bilibili.com/<uid>/
    """
    GET_LOGIN_URL = "https://passport.bilibili.com/qrcode/getLoginUrl"
    GET_LOGIN_INFO_URL = "https://passport.bilibili.com/qrcode/getLoginInfo"
    GET_LOGIN_buvid3_URL = "https://api.bilibili.com/x/frontend/finger/spi"

    def __init__(self, uid:int, qrcode_Force=False):
        self.SESSDATA, self.bili_jct, self.buvid3, self.info_dict = None, None, None, None
        self.uid = uid
        self.session = requests.Session()
        if (not self.load_info_from_file()) or qrcode_Force:
            self.login()
            self.get_info()
            self.get_buvid3()
            self.dump_info()
        print("登录成功")
        print(self.SESSDATA, self.bili_jct, self.buvid3)

    def load_info_from_file(self):
        try:
            with open("user_secret.pkl","rb") as f:
                cookies = pickle.load(f)
            self.SESSDATA = cookies["SESSDATA"]
            self.bili_jct = cookies["bili_jct"]
            self.buvid3 = cookies["buvid3"]
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
        input("Press return after you've logined by QRcode")
    
    def get_info(self):
        resp = self.session.post(
            self.GET_LOGIN_INFO_URL,
            data={
                "oauthKey": self.oauthkey,
                "gourl": "https://www.bilibili.com/"
            }
        ).json()
        print(resp)
        assert resp["status"]
        self.info_dict = self.session.cookies.get_dict()
        self.SESSDATA = self.session.cookies.get("SESSDATA")
        self.bili_jct = self.session.cookies.get("bili_jct")
        print("扫码登录成功")
    
    def get_buvid3(self):
        resp = self.session.get(self.GET_LOGIN_buvid3_URL, 
            cookies={"SESSDATA": self.SESSDATA}
        ).json()
        self.buvid3 = resp["data"]["b_3"]

    def dump_info(self):
        with open("user_secret.pkl","wb") as f:
            data = {
                "SESSDATA": self.SESSDATA,
                "bili_jct": self.bili_jct,
                "buvid3": self.buvid3
            }
            pickle.dump(data, f)
    
    def get_user(self):
        from bilibili_api import video, Credential, user
        credential = Credential(sessdata=self.SESSDATA, bili_jct=self.bili_jct, buvid3=self.buvid3)
        u = user.User(uid=self.uid, credential=credential)
        return u


class Up_manager():
    def __init__(self, user):
        self.user = user
    
    async def get_followings(self):
        followings = []
        i = 1
        while True:
            info = await self.user.get_followings(i)
            if info['list']:
                i += 1
                followings += info['list']
            else:
                break
        self.followings = followings


if __name__ == "__main__":
    import asyncio
    ybw = Bilibili_user_basic(uid=306062555, qrcode_Force=True)
    manager = Up_manager(ybw.get_user())
    # asyncio.run(manager.get_followings())   # 这里api的模块没写好,由于async的更新会报错,但是不影响使用
    # print(manager.followings)
