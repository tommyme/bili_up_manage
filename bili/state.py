
from bili.manager import Bilibili_user_basic, Up_manager, TableManager
import asyncio


ybw = Bilibili_user_basic()
up_manager = Up_manager(ybw.user)
asyncio.run(up_manager.init())
table_manager = TableManager(up_manager)

def reload():
    global table_manager
    asyncio.run(up_manager.init())
    table_manager = TableManager(up_manager)
