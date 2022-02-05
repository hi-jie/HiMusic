from PyQt5.QtWidgets import (QWidget, QPushButton, QLabel, QSlider,
                             QVBoxLayout, QSizePolicy)
from PyQt5.QtCore import (Qt, QCoreApplication, QMetaObject, QSize, pyqtSignal, pyqtSlot)
import qtawesome as qta

class QVolumeControler(QWidget):
    volumeChanged = pyqtSignal(int)
    mutedChanged = pyqtSignal(bool)

    __is_muted = False

    def __init__(self, parent):
        QWidget.__init__(self, parent)

        sizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.sizePolicy().hasHeightForWidth())
        self.setSizePolicy(sizePolicy)
        self.setMinimumSize(QSize(40, 240))
        self.setMaximumSize(QSize(40, 240))
        self.verticalLayout_8 = QVBoxLayout(self)
        self.verticalLayout_8.setContentsMargins(9, 0, 9, 5)
        self.verticalLayout_8.setSpacing(10)
        self.verticalLayout_8.setObjectName("verticalLayout_8")
        self.volume_lab = QLabel('100', self)
        self.volume_lab.setObjectName('volume_lab')
        self.volume_lab.setToolTip('100')
        self.verticalLayout_8.addWidget(self.volume_lab)
        self.volume_bar = QSlider(self)
        self.volume_bar.setMinimumSize(QSize(22, 160))
        self.volume_bar.setMaximumSize(QSize(22, 160))
        self.volume_bar.setMaximum(100)
        self.volume_bar.setProperty("value", 100)
        self.volume_bar.setOrientation(Qt.Vertical)
        self.volume_bar.setObjectName("volume_bar")
        self.verticalLayout_8.addWidget(self.volume_bar)
        self.volume_mute = QPushButton(self)
        self.volume_mute.setMinimumSize(QSize(22, 22))
        self.volume_mute.setMaximumSize(QSize(22, 22))
        self.volume_mute.setProperty('is_toolbtn', True)
        self.volume_mute.setIcon(qta.icon('fa.volume-up', color='#555'))
        self.volume_mute.setToolTip('静音')
        self.volume_mute.setObjectName("volume_mute")
        self.verticalLayout_8.addWidget(self.volume_mute)

        QMetaObject.connectSlotsByName(self)

# ======== 自动关联的槽函数 ========

    @pyqtSlot(int)
    def on_volume_bar_valueChanged(self, value):
        self.change_mute_icon()
        self.volumeChanged.emit(value)

    @pyqtSlot()
    def on_volume_mute_clicked(self):
        self.__is_muted = not self.__is_muted

        if self.__is_muted:
            self.volume_lab.setText('0')
            self.volume_mute.setToolTip('取消静音')
            self.volume_mute.setIcon(qta.icon('fa.volume-off', color='#555'))
            self.volume_bar.setEnabled(False)
            self.volumeChanged.emit(0)
            self.volume_mute.setStyleSheet('''
#volume_mute {background-color: #ddd;}
#volume_mute:hover {background-color: #ccc;}
''')
        else:         
            self.change_mute_icon()
            self.volume_mute.setToolTip('静音')   
            self.volume_bar.setEnabled(True)  
            self.volumeChanged.emit(self.volume_bar.value())
            self.volume_mute.setStyleSheet('''
#volume_mute {background-color: white;}
#volume_mute:hover {background-color: #ddd;}
''')

        self.mutedChanged.emit(self.__is_muted)

# ======== 自定义槽函数 ========

# ======== 组件事件

# ======== 其他方法 ========

    def change_mute_icon(self):
        value = self.volume_bar.value()

        self.volume_lab.setText(str(value))
        self.volume_lab.setToolTip(str(value))
        self.volume_bar.setToolTip(str(value))

        color = '#555'

        if value == 0:
            self.volume_mute.setIcon(qta.icon('fa.volume-off', color=color))
        elif 0 < value <= 50:
            self.volume_mute.setIcon(qta.icon('fa.volume-down', color=color))        
        else:    
            self.volume_mute.setIcon(qta.icon('fa.volume-up', color=color))