from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import (QCoreApplication, QMetaObject)

class QMyWidget(QWidget):
    def __init__(self, parent):
        QWidget.__init__(self, parent)

        # setup ui

        _translate = QCoreApplication.translate
        # set translate

        QMetaObject.connectSlotsByName(self)

# ======== 自动关联的槽函数 ========

# ======== 自定义槽函数 ========

# ======== 组件事件

# ======== 其他方法 ========