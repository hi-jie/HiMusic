from PyQt5.QtWidgets import (QWidget, QPushButton, QSpacerItem,
                             QHBoxLayout, 
                             QSizePolicy)
from PyQt5.QtCore import (QSize, QMetaObject, pyqtSignal, pyqtSlot)
import qtawesome as qta

class QSongsEditBar(QWidget):
    upmoved = pyqtSignal()
    downmoved = pyqtSignal()
    removed = pyqtSignal()
    fromLocal = pyqtSignal()

    def __init__(self, parent):
        QWidget.__init__(self, parent)

        self.horizontalLayout_12 = QHBoxLayout(self)
        self.horizontalLayout_12.setContentsMargins(0, 0, 0, 5)
        self.horizontalLayout_12.setSpacing(5)
        self.remove = QPushButton(self)
        self.remove.setEnabled(False)
        self.remove.setMinimumSize(QSize(70, 26))
        self.horizontalLayout_12.addWidget(self.remove)
        self.upmove = QPushButton(self)
        self.upmove.setEnabled(False)
        self.upmove.setMinimumSize(QSize(70, 26))
        self.horizontalLayout_12.addWidget(self.upmove)
        self.downmove = QPushButton(self)
        self.downmove.setEnabled(False)
        self.downmove.setMinimumSize(QSize(70, 26))
        self.horizontalLayout_12.addWidget(self.downmove)
        spacerItem = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.horizontalLayout_12.addItem(spacerItem)
        self.from_local = QPushButton(self)
        self.from_local.setMinimumSize(QSize(100, 26))
        self.horizontalLayout_12.addWidget(self.from_local)

        self.remove.setText("删除")
        self.upmove.setText("上移")
        self.downmove.setText("下移")
        self.from_local.setText("本地歌曲")

        color = '#555'
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
        self.fromLocal.emit()

    def setUpmoveEnabled(self, state: bool):
        self.upmove.setEnabled(state)

    def setDownmoveEnabled(self, state: bool):
        self.downmove.setEnabled(state)

    def setRemoveEnabled(self, state: bool):
        self.remove.setEnabled(state)
        
    def upmoveEnabled(self):
        return self.upmove.isEnabled()
        
    def downmoveEnabled(self):
        return self.downmove.isEnabled()
        
    def removeEnabled(self):
        return self.remove.isEnabled()

# ======== 组件事件

# ======== 其他方法 ========