from PyQt5.QtWidgets import (QWidget, QTableWidget, QLabel,
                             QTableWidgetItem,
                             QAbstractItemView, QHeaderView,
                             QMenu, QAction, QWidgetAction)
from PyQt5.QtCore import (Qt, pyqtSignal, QCoreApplication)
from PyQt5.QtGui import QPixmap
import qtawesome as qta

class QSongsTableWidget(QTableWidget):
    itemPlay = pyqtSignal(int)
    itemAdd = pyqtSignal(list)
    itemCollect = pyqtSignal(list)

    __row = -1

    def __init__(self, parent):
        QTableWidget.__init__(self, parent)

        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.setShowGrid(False)
        self.setColumnCount(9)
        self.verticalHeader().setVisible(False)
        self.verticalHeader().setMinimumSectionSize(50)

        self.setEditTriggers(QAbstractItemView.NoEditTriggers) # 不可编辑
        # 列宽、行高
        self.setColumnWidth(0, 20)
        self.setColumnWidth(1, 50)
        self.setColumnWidth(5, 50)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        # 隐藏列
        self.setColumnHidden(6, True)
        self.setColumnHidden(7, True)
        self.setColumnHidden(8, True)

        _translate = QCoreApplication.translate
        item = QTableWidgetItem('')
        self.setHorizontalHeaderItem(0, item)
        item = QTableWidgetItem('')
        self.setHorizontalHeaderItem(1, item)
        item = QTableWidgetItem()
        item.setText(_translate("MainWindow", "歌名"))
        self.setHorizontalHeaderItem(2, item)
        item = QTableWidgetItem()
        item.setText(_translate("MainWindow", "歌手"))
        self.setHorizontalHeaderItem(3, item)
        item = QTableWidgetItem()
        item.setText(_translate("MainWindow", "专辑"))
        self.setHorizontalHeaderItem(4, item)
        item = QTableWidgetItem()
        item.setText(_translate("MainWindow", "时长"))
        self.setHorizontalHeaderItem(5, item)

        self.setup_rightbutton_actions() # 设置菜单
        self.setup_slots() # 连接槽函数
        self.setup_events() # 连接事件

    # 设置菜单
    def setup_rightbutton_actions(self):
        color = '#333'

        self.rightclick_menu = QMenu(self)

        act_play = QAction(qta.icon('fa.play', color=color), '播放', self.rightclick_menu)
        act_add = QAction(qta.icon('fa.plus', color=color), '添加到播放列表', self.rightclick_menu)
        act_collect = QAction(qta.icon('fa.heart-o', color=color), '收藏', self.rightclick_menu)

        act_play.triggered.connect(self.act_item_play)
        act_add.triggered.connect(self.act_item_add)
        act_collect.triggered.connect(self.act_item_collect)

        self.rightclick_menu.addAction(act_play)
        self.rightclick_menu.addAction(act_add)
        self.rightclick_menu.addAction(act_collect)

    # 连接槽函数
    def setup_slots(self):
        self.cellDoubleClicked.connect(self.on_cellDoubleClicked)
        self.cellEntered.connect(self.on_cellEntered)

    # 连接事件
    def setup_events(self):
        self.mouseReleaseEvent = self.on_mouseReleaseEvent

# ======== 自定义槽函数 ========

    # 双击项
    def on_cellDoubleClicked(self, row, column):
        self.itemPlay.emit(row)

    # 经过单元格
    def on_cellEntered(self, row, column):
        pass

# ======== 事件 ========

    # 重绘
    def paintEvent(self, event) -> None:
        self.setColumnWidth(3, self.width() // 5) 
        self.setColumnWidth(4, self.width() // 5)       
        
        return QTableWidget.paintEvent(self, event)

    # 松开鼠标
    def on_mouseReleaseEvent(self, event):
        QTableWidget.mouseReleaseEvent(self, event)

        # 是否右键单击
        if (event.button() != Qt.RightButton) or (self.get_selected_rows() == None):
            return

        # 弹出菜单
        self.rightclick_menu.exec_(event.globalPos())

# ======== 其他方法 ========

    # 播放
    def act_item_play(self):
        rows = self.get_selected_rows()
        if rows:
            self.itemPlay.emit(rows[0])

    # 添加到播放列表
    def act_item_add(self):
        rows = self.get_selected_rows()
        if rows:
            self.itemAdd.emit(rows)

    # 喜欢
    def act_item_collect(self):
        rows = self.get_selected_rows()
        if rows:
            self.itemCollect.emit(rows)

    def get_selected_rows(self):
        rows = []
        for row in self.selectedItems():
            rows.append(row.row())
        return list(set(rows))

    def insert_datas(self, row, datas):
        # 行号
        row_sign = QTableWidgetItem(str(row + 1))
        row_sign.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter) # 垂直、水平居中
        self.setItem(row, 0, row_sign)

        # 其他文本数据
        for i, text in enumerate(datas):
            item = QTableWidgetItem(str(text))
            self.setItem(row, i + 2, item)

    def insert_pixmap(self, row, pixmap):
        # 加载图片
        image = QLabel()
        image.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        image.setPixmap(pixmap)            
        self.setCellWidget(row, 1, image)

    def get_datas(self, row):
        datas = []        
        for i in range(2, 9):
            datas.append(self.item(row, i).text())

        return datas

    def get_pixmap(self, row):
        try:
            pixmap = self.cellWidget(row, 1).pixmap()
        except:
            pixmap = QPixmap()

        return pixmap

    def move_item(self, from_row, to_row):
        # 获取信息分别插入 列表
        from_datas = self.get_datas(from_row)
        to_datas = self.get_datas(to_row)
        from_pixmap = self.get_pixmap(from_row)
        to_pixmap = self.get_pixmap(to_row)

        self.insert_datas(to_row, from_datas)
        self.insert_datas(from_row, to_datas)
        self.insert_pixmap(to_row, from_pixmap)
        self.insert_pixmap(from_row, to_pixmap)
        self.selectRow(to_row)

    def remove_item(self, row):
        self.removeRow(row)

        for r in range(row, self.rowCount()):
            self.item(r, 0).setText(str(r + 1))

        if self.rowCount() < row + 1:
            self.selectRow(row - 1)
        else:
            self.selectRow(row)