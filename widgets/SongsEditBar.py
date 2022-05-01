from PyQt5.QtWidgets import (QWidget, QPushButton, QSpacerItem,
                             QHBoxLayout, 
                             QSizePolicy,
                             QFileDialog)
from PyQt5.QtCore import (QSize, pyqtSignal, QDir)
import qtawesome as qta

class QSongsEditBar(QWidget):
    upmoved = pyqtSignal()
    downmoved = pyqtSignal()
    removed = pyqtSignal()
    fromLocal = pyqtSignal(list)

    def __init__(self, parent):
        QWidget.__init__(self, parent)

        self.horizontalLayout_12 = QHBoxLayout(self)
        self.horizontalLayout_12.setContentsMargins(0, 0, 0, 5)
        self.horizontalLayout_12.setSpacing(5)
        self.remove = QPushButton(self)
        self.remove.setEnabled(False)
        self.remove.setMinimumSize(QSize(70, 26))
        self.remove.setProperty('is_editbtn', True)
        self.horizontalLayout_12.addWidget(self.remove)
        self.upmove = QPushButton(self)
        self.upmove.setEnabled(False)
        self.upmove.setMinimumSize(QSize(70, 26))
        self.upmove.setProperty('is_editbtn', True)
        self.horizontalLayout_12.addWidget(self.upmove)
        self.downmove = QPushButton(self)
        self.downmove.setEnabled(False)
        self.downmove.setMinimumSize(QSize(70, 26))
        self.downmove.setProperty('is_editbtn', True)
        self.horizontalLayout_12.addWidget(self.downmove)
        spacerItem = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.horizontalLayout_12.addItem(spacerItem)
        self.from_local = QPushButton(self)
        self.from_local.setMinimumSize(QSize(100, 26))
        self.from_local.setProperty('is_editbtn', True)
        self.horizontalLayout_12.addWidget(self.from_local)

        self.remove.setText("删除")
        self.upmove.setText("上移")
        self.downmove.setText("下移")
        self.from_local.setText("本地歌曲")

        color = '#333'
        self.remove.setIcon(qta.icon('fa.trash-o', color=color))
        self.upmove.setIcon(qta.icon('fa.angle-double-up', color=color))
        self.downmove.setIcon(qta.icon('fa.angle-double-down', color=color))
        self.from_local.setIcon(qta.icon('fa.folder-open-o', color=color))

        self.remove.clicked.connect(self.on_remove_clicked)
        self.upmove.clicked.connect(self.on_upmove_clicked)
        self.downmove.clicked.connect(self.on_downmove_clicked)
        self.from_local.clicked.connect(self.on_from_local_clicked)

# ======== 自定义槽函数 ========

    # 列表项删除
    def on_remove_clicked(self):
        self.removed.emit()

    # 列表项上移
    def on_upmove_clicked(self):
        self.upmoved.emit()

    # 列表项下移
    def on_downmove_clicked(self):
        self.downmoved.emit()

    def on_from_local_clicked(self):
        cur_path = QDir.currentPath()
        title = '打开'
        filt = '所有文件(*.*);;mp3文件(*.mp3)'
        filelist, file_filter = QFileDialog.getOpenFileNames(self, title, cur_path, filt)
        
        datas = []

        for index, url in enumerate(filelist):
            path = '/'.join(url.replace('\\', '/').split('/')[:-1])
            file = url.replace('\\', '/').split('/')[-1]
            file_name = '.'.join(file.split('.')[:-1])
            suffix = file.split('.')[-1]

            if suffix not in ['mp3']:
                continue

            song_name = file_name
            name_split = song_name.split('-')
            if len(name_split) != 1:
                song_name = '-'.join(name_split[:-1])
                artist = name_split[-1]
            else:
                artist = '本地'
            album = '本地'

            data = [song_name, artist, album, '', *['local:' + url] * 3]
            datas.append(data)
            
        self.fromLocal.emit(datas)
        
    def upmoveEnabled(self):
        return self.upmove.isEnabled()
        
    def downmoveEnabled(self):
        return self.downmove.isEnabled()
        
    def removeEnabled(self):
        return self.remove.isEnabled()

    # 歌曲列表选中歌曲变化
    def on_table_itemSelectionChanged(self):
        selected_items = self.table.selectedItems()

        # “删除”按钮
        if len(selected_items) != 0:
            self.remove.setEnabled(True)
        else:
            self.remove.setEnabled(False)

        # “上移”、“下移”按钮
        if len(selected_items) != 1 * 5:
            self.upmove.setEnabled(False)
            self.downmove.setEnabled(False)

            return

        row = self.table.row(selected_items[0])

        if row != 0:
            self.upmove.setEnabled(True)
        else:
            self.upmove.setEnabled(False)

        if row != self.table.rowCount() - 1:
            self.downmove.setEnabled(True)
        else:
            self.downmove.setEnabled(False)

# ======== 组件事件 ========

# ======== 其他方法 ========

    def bind_table(self, widget):
        self.table = widget
        self.table.itemSelectionChanged.connect(self.on_table_itemSelectionChanged)