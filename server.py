from sanic import Sanic
from sanic_cors import CORS
from sanic.response import raw, file, json
import httpx
from bili.utils import param_or_fail
import asyncio
import os

print(os.getpid(), __name__)
app = Sanic("http")
CORS(app)

polymer_dynamic_offset = None
# TODO: 网页扫码登陆


@app.get("/videos")
@param_or_fail("mid")
async def get_videos(request):
    mid = request.args.get("mid")
    res = await table_manager.get_videos(mid)
    return json(res)


@app.get("/groups")
async def get_groups(request):
    res = table_manager.get_treeGroups()
    return json(res)


@app.get("/followings")
@param_or_fail("key")
def get_followings(request):
    tree_key = request.args.get("key")
    res = table_manager.get_treeNode_data(tree_key)
    return json(res)


@app.get("/pic")
@param_or_fail("url")
async def get_pic(request):
    url = request.args.get("url")
    async with httpx.AsyncClient() as client:
        raw_img = await client.get(url)
    return raw(raw_img.content, content_type="image/jpeg")


@app.get("/pic_download")
async def download(req):
    return file("./08.png")

@param_or_fail('page', 'groupId')
@app.get("/polymer_dynamic")
def polymer_dynamic(request):
    global polymer_dynamic_offset
    page = request.args.get('page')
    groupId = request.args.get('groupId')
    data = ybw.user.get_polymer_dynamic(page, offset=polymer_dynamic_offset)
    polymer_dynamic_offset = data['offset']
    data = table_manager.pps_polymer_data(data['items'], groupId)
    return json(data)

@param_or_fail('mid')
@app.get("/sign")
def sign(request):
    mid = int(request.args.get('mid'))
    table = table_manager.followings_mini
    data = table[table['mid'] == mid]['sign'].values[0]
    return json({"sign": data})

@app.get("reload")
def reload_managers(req):
    reload()
    return json({"res": "ok"})

@param_or_fail('mid')
@app.get("unfollow")
async def unfollow(request):
    mid = int(request.args.get('mid'))
    await up_manager.unfollow(mid)
    return json({"res":"ok"})

if __name__ == '__main__':
    from bili.state import ybw, up_manager, table_manager, reload
    app.run(host="127.0.0.1", port=8000, debug=False, single_process=True)

