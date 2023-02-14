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



class MyWin(QWidget, Ui_Dialog):
    def __init__(self, parent=None):
        super(MyWin, self).__init__(parent)
        self.setupUi(self)
        self.loop = asyncio.get_event_loop()
        self.curr_homepage = None

        self.followings = []
        self.groups = []
        self.gp_dict = {}
        self.fl_dict = {}
        self.fl_selected = []
        self.gp_selected = []

        self.groups = get_groups()
        self.gp_dict = {i['name']: i for i in self.groups}
        self.load_gp_list()
        self.gp_pick.insertItems(0, [i['name'] for i in self.groups])
        self.gp_pick.insertItem(0, "ALL")
        self.gp_pick.setCurrentIndex(0)

        self.loop.run_until_complete(self._async_get_fl())
        self.load_fl_list("ALL")
        self.connect()

    def connect(self):
        self.fl_list.currentItemChanged.connect(self.show_info)
        self.fl_pic.setScaledContents(True)
        self.gp_pick.currentTextChanged.connect(self.refresh_fl_list)
        self.btn_unfl.clicked.connect(self.btn_unfollow)
        self.btn_cls.clicked.connect(self.btn_classify)
        self.btn_del_gp.clicked.connect(self.btn_delete_gp)
        self.btn_add_gp.clicked.connect(self.btn_new_gp)
        self.btn_homepage.clicked.connect(self.goto_homepage)

    async def _async_get_fl(self):
        """
        异步加载关注列表，并且建立dict
        :return:
        """
        self.followings = await get_followings()
        self.fl_dict = {i['uname']: i for i in self.followings}

    def goto_homepage(self):
        webbrowser.open(self.curr_homepage)

    def show_info(self):
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
        resp = r.get(face).content
        img = QtGui.QImage.fromData(resp)
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
        加载关注的up的列表
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

    def refresh_fl_list(self):
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
        得到备选统计项的字段
        :return: list[str]
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
        得到备选统计项的字段
        :return: list[str]
        """
        count = self.gp_list.count()
        cb_list = [self.gp_list.item(i) for i in range(count)]
        selected = []
        for cb in cb_list:  # type:QCheckBox
            if cb.checkState() > 0:
                selected.append(cb.text())
        print(selected)
        self.gp_selected = selected

    def btn_unfollow(self):
        self.get_fl_selected()
        self.loop.run_until_complete(self._btn_unfollow())

    async def _btn_unfollow(self):
        for i in self.fl_selected:
            mid = self.fl_dict[i]['mid']
            await unfollow(mid)
            del self.followings[list(self.fl_dict).index(i)]
            self.fl_dict.pop(i)
        self.refresh_fl_list()

    def btn_classify(self):
        self.get_gp_selected()
        self.get_fl_selected()
        self.loop.run_until_complete(self._btn_classify())
        # self._btn_classify2()

    def _btn_classify2(self):
        uids = [self.fl_dict[i]['mid'] for i in self.fl_selected]
        groupids = [self.gp_dict[i]['tagid'] for i in self.gp_selected]
        classify2(uids, groupids)
        for uname in self.fl_selected:
            self.followings[list(self.fl_dict).index(uname)]['tag'] = groupids
            self.fl_dict[uname]['tag'] = groupids
        self.refresh_fl_list()


    async def _btn_classify(self):
        uids = [self.fl_dict[i]['mid'] for i in self.fl_selected]
        groupids = [self.gp_dict[i]['tagid'] for i in self.gp_selected]
        await classify(uids, groupids)
        self.refresh_fl_list()

    def btn_delete_gp(self):
        self.get_gp_selected()
        self.loop.run_until_complete(self._btn_delete_gp())

    async def _btn_delete_gp(self):
        gpids = [self.gp_dict[i]['tagid'] for i in self.gp_selected]
        for i in gpids:
            await del_group(i)
        for i in self.gp_selected:
            del self.groups[list(self.gp_dict).index(i)]
            self.gp_dict.pop(i)
        self.refresh_gp_list()

    def btn_new_gp(self):
        self.loop.run_until_complete(self._btn_new_gp())

    async def _btn_new_gp(self):
        name = self.new_gp_name.text()
        await new_group(name)
        self.groups = get_groups()
        self.gp_dict = {i['name']: i for i in self.groups}
        self.refresh_gp_list()


if __name__ == '__main__':
    app = QApplication(["ybw"])
    myWin = MyWin()
    myWin.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
    myWin.show()
    app.exec_()
    # sys.exit(app.exec_())
