from PyQt5.QtWidgets import (QWidget, QLabel, QPushButton,
                             QHBoxLayout, QVBoxLayout)
from PyQt5.QtCore import (QSize, QMetaObject)

class QTrayIconWidget(QWidget):
    def __init__(self, parent):
        QWidget.__init__(self, parent)

        self.setMinimumSize(QSize(110, 0))
        self.setObjectName("menu_widget")
        self.verticalLayout_8 = QVBoxLayout(self)
        self.verticalLayout_8.setContentsMargins(5, 0, 5, 5)
        self.verticalLayout_8.setSpacing(5)
        self.verticalLayout_8.setObjectName("verticalLayout_8")
        self.menu_name = QLabel()
        self.menu_name.setObjectName("menu_name")
        self.menu_name.setIndent(4)
        self.verticalLayout_8.addWidget(self.menu_name)
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setSpacing(0)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.menu_mode = QPushButton()
        self.menu_mode.setMinimumSize(QSize(22, 22))
        self.menu_mode.setMaximumSize(QSize(22, 22))
        self.menu_mode.setObjectName("menu_mode")
        self.menu_mode.setProperty('is_toolbtn', True)
        self.horizontalLayout.addWidget(self.menu_mode)
        self.menu_last = QPushButton()
        self.menu_last.setMinimumSize(QSize(30, 30))
        self.menu_last.setMaximumSize(QSize(30, 30))
        self.menu_last.setObjectName("menu_last")
        self.horizontalLayout.addWidget(self.menu_last)
        self.menu_pause = QPushButton()
        self.menu_pause.setMinimumSize(QSize(30, 30))
        self.menu_pause.setMaximumSize(QSize(30, 30))
        self.menu_pause.setObjectName("menu_pause")
        self.horizontalLayout.addWidget(self.menu_pause)
        self.menu_next = QPushButton()
        self.menu_next.setMaximumSize(QSize(30, 30))
        self.menu_next.setObjectName("menu_next")
        self.horizontalLayout.addWidget(self.menu_next)
        self.menu_volume = QPushButton()
        self.menu_volume.setMinimumSize(QSize(22, 22))
        self.menu_volume.setMaximumSize(QSize(22, 22))
        self.menu_volume.setObjectName("menu_volume")
        self.menu_volume.setProperty('is_toolbtn', True)
        self.horizontalLayout.addWidget(self.menu_volume)
        self.verticalLayout_8.addLayout(self.horizontalLayout)

        self.menu_name.setText('无歌曲')

        QMetaObject.connectSlotsByName(self)

# ======== 自动关联的槽函数 ========

# ======== 自定义槽函数 ========

# ======== 组件事件

# ======== 其他方法 ========