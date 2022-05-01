from PyQt5.QtWidgets import (QWidget, QPushButton, QLabel, QSlider,
                             QVBoxLayout, QSizePolicy)
from PyQt5.QtCore import (Qt, QCoreApplication, QMetaObject, QSize, pyqtSignal, pyqtSlot)
import qtawesome as qta

class QVolumeControler(QWidget):
    volumeChanged = pyqtSignal(int)
    mutedChanged = pyqtSignal(bool)

    is_muted = False

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
        self.volume_mute.setMinimumSize(QSize(24, 24))
        self.volume_mute.setMaximumSize(QSize(24, 24))
        self.volume_mute.setProperty('is_toolbtn', True)
        self.volume_mute.setIcon(qta.icon('fa.volume-up', color='#333'))
        self.volume_mute.setToolTip('静音')
        self.volume_mute.setObjectName("volume_mute")
        self.verticalLayout_8.addWidget(self.volume_mute)

        QMetaObject.connectSlotsByName(self)

# ======== 自动关联的槽函数 ========

    # 音量变化
    @pyqtSlot(int)
    def on_volume_bar_valueChanged(self, value):
        self.set_volume_data()
        self.volumeChanged.emit(value)

    # 按下静音按钮
    @pyqtSlot()
    def on_volume_mute_clicked(self):
        self.is_muted = not self.is_muted 
        
        # 设置音量信息
        self.set_volume_data()
            
        if self.is_muted:
            self.volumeChanged.emit(0)
        else:
            self.volumeChanged.emit(self.volume_bar.value()) 
        self.mutedChanged.emit(self.is_muted)

# ======== 自定义槽函数 ========

# ======== 组件事件

# ======== 其他方法 ========

    # 获取当前音量对应图标
    def get_volume_icon(self):
        value = self.volume_bar.value()

        if value == 0:
            icon_name = 'fa.volume-off'
        elif 0 < value <= 50:
            icon_name = 'fa.volume-down'     
        else:    
            icon_name = 'fa.volume-up'
            
        if self.is_muted:
            icon = qta.icon(icon_name, 'fa.ban', options=[{'color': '#777'}, {'color': '#f33', 'offset': (0.15, 0.15), 'scale_factor': 0.8}])
        else:
            icon = qta.icon(icon_name, color='#333')
        
        return icon
    
    # 设置音量信息
    def set_volume_data(self):         
        # 音量标签
        if self.is_muted:
            value = '0'
        else:
            value = str(self.volume_bar.value())
        self.volume_lab.setText(value)
        self.volume_lab.setToolTip(value)
        self.volume_bar.setToolTip(value)
            
        # 当前音量对应图标
        icon = self.get_volume_icon()

        if self.is_muted:
            self.volume_mute.setToolTip('取消静音')
        else:         
            self.volume_mute.setToolTip('静音')   
            
        self.volume_mute.setIcon(icon)            
        self.volume_bar.setEnabled(not self.is_muted)