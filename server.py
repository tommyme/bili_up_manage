from matplotlib.pyplot import table
from sanic import Sanic
from sanic_cors import CORS
from bili_user import Bilibili_user_basic, Up_manager, TableManager
from sanic.response import raw, file, text, json
import requests as r
import httpx
import io
import asyncio

app = Sanic("http")
CORS(app)

ybw = Bilibili_user_basic()
manager = Up_manager(ybw.user)
asyncio.run(manager.init())
table_manager = TableManager(manager)

# TODO: 网页扫码登陆
def param(esse_params, f):
    def wrapper(*args, **kwargs):
        return f(*args, **kwargs)
    return wrapper


@app.get("/videos")
async def get_videos(request):
    mid = request.args.get("mid")
    res = await table_manager.get_videos(mid)
    return json(res)

@app.get("/groups")
async def get_groups(request):
    res = table_manager.get_treeGroups()
    return json(res)

@app.get("/followings")
def get_followings(request):
    tree_key = request.args.get("key")
    res = table_manager.get_treeNode_data(tree_key)
    return json(res)


@app.get("/pic")
async def get_pic(request):
    url = request.args.get("url", False)
    if not url: 
        return text("nop") 
    async with httpx.AsyncClient() as client:
        raw_img = await client.get(url)
    return raw(raw_img.content, content_type="image/jpeg")
    # return file("08.jpg")
if __name__ == '__main__':
    app.run(host="127.0.0.1", port=8000, debug=True)