# 检查koala的动态并且获取最新视频 然后拿到置顶的评论
import json
from bilibili_api import user, sync, comment


# 实例化
u = user.User(489667127)


async def get_dyn():
    # 用于记录起点
    offset = 0

    # 用于存储所有动态
    dynamics = []

    page = await u.get_dynamics(offset)
    if 'cards' in page:
        # 若存在 cards 字段（即动态数据），则将该字段列表扩展到 dynamics
        dynamics.extend(page['cards'])

    # 打印动态数量
    print(f"共有 {len(dynamics)} 条动态")
    return dynamics


async def get_content():

    dynamics = await get_dyn()

    aid = dynamics[0]['card']['aid']
    c = await comment.get_comments(aid, comment.ResourceType.VIDEO)
    content = c['upper']['top']['content']['message']
    return content
