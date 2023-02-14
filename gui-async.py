from PyQt5.QtWidgets import QApplication, QWidget, QListWidgetItem
from gui.untitled import Ui_Dialog
from PyQt5 import QtCore
from PyQt5 import QtGui
import sys
from bili.api import get_followings, get_groups, unfollow, del_group, new_group, classify, classify2
import asyncio
import requests as r
import webbrowser
from typing import List
import qasync
import httpx
import contextlib



class MyWin(QWidget, Ui_Dialog):
    def __init__(self, followings):
        super(MyWin, self).__init__()
        self.setupUi(self)
        # self.loop = asyncio.get_event_loop()
        self.curr_homepage = None

        self.followings = followings
        self.groups = []
        self.gp_dict = {}
        self.fl_dict = {i['uname']: i for i in self.followings}
        self.fl_selected = []
        self.gp_selected = []

        self.groups = get_groups()
        self.gp_dict = {i['name']: i for i in self.groups}
        self.load_gp_list()
        self.gp_pick.insertItems(0, [i['name'] for i in self.groups])
        self.gp_pick.insertItem(0, "ALL")
        self.gp_pick.setCurrentIndex(0)
        self.load_fl_list("ALL")
        self.connect()

    @qasync.asyncSlot()
    async def reload_followings(self):
        self.followings = await get_followings()
        self.fl_dict = {i['uname']: i for i in self.followings}

    def connect(self):
        self.fl_list.currentItemChanged.connect(self.show_info)
        self.fl_pic.setScaledContents(True)
        self.gp_pick.currentTextChanged.connect(self.refresh_fl_list)
        self.btn_unfl.clicked.connect(self._btn_unfollow)   # need refresh
        self.btn_cls.clicked.connect(self._btn_classify)    # need refresh
        self.btn_del_gp.clicked.connect(self._btn_delete_gp)
        self.btn_add_gp.clicked.connect(self._btn_new_gp)
        self.btn_homepage.clicked.connect(lambda : webbrowser.open(self.curr_homepage))
    
    @contextlib.contextmanager
    def loading(self):
        self.label_loading.setText("loading...")
        yield
        self.label_loading.setText("")

    @qasync.asyncSlot()
    async def _async_get_fl(self):
        """
        异步加载关注列表，并且建立dict
        :return:
        """
        self.followings = await get_followings()
        self.fl_dict = {i['uname']: i for i in self.followings}

    @qasync.asyncSlot()
    async def show_info(self):
        """
        展示选择的up的信息，并且加载头像
        :return:
        """
        s = self.fl_list.currentItem().text()
        info = self.fl_dict[s]
        print(info)
        self.curr_homepage = f"https://space.bilibili.com/{info['mid']}"
        face = info['face']
        content = info['sign']
        self.fl_info.setText(content)
        with self.loading():
            async with httpx.AsyncClient() as client:
                resp = await client.get(face)
        img = QtGui.QImage.fromData(resp._content)
        self.fl_pic.setPixmap(QtGui.QPixmap.fromImage(img))

        for i in range(len(self.groups)):
            self.gp_list.item(i).setCheckState(False)
        if info['tag'] is not None:
            ids = [i['tagid'] for i in self.groups]
            indexs = [ids.index(i) for i in info['tag']]
            [self.gp_list.item(i).setCheckState(True) for i in indexs]

    def in_group(self, i, gname):
        """
        判断up主是否在对应的组里面
        :param i:
        :param gname:
        :return:
        """
        if gname == 'ALL':
            return True
        if i['tag'] is not None:
            for sid in i['tag']:
                if sid == self.gp_dict[gname]['tagid']:
                    return 1
        elif gname == '默认分组':
            return 1
        return 0

    def load_fl_list(self, gname):
        """
        通过self.followings加载关注的up的列表
        :param gname:
        :return:
        """
        fl_list = [i['uname'] for i in self.followings if self.in_group(i, gname)]
        for i in fl_list:
            item = QListWidgetItem()
            item.setCheckState(QtCore.Qt.Unchecked)
            item.setText(i)
            self.fl_list.addItem(item)

    def load_gp_list(self):
        gp_list = [i['name'] for i in self.groups]
        for i in gp_list:
            item = QListWidgetItem()
            item.setCheckState(QtCore.Qt.Unchecked)
            item.setText(i)
            self.gp_list.addItem(item)

    def refresh_fl_list(self, refresh=False):
        if refresh:
            self.reload_followings()
        # 不涉及网络请求
        self.fl_list.disconnect()
        self.fl_list.clear()
        self.load_fl_list(self.gp_pick.currentText())
        self.fl_list.currentItemChanged.connect(self.show_info)

    def refresh_gp_list(self):
        self.gp_list.disconnect()
        self.gp_list.clear()
        self.load_gp_list()

        self.gp_pick.disconnect()
        self.gp_pick.clear()
        self.gp_pick.insertItems(0, [i['name'] for i in self.groups])
        self.gp_pick.insertItem(0, "ALL")
        self.gp_pick.setCurrentIndex(0)
        self.gp_pick.currentTextChanged.connect(self.refresh_fl_list)

    def get_fl_selected(self) -> List[str]:
        """
        得到选中的following up; set self.fl_selected
        """
        count = self.fl_list.count()
        cb_list = [self.fl_list.item(i) for i in range(count)]
        selected = []
        for cb in cb_list:  # type:QCheckBox
            if cb.checkState() > 0:
                selected.append(cb.text())
        print(selected)
        self.fl_selected = selected

    def get_gp_selected(self) -> List[str]:
        """
        得到选中的group; set self.gp_selected
        """
        count = self.gp_list.count()
        cb_list = [self.gp_list.item(i) for i in range(count)]
        selected = []
        for cb in cb_list:  # type:QCheckBox
            if cb.checkState() > 0:
                selected.append(cb.text())
        print(selected)
        self.gp_selected = selected

    @qasync.asyncSlot()
    async def _btn_unfollow(self):
        self.get_fl_selected()
        for i in self.fl_selected:
            mid = self.fl_dict[i]['mid']
            await unfollow(mid)
            del self.followings[list(self.fl_dict).index(i)]
            self.fl_dict.pop(i)
        self.refresh_fl_list()


    @qasync.asyncSlot()
    async def _btn_classify(self):
        self.get_gp_selected()
        self.get_fl_selected()
        uids = [self.fl_dict[i]['mid'] for i in self.fl_selected]
        groupids = [self.gp_dict[i]['tagid'] for i in self.gp_selected]
        await classify(uids, groupids)
        self.refresh_fl_list(refresh=True)

    @qasync.Slot()
    async def _btn_delete_gp(self):
        self.get_gp_selected()
        gpids = [self.gp_dict[i]['tagid'] for i in self.gp_selected]
        for i in gpids:
            await del_group(i)
        for i in self.gp_selected:
            del self.groups[list(self.gp_dict).index(i)]
            self.gp_dict.pop(i)
        self.refresh_gp_list()

    @qasync.asyncSlot()
    async def _btn_new_gp(self):
        name = self.new_gp_name.text()
        await new_group(name)
        self.groups = get_groups()
        self.gp_dict = {i['name']: i for i in self.groups}
        self.refresh_gp_list()

async def main(followings):
    future = asyncio.Future()
    app = QApplication.instance()
    app.aboutToQuit.connect(future.cancel)
    mainWindow = MyWin(followings)
    # mainWindow.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
    mainWindow.show()
    await future

if __name__ == '__main__':
    try:
        
        followings = asyncio.run(get_followings())
        qasync.run(main(followings))
    except asyncio.exceptions.CancelledError:
        sys.exit(0)
