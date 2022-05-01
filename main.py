import sys
from os import walk, system, getcwd, startfile
from re import search, fullmatch, I
from json import load, dump

from PyQt5.QtWidgets import (QApplication, QMainWindow, QLabel, QSlider,
                             QListView, 
                             QTableWidgetItem,
                             QGraphicsDropShadowEffect, QGraphicsBlurEffect,
                             QFileDialog, QMessageBox,
                             QSystemTrayIcon, QMenu, QAction, QWidgetAction,
                             QSizePolicy)
from PyQt5.QtCore import (Qt, QSize, QPoint, QMetaObject, pyqtSignal, pyqtSlot, QThread, QUrl, QTimer, QDir, QEvent, QSharedMemory)
from PyQt5.QtGui import (QIcon, QFont, QImage, QPixmap, QPalette, QBrush)
from PyQt5.QtMultimedia import (QMediaPlayer, QMediaPlaylist, QMediaContent)
from PyQt5.QtWinExtras import (QWinThumbnailToolBar, QWinThumbnailToolButton)
from PyQt5.Qt import QPropertyAnimation
import qtawesome as qta
from PIL import ImageQt, ImageFilter

from widgets import ui_MainWindow, TrayIconWidget, VolumeControler
from app import mapi

class MainWindow(QMainWindow):
    result_getters = [] # 获取搜索结果线程集
    img_getters = [] # 获取图片线程集
    music_url_getters = [] # 获取音乐URL线程
    music_content_getters = [] # 获取音乐线程
    lrc_getters = [] # 获取歌词线程
    
    engines = {} # 搜索引擎
    __playlist = [] # 播放列表，不重复的音乐名有序集合

    __cur_pos = '' # 进度显示
    __duration = '' # 总长度显示

    __is_moving = False # 是否正在拖动
    __move_pos = None # 拖动
    __is_resizing = False
    __width = 0 # 窗体理论宽度，受窗体最小宽度限制
    __height = 0 # 窗体理论高度，受窗体最小高度限制
    __last_pos = QPoint(0, 0) # 调整大小时的上一个位置

    lrcs = [['无歌词', 0]] # 歌词
    lrc_height = 30 # 歌词高度
    lrcs_top = 2 # 歌词距离顶部的个数
    __lrc_index = 0 # 当前歌词序号
    lrcs_animation = None # 歌词动画
    __scrolling_timers = [] # 正在拖动歌词的定时器们

    current_music_url = '' # 当前音乐网址

    toolbtn_color = '#333' # 工具按钮的颜色

    play_modes = (('fa.circle-o', '播放一次'), 
                  ('fa.repeat', '单曲循环'), 
                  ('fa.sort-amount-asc', '顺序播放'), 
                  ('fa.refresh', '列表循环'), 
                  ('fa.random', '随机播放'))

    def __init__(self):
        QMainWindow.__init__(self)

        # 设置 UI
        self.ui = ui_MainWindow.Ui_MainWindow()
        self.ui.setupUi(self)

        self.setWindowFlags(Qt.FramelessWindowHint) # 窗口去边框
        self.setWindowIcon(QIcon('imgs/ico.ico'))

        self.set_effect() # 生成特效
        self.set_shadow() # 设置窗口阴影

        self.setup_system_tray() # 设置托盘图标
        self.setup_toolbar() # 设置任务栏缩略图工具按钮
        self.setup_menus() # 设置音量菜单
        self.setup_ui() # 组件初始化
        self.setup_cache() # 设置缓存
        self.setup_settings() # 设置
        self.setup_engine() # 导入引擎
        self.setup_media() # 设置播放器
        self.setup_timer() # 设置定时器
        self.setup_animation() # 设置歌词滚动动画  
        self.setup_slots() # 组件槽连接
        self.setup_events() # 组件事件连接

    # 设置UI
    def setup_ui(self):  
        # 窗口背景自动填充，不可透明
        self.ui.main_frame.setAutoFillBackground(True)
        
        # 设置搜索引擎列表模型
        self.ui.input_engine.setView(QListView())
        self.ui.settings_default_engine.setView(QListView())
        self.ui.settings_lrcs_distance.setView(QListView())
        
        # 搜索栏搜索按钮
        self.ui.input_ok.setIcon(qta.icon('fa.search', color='#888'))
        self.ui.input_ok.setCursor(Qt.PointingHandCursor)
        
        # 菜单栏图标
        font = qta.font('fa', 14)
        self.ui.logo.setText('Hi 音乐')
        self.ui.logo.setFont(font)
        self.ui.sidebar.item(0).setText(chr(0xf015) + '      首页     ')
        self.ui.sidebar.item(1).setText(chr(0xf002) + '      搜索     ')
        self.ui.sidebar.item(2).setText(chr(0xf0db) + '      歌词     ')
        self.ui.sidebar.item(3).setText(chr(0xf08a) + '   我的收藏 ')
        self.ui.sidebar.item(4).setText(chr(0xf03a) + '   播放列表 ')
        self.ui.sidebar.item(5).setText(chr(0xf013) + '      设置     ')
        self.ui.sidebar.item(0).setFont(font)
        self.ui.sidebar.item(1).setFont(font)
        self.ui.sidebar.item(2).setFont(font)
        self.ui.sidebar.item(3).setFont(font)
        self.ui.sidebar.item(4).setFont(font)
        self.ui.sidebar.item(5).setFont(font)
      
        # 菜单栏选中首页
        self.ui.sidebar.setCurrentRow(0)
        
        # 首页“上次在听”
        self.ui.last_song.horizontalHeader().setVisible(False)
        self.ui.last_song.setRowCount(1) # 一行
        self.ui.last_song.verticalHeader().setDefaultSectionSize(50) # 高50px
        self.ui.last_song.setMinimumHeight(52)
        self.ui.last_song.setMaximumHeight(52)

        color = '#333'
        self.ui.last_song_play.setIcon(qta.icon('fa.play-circle-o', color=color))
        self.ui.last_playlist_addall.setIcon(qta.icon('fa.plus', color=color))

        self.ui.last_song_fold.setIcon(qta.icon('fa.angle-up', color=color))
        self.ui.last_song_fold.fold_widget = self.ui.last_song
        
        # 首页“上次播放列表”
        self.ui.last_playlist.verticalHeader().setDefaultSectionSize(50) # 高50px
        self.ui.last_playlist_fold.setIcon(qta.icon('fa.angle-up', color=color))
        self.ui.last_playlist_fold.fold_widget = self.ui.last_playlist
        
        # 收藏列表
        self.ui.collections_view.verticalHeader().setDefaultSectionSize(50) # 高50px
        self.ui.collections_view_editbar.bind_table(self.ui.collections_view)
        
        # 播放列表
        self.ui.playlist_view_editbar.bind_table(self.ui.playlist_view)

        # 工具按钮图标
        color = self.toolbtn_color
        self.ui.mmode.setIcon(qta.icon(self.play_modes[1][0], color=color))
        self.menu_widget.menu_mode.setIcon(qta.icon(self.play_modes[1][0], color=color))
        self.ui.mdownload.setIcon(qta.icon('fa.download', color=color))
        self.ui.mmv.setIcon(qta.icon('fa.caret-square-o-right', color=color))
        self.ui.mdetail.setIcon(qta.icon('fa.ellipsis-h', color=color))
        self.ui.mcollect.setIcon(qta.icon('fa.heart-o', color=color))
        self.ui.mvolume.setIcon(qta.icon('fa.volume-up', color=color))
        self.menu_widget.menu_volume.setIcon(qta.icon('fa.volume-up', color=color))
        self.ui.mplaylist.setIcon(qta.icon('fa.list-ul', color=color))
        self.ui.more.setIcon(qta.icon('fa.bars', color=color))

        self.ui.mmv.setVisible(False)
        self.ui.mdetail.setVisible(False)

        # 小图片
        self.ui.mimage.setCursor(Qt.PointingHandCursor)
        
        # 歌词列表字体变大
        list_font = QFont('', 12)
        self.ui.lrcs_view.setFont(list_font)

        # 初始化歌词
        self.insert_lrcbox([['无歌词', 0]])
        
        # 设置
        self.ui.settings_close_trayicon.setCursor(Qt.PointingHandCursor)

        self.ui.settings_appicon.setPixmap(QPixmap('imgs/ico.ico'))

        self.ui.settings_download_path_choose.setIcon(qta.icon('fa.folder-open-o', color=color))
        self.ui.settings_download_cache_open.setIcon(qta.icon('fa.folder-open-o', color=color))
        self.ui.settings_download_cache_clear.setIcon(qta.icon('fa.trash-o', color=color))
        
    # 设置缓存
    def setup_cache(self):  
        # 初始化“上次在听”
        try:
            datas = helper.cache['last_song']
            self.insert_songs_datas(self.ui.last_song, datas, 0)
            self.ui.last_song.itemPlay.connect(self.music_selected) # 选中上次播放
        except:
            self.ui.last_song.setItem(0, 2, QTableWidgetItem('上次无在听歌曲'))
            self.ui.last_song_play.setEnabled(False) # 禁用播放
            
        self.ui.last_song.setItem(0, 0, QTableWidgetItem(''))
        
        # 初始化“上次的播放列表”
        try:
            datas = helper.cache['last_playlist']
            if not datas:
                raise Exception()
            
            self.ui.last_playlist.setRowCount(len(datas))
            for i, data in enumerate(datas):
                self.insert_songs_datas(self.ui.last_playlist, data, i)
                
            self.ui.last_playlist.itemPlay.connect(self.music_selected) # 选中上次播放列表
        except:
            self.ui.last_playlist.setMaximumHeight(52)
            self.ui.last_playlist.horizontalHeader().setVisible(False)
            self.ui.last_playlist.setRowCount(1)
            self.ui.last_playlist.setItem(0, 2, QTableWidgetItem('上次无播放列表'))
            self.ui.last_playlist.setItem(0, 0, QTableWidgetItem(''))
            
            self.ui.last_playlist_addall.setEnabled(False) # 禁用添加到播放列表
            
        # 初始化“我的收藏”
        datas = helper.cache['collections']
        
        self.ui.collections_view.setRowCount(len(datas))
        for i, data in enumerate(datas):
            self.insert_songs_datas(self.ui.collections_view, data, i)
            
        self.ui.collections_view.itemPlay.connect(self.music_selected)

    # 设置
    def setup_settings(self):
        settings = helper.settings
        # QSS
        qss = helper.qss
        self.setStyleSheet(''.join(qss))
        
        # 关闭按钮最小化到托盘 
        close_trayicon = settings['general'].setdefault('close_trayicon', True)
        self.ui.settings_close_trayicon.setChecked(close_trayicon)
        QApplication.setQuitOnLastWindowClosed(not close_trayicon)
        
        # 下载地址
        self.ui.settings_download_path_edit.setText(settings['download'].setdefault('path', ''))

        # 歌词高度
        heights = [['小', 22], ['中', 30], ['大', 37]]
        index = helper.settings['lrcs'].setdefault('distance', 1)
        for s, v in heights:
            self.ui.settings_lrcs_distance.addItem(s, v)
        self.ui.settings_lrcs_distance.setCurrentIndex(index)
        self.lrc_height = heights[index][1]

    # 组件槽连接
    def setup_slots(self): 
        # 自动连接       
        QMetaObject.connectSlotsByName(self.ui.centralwidget)
        
        self.ui.min_win.clicked.connect(self.showMinimized) # 窗口最小化
        self.ui.close_win.clicked.connect(self.close)
        
        self.ui.input_engine.currentIndexChanged[int].connect(self.search) # 搜索引擎切换
        self.ui.input_entry.returnPressed.connect(self.search) # 搜索框按下回车
        self.ui.input_ok.clicked.connect(self.search) # 搜索按钮按下

        self.ui.mpause.clicked.connect(self.change_player_state) # 界面点击播放/暂停
        self.menu_widget.menu_pause.clicked.connect(self.change_player_state) # 托盘点击播放/暂停
        self.toolbar_pause.clicked.connect(self.change_player_state)

        self.ui.last_song_fold.clicked.connect(self.on_fold_clicked) # 收起/展开上次在听
        self.ui.last_playlist_fold.clicked.connect(self.on_fold_clicked) # 收起/展开上次播放列表

        self.ui.results_view.itemPlay.connect(self.music_selected) # 选中搜索结果歌曲
        self.ui.playlist_view.itemPlay.connect(self.music_selected) # 选中播放列表歌曲

        self.ui.mlast.clicked.connect(self.previous) # 界面点击上一曲
        self.menu_widget.menu_last.clicked.connect(self.previous) # 托盘点击上一曲
        self.toolbar_last.clicked.connect(self.previous) # 任务栏缩略图工具栏点击上一曲
        self.ui.mnext.clicked.connect(self.next) # 界面点击下一曲
        self.menu_widget.menu_next.clicked.connect(self.next) # 托盘点击下一曲
        self.toolbar_next.clicked.connect(self.next) # 任务栏缩略图工具栏点击下一曲

        self.ui.mmode.clicked.connect(self.change_playbackmode) # 界面点击播放模式
        self.menu_widget.menu_mode.clicked.connect(self.change_playbackmode) # 托盘点击播放模式

        self.ui.mvolume.clicked.connect(self.on_mvolume_clicked) # 界面调整音量
        self.menu_widget.menu_volume.clicked.connect(self.on_menu_volume_clicked) # 托盘调整音量

        self.volume_widget.volumeChanged.connect(self.on_volume_widget_volumeChanged)

        self.player.positionChanged.connect(self.position_changed) # 播放器进度变化
        self.player.durationChanged.connect(self.__durationchanged) # 播放器长度变化
        self.player.stateChanged.connect(self.state_changed) # 播放器状态变化

        self.playlist.currentIndexChanged.connect(self.music_changed) # 播放器音乐变化
        
        # 添加到播放列表
        self.ui.last_song.itemAdd.connect(self.add_to_playlist)
        self.ui.last_playlist.itemAdd.connect(self.add_to_playlist)
        self.ui.results_view.itemAdd.connect(self.add_to_playlist)
        self.ui.collections_view.itemAdd.connect(self.add_to_playlist)
        self.ui.playlist_view.itemAdd.connect(self.add_to_playlist)
        
        # 收藏歌曲
        self.ui.last_song.itemCollect.connect(self.collect)
        self.ui.last_playlist.itemCollect.connect(self.collect)
        self.ui.results_view.itemCollect.connect(self.collect)
        self.ui.collections_view.itemCollect.connect(self.collect)
        self.ui.playlist_view.itemCollect.connect(self.collect)
        self.ui.mcollect.clicked.connect(self.collect) # 控制框点击收藏

    # 组件事件连接        
    def setup_events(self):
        self.ui.main.mousePressEvent = self.on_main_mousePressEvent # 窗口边缘按下
        self.ui.main.mouseMoveEvent = self.on_main_mouseMoveEvent # 调整窗口大小
        self.ui.main.mouseReleaseEvent = self.on_main_mouseReleaseEvent # 窗口边缘松开
        
        self.ui.logo.mousePressEvent = self.on_title_mousePressEvent # logo 按下
        self.ui.logo.mouseMoveEvent = self.on_title_mouseMoveEvent  # logo 拖动
        self.ui.logo.mouseReleaseEvent = self.on_title_mouseReleaseEvent # logo 松开
        
        self.ui.title.mousePressEvent = self.on_title_mousePressEvent # title 按下
        self.ui.title.mouseMoveEvent = self.on_title_mouseMoveEvent  # title 拖动
        self.ui.title.mouseReleaseEvent = self.on_title_mouseReleaseEvent # title 松开
        
        self.ui.bar.mousePressEvent = self.on_bar_mousePressEvent # 进度条点击跳转
        
        self.ui.mimage.mouseReleaseEvent = self.on_mimage_mouseReleaseEvent # 小图片按下
        
        self.ui.lrcs_view_content.mouseDoubleClickEvent = self.on_lrcs_view_content_mouseDoubleClickEvent # 歌词容器双击
        
    # 定义特效
    def set_effect(self):
        self.effect_shadow = QGraphicsDropShadowEffect(self) # 创建阴影
        self.effect_shadow.setOffset(0, 0) # 偏移
        self.effect_shadow.setBlurRadius(10) # 阴影半径
        self.effect_shadow.setColor(Qt.black) # 阴影颜色
        
        self.effect_blur = QGraphicsBlurEffect(self)
        self.effect_blur.setBlurRadius(100)
    
    # 设置窗口阴影
    def set_shadow(self):
        self.setAttribute(Qt.WA_TranslucentBackground)   #将窗口设置为透明
        self.setGraphicsEffect(self.effect_shadow) # 将设置套用到窗口中
        
    # 导入引擎
    def setup_engine(self):
        for index, engine in enumerate(helper.engines.values()):        
            self.ui.input_engine.addItem(engine.name, engine)       
            self.ui.settings_default_engine.addItem(engine.name, engine.pre)

            if engine.pre == helper.default_engine.pre:
                self.ui.input_engine.setCurrentIndex(index)
                self.ui.settings_default_engine.setCurrentIndex(index)

    # 设置播放器
    def setup_media(self):
        self.playlist = QMediaPlaylist(self)
        self.playlist.setPlaybackMode(QMediaPlaylist.CurrentItemInLoop)
        self.player = QMediaPlayer(self)
        self.player.setPlaylist(self.playlist)
        
    # 设置托盘图标
    def setup_system_tray(self):
        self.menu_widget = TrayIconWidget.QTrayIconWidget(self)
        self.menu_widget.setObjectName('menu_widget')

        self.act_state = QWidgetAction(self.menu_widget)
        self.act_state.setDefaultWidget(self.menu_widget)

        color = '#333'
        self.act_open = QAction(qta.icon('fa.window-maximize', color=color), '打开', self)
        self.act_open.triggered.connect(self.showNormal)
        self.act_quit = QAction(qta.icon('fa.power-off', color='#f33'), '退出', self)
        self.act_quit.triggered.connect(self.app_quit)

        self.tray_icon_menu = QMenu(self)
        self.tray_icon_menu.addAction(self.act_state)
        self.tray_icon_menu.addSeparator()
        self.tray_icon_menu.addAction(self.act_open)
        self.tray_icon_menu.addAction(self.act_quit)

        self.tray_icon = QSystemTrayIcon()
        self.tray_icon.setObjectName('tray_icon')
        self.tray_icon.setContextMenu(self.tray_icon_menu)
        self.tray_icon.setIcon(QIcon('imgs/ico.ico'))
        self.tray_icon.setToolTip('Hi音乐\n无歌曲')
        self.tray_icon.activated.connect(self.on_tray_icon_activated)
        self.tray_icon.show()

    # 任务栏缩略图工具条
    def setup_toolbar(self):
        self.toolbar = QWinThumbnailToolBar(self)

        color = 'white'

        # 上一首，播放/暂停，下一首按钮
        self.toolbar_last = QWinThumbnailToolButton(self.toolbar)
        self.toolbar_last.setToolTip('上一首')
        self.toolbar_last.setIcon(qta.icon('fa.step-backward', color=color))
        # self.toolbar_last.clicked.connect(self.set_prev)
        self.toolbar.addButton(self.toolbar_last)

        self.toolbar_pause = QWinThumbnailToolButton(self.toolbar)
        self.toolbar_pause.setToolTip('播放')
        self.toolbar_pause.setProperty('status', 0)
        self.toolbar_pause.setIcon(qta.icon('fa.play', color=color))
        # self.toolbar_pause.clicked.connect(self.set_control)
        self.toolbar.addButton(self.toolbar_pause)

        self.toolbar_next = QWinThumbnailToolButton(self.toolbar)
        self.toolbar_next.setToolTip('下一首')
        self.toolbar_next.setIcon(qta.icon('fa.step-forward', color=color))
        # self.toolbar_next.clicked.connect(self.set_next)
        self.toolbar.addButton(self.toolbar_next)

    # 设置菜单
    def setup_menus(self):
        # 音量菜单
        self.volume_widget = VolumeControler.QVolumeControler(self)
        self.volume_widget.setObjectName('volume_widget')

        self.act_volume = QWidgetAction(self.volume_widget)
        self.act_volume.setDefaultWidget(self.volume_widget)

        self.volume_menu = QMenu(self)
        self.volume_menu.addAction(self.act_volume)

        # 标题栏“更多”菜单
        color = '#333'
        self.act_settings = QAction(qta.icon('fa.cog', color=color), '设置', self)
        self.act_settings.triggered.connect(lambda: self.change_tab(5))

        self.more_menu = QMenu(self)
        self.more_menu.addAction(self.act_settings)

    # 设置定时器
    def setup_timer(self):
        self.timer = QTimer()
        self.timer.stop()
        self.timer.setInterval(400)
        self.timer.timeout.connect(self.synchronize_lrcs) # 连接歌词同步

    # 设置歌词滚动动画
    def setup_animation(self):
        self.lrcs_animation = QPropertyAnimation(self.ui.lrcs_view_content, b'pos', self)
        self.lrcs_animation.setDuration(150)

# ======== 自动关联的槽函数 ========

    # 标题栏“更多”按钮
    @pyqtSlot()
    def on_more_clicked(self):
        pos = self.ui.main.mapToGlobal(self.ui.more.pos())
        x = pos.x()
        y = pos.y() + self.ui.more.height() + 5
        self.more_menu.exec_(QPoint(x, y))

    # 关闭窗口
    @pyqtSlot()
    def on_close_win_clicked(self):
        self.close()
    
    # 窗口最大化/还原窗口
    @pyqtSlot()
    def on_max_win_clicked(self):
        if self.isMaximized():
            self.ui.main_layout.setContentsMargins(10, 10, 10, 10) # 增加边距
            self.ui.max_win.setStyleSheet('''
#max_win {image: url("imgs/max.svg")}
#max_win:hover {image: url("imgs/max1.svg")}
''')
            self.ui.main_frame.setStyleSheet('#main_frame {border-radius: 3px;}')
            self.showNormal() # 正常大小
        else:
            self.ui.main_layout.setContentsMargins(0, 0, 0, 0) # 取消边距
            self.ui.max_win.setStyleSheet('''
#max_win {image: url("imgs/res.svg")}
#max_win:hover {image: url("imgs/res1.svg")}
''')
            self.ui.main_frame.setStyleSheet('#main_frame {border-radius: 0;}')
            self.showMaximized() # 最大化

    # 切换搜索引擎
    @pyqtSlot(int)
    def on_input_engine_currentIndexChanged(self, index):
        engine = self.ui.input_engine.currentText()
        self.ui.input_engine.setToolTip(engine)
            
    # 切换菜单
    @pyqtSlot(int)
    def on_sidebar_currentRowChanged(self, index):
        self.ui.stacked_tab.setCurrentIndex(index)

    # 拖动进度条
    @pyqtSlot()
    def on_bar_sliderReleased(self):
        position = self.ui.bar.value()
        self.player.setPosition(position)        
        
    # 设置中选择下载路径
    @pyqtSlot()
    def on_settings_download_path_choose_clicked(self):
        cur_path = QDir.currentPath()
        title = '打开'
        path = QFileDialog.getExistingDirectory(self, title, cur_path, QFileDialog.ShowDirsOnly)
        
        self.ui.settings_download_path_edit.setText(path)        

    # “下载”按钮按下
    @pyqtSlot()
    def on_mdownload_clicked(self):
        # 获取完音乐
        def music_content_finished(content):
            name = self.ui.mname.text()

            if not content:
                QMessageBox.warning(self, '下载失败', '下载失败，请重试。')
                return
            
            path = self.ui.settings_download_path_edit.text()
            if not path:
                path = 'musics/'
                
            if not path.endswith(('/', '\\', '\\\\')):
                path = path + '/'
                
            file = f'{path}{name}.mp3'

            try:
                with open(file, 'wb') as f:
                    f.write(content)
            except:
                QMessageBox.warning(self, '下载失败', '下载失败，请检查下载路径是否正确。')                
                return

            self.ui.mdownload.setStyleSheet('''
#mdownload {background: #ddd;}
#mdownload:hover {background: #ccc;}
''')
            QMessageBox.information(self, '下载成功', f'下载成功：\n{file}')

        # 当前音乐的 URL
        url = self.current_music_url
        
        if not url:
            QMessageBox.warning(self, '无歌曲', '当前无播放歌曲。')
            return
        
        # 获取音乐
        music_content_getter = SubThread(task=SubThread.get_music_content, data=url)
        music_content_getter.music_content_finished.connect(music_content_finished)
        self.music_content_getters.append(music_content_getter)
        music_content_getter.start()

    # “播放列表”按钮按下
    @pyqtSlot()
    def on_mplaylist_clicked(self):
        self.ui.sidebar.setCurrentRow(4)
        self.ui.stacked_tab.setCurrentIndex(4)

    # 音量调整
    @pyqtSlot(int)
    def on_volume_widget_volumeChanged(self, value):
        self.player.setVolume(value)
        # 当前音量对应图标
        icon = self.volume_widget.get_volume_icon()   
           
        self.ui.mvolume.setIcon(icon)
        self.menu_widget.menu_volume.setIcon(icon)
        
        if self.volume_widget.is_muted:
            self.ui.mvolume.setToolTip('音量 0') 
        else:
            self.ui.mvolume.setToolTip(f'音量 {value}')  

    # 静音
    @pyqtSlot(bool)
    def on_volume_widget_mutedChanged(self, is_muted):
        self.player.setMuted(is_muted)
            
    # “上次在听”播放
    @pyqtSlot()
    def on_last_song_play_clicked(self):
        self.add_media(self.ui.last_song.get_datas(0), play=True)
            
    # “上次的播放列表”添加全部
    @pyqtSlot()
    def on_last_playlist_addall_clicked(self):
        for row in range(self.ui.last_playlist.rowCount()):
            datas = self.ui.last_playlist.get_datas(row)
            self.add_media(datas)

    # 删除列表项
    @pyqtSlot()
    def on_playlist_view_editbar_removed(self):
        playlist_view = self.ui.playlist_view
        rows = playlist_view.get_selected_rows()
        current_index = self.playlist.currentIndex()

        # 删除行
        for row in rows[::-1]:
            del self.__playlist[row]
            self.playlist.removeMedia(row)
            self.ui.playlist_view.remove_item(row)
            if row < current_index:
                current_index -= 1
                
        if current_index >= self.ui.playlist_view.rowCount():
            current_index -= 1
            self.player.stop()

        # 播放
        self.playlist.setCurrentIndex(current_index)
        self.player.play()        
        
        # 刷新
        if self.ui.playlist_view.rowCount() != 0:
            self.refresh_songsui(self.__playlist[current_index][1])

    # 列表项上移
    @pyqtSlot()
    def on_playlist_view_editbar_upmoved(self):
        index = self.ui.playlist_view.get_selected_rows()[0]
        self.move_playlist_view_item(index, index - 1)

    # 列表项下移
    @pyqtSlot()
    def on_playlist_view_editbar_downmoved(self):
        index = self.ui.playlist_view.get_selected_rows()[0]
        self.move_playlist_view_item(index, index + 1)

    # 本地歌曲
    @pyqtSlot(list)
    def on_playlist_view_editbar_fromLocal(self, datas):
        for data in datas:
            self.add_media(data)

    # 删除收藏列表项
    @pyqtSlot()
    def on_collections_view_editbar_removed(self):
        table = self.sender().table
        rows = table.get_selected_rows()

        for row in rows[::-1]:
            table.remove_item(row)
        
    # 收藏列表项上移
    @pyqtSlot()
    def on_collections_view_editbar_upmoved(self):
        table = self.sender().table
        index = table.get_selected_rows()[0]
        table.move_item(index, index - 1)
        
    # 收藏列表项下移
    @pyqtSlot()
    def on_collections_view_editbar_downmoved(self):
        table = self.sender().table
        index = table.get_selected_rows()[0]
        table.move_item(index, index + 1)
        
    # 从本地选择
    @pyqtSlot(list)
    def on_collections_view_editbar_fromLocal(self, datas):
        table = self.sender().table
        for data in datas:
            table.setRowCount(table.rowCount() + 1)
            self.insert_songs_datas(table, data, table.rowCount() - 1)

    # 打开缓存文件夹
    @pyqtSlot()
    def on_settings_download_cache_open_clicked(self):
        system(f'explorer.exe "{getcwd()}\\datas\\cache\\"')

    # 清除缓存
    @pyqtSlot()
    def on_settings_download_cache_clear_clicked(self):
        commands = [
            'cd datas/cache',
            'del *.* /q'
        ]
        system('&&'.join(commands))


# ======== 自定义槽函数 ========

    # 退出程序
    def app_quit(self):
        self.close()
        app.quit()

    # 界面音量按钮点击
    def on_mvolume_clicked(self):
        sender = self.sender()
        pos = sender.pos()
        global_pos = self.ui.main.mapToGlobal(pos)

        self.volume_controler_pop(global_pos)

    # 托盘菜单音量按钮点击
    def on_menu_volume_clicked(self):
        sender = self.sender()
        pos = sender.pos()
        global_pos = self.menu_widget.mapToGlobal(pos)

        self.volume_controler_pop(global_pos)

    # 托盘图标点击
    def on_tray_icon_activated(self, reason):
        if (reason == QSystemTrayIcon.Trigger) and (self.isHidden() or self.isMinimized() or not self.isActiveWindow()):
            # 如果最大化则还原
            if self.isMaximized():
                self.on_max_win_clicked()

            # 正常显示
            self.showNormal()

            # 刷新界面
            # QApplication.processEvents()
        
    # 搜索
    def search(self):
        def result_finished(result):
            if not result:
                title = '错误'
                warn = '搜索出错，请重试。'
                QMessageBox.warning(self, title, warn)   

                return
                            
            # 插入搜索结果
            self.insert_search_result(result)

        keyword = self.ui.input_entry.text()
        # 是否含有非空白符
        if search(r'\S', keyword) is None:
            self.ui.results_view.clearContents()
            return

        # 切换引擎
        engine = self.ui.input_engine.currentData()
        helper.engine = engine

        # 清除所有歌
        self.ui.results_view.clearContents()
        
        # 选中搜索结果列表
        self.ui.sidebar.setCurrentRow(1)
        self.ui.stacked_tab.setCurrentIndex(1)

        # 搜索
        result_getter = SubThread(task=SubThread.get_result, keyword=keyword)
        result_getter.result_finished.connect(result_finished)
        self.result_getters.append(result_getter)
        result_getter.start()

    # 选中歌曲
    def music_selected(self, row):
        widget = self.sender()

        # 初始化数据
        datas = widget.get_datas(row)
            
        # 添加音乐
        self.add_media(datas, play=True)
        
    # 搜索结果添加到列表
    def add_to_playlist(self, rows):
        sender = self.sender()
        if sender == self.ui.playlist_view:
            QMessageBox.information(self, '已添加', '歌曲已在播放列表中。')
            return
            
        for row in rows:
            self.add_media(sender.get_datas(row))
        
    # 添加到收藏
    def collect(self):
        sender = self.sender()
        collections_view = self.ui.collections_view
                
        # 已收藏
        collected = []
        for row in range(collections_view.rowCount()):
            collected.append(collections_view.get_datas(row)[6])
        
        # 选中歌曲
        datas = []
        if sender == self.ui.mcollect:
            if self.__playlist:
                datas = [self.__playlist[self.playlist.currentIndex()][1]]
                # 是否已收藏过
                if datas[0][6] in collected:
                    self.ui.collections_view.remove_item(collected.index(datas[0][6]))
                    self.refresh_mcollect_status() # 刷新控制栏收藏按钮状态
                    QMessageBox.warning(self, '已取消收藏', '已取消收藏！')

                    return

            else:
                QMessageBox.warning(self, '无歌曲', '当前无播放歌曲。')
                return
        else:
            rows = sender.get_selected_rows()
            for row in rows:
                datas.append(sender.get_datas(row))
                
        # 收藏
        collections = []
        for data in datas:
            # 是否已收藏过
            if data[6] in collected:
                continue
            collections_view.setRowCount(collections_view.rowCount() + 1)
            self.insert_songs_datas(collections_view, data, collections_view.rowCount() - 1)
            collections.append(f'{data[0]} - {data[1]}')
                    
        self.refresh_mcollect_status() # 刷新控制栏收藏按钮状态

        if collections:
            QMessageBox.information(self, '已收藏', '已收藏！\n' + '\n'.join(collections))
        else:
            QMessageBox.information(self, '已收藏', '歌曲已在收藏列表中。')

    # 按下播放/暂停
    def change_player_state(self):
        if self.player.state() == QMediaPlayer.PlayingState:
            self.player.pause()
        else:
            self.player.play()

    # 切换播放模式
    def change_playbackmode(self):
        mode = self.playlist.playbackMode() # 当前模式
        mode = (mode + 1) % 5 # 目标模式

        # 设置模式
        self.playlist.setPlaybackMode(mode)

        # 设置按钮
        mode_data = self.play_modes[mode]
        self.ui.mmode.setIcon(qta.icon(mode_data[0], color=self.toolbtn_color))
        self.menu_widget.menu_mode.setIcon(qta.icon(mode_data[0], color=self.toolbtn_color))
        self.ui.mmode.setToolTip(mode_data[1])

    # 播放器状态变化
    def state_changed(self, state):
        color = 'white'
        if state == QMediaPlayer.PlayingState:
            style_sheet = '''
#mpause, #menu_pause {border-image: url("imgs/pause.svg");}
#mpause:hover, #menu_pause:hover {border-image: url("imgs/pause1.svg");}
'''
            self.ui.mpause.setStyleSheet(style_sheet)
            self.menu_widget.menu_pause.setStyleSheet(style_sheet)
            self.toolbar_pause.setIcon(qta.icon('fa.pause', color=color))
        else:
            style_sheet = '''
#mpause, #menu_pause {border-image: url("imgs/play.svg");}
#mpause:hover, #menu_pause:hover {border-image: url("imgs/play1.svg");}
'''
            self.ui.mpause.setStyleSheet(style_sheet)
            self.menu_widget.menu_pause.setStyleSheet(style_sheet)
            self.toolbar_pause.setIcon(qta.icon('fa.play', color=color))

    # 播放器进度变化
    def position_changed(self, position):
        # 如果正在拖动进度条调整进度
        if self.ui.bar.isSliderDown():
            return

        # 同步进度
        self.ui.bar.setSliderPosition(position)

        self.__cur_pos = format_position(position)
        self.ui.position_label.setText(self.__cur_pos + '/' + self.__duration)

    # 播放器文件长度变化，即切换音乐
    def __durationchanged(self, duration):
        self.ui.bar.setMaximum(duration)
      
        self.__duration = format_position(duration)

    # 播放器音乐变化
    def music_changed(self, position):
        index = self.playlist.currentIndex()
        datas = self.__playlist[index][1]

        # 选中行
        self.ui.playlist_view.selectRow(index)

        # 刷新歌曲信息显示
        self.refresh_songsui(datas)

    # 上次在听/上次播放列表收起
    def on_fold_clicked(self):
        sender = self.sender()
        if sender.fold_widget.isVisible():
            sender.setIcon(qta.icon('fa.angle-down', color='#333'))
            sender.setToolTip('展开')
        else:
            sender.setIcon(qta.icon('fa.angle-up', color='#333'))
            sender.setToolTip('收起')
        sender.fold_widget.setVisible(not sender.fold_widget.isVisible())

# ======== 组件事件 ========

    def showEvent(self, event):
        QMainWindow.showEvent(self, event)
        if not self.toolbar.window():
            # 必须等窗口显示后设置才有效，或者通过软件流程在适当的时候设置也可以
            self.toolbar.setWindow(self.windowHandle())

    #顶层窗口激活状态改变
    def changeEvent(self, event):
        self.repaint()

    # 窗口关闭事件
    def closeEvent(self, event):
        # 设置
        helper.settings['general']['close_trayicon'] = self.ui.settings_close_trayicon.isChecked() # 关闭时最小化到托盘
        helper.settings['general']['default_engine'] = self.ui.settings_default_engine.currentData() # 默认搜索引擎
        helper.settings['download']['path'] = self.ui.settings_download_path_edit.text() # 下载地址
        helper.settings['lrcs']['distance'] = self.ui.settings_lrcs_distance.currentIndex() # 歌词高度
        
        helper.save_settings() # 保存设置
        
        # 缓存    
        try:
            helper.cache['last_song'] = self.__playlist[self.playlist.currentIndex()][1] # 上次在听
        except:
            helper.cache['last_song'] = []
            
        try:
            helper.cache['last_playlist'] = list(zip(*self.__playlist))[1]
        except:
            helper.cache['last_playlist'] = []
            
        helper.cache['collections'] = []
        for row in range(self.ui.collections_view.rowCount()):
            helper.cache['collections'].append(self.ui.collections_view.get_datas(row))
            
        helper.save_cache() # 保存缓存

    # 窗口边缘按下
    def on_main_mousePressEvent(self, event):
        if self.isMaximized() or self.isFullScreen():
            return

        if event.button() == Qt.LeftButton:
            self.__width = self.width()
            self.__height = self.height()

            self.__is_resizing = (event.x() > self.ui.main.width() - 10) and (event.y() > self.ui.main.height() - 10)

            self.__last_pos = event.pos()

    # 调整窗口大小
    def on_main_mouseMoveEvent(self, event):
        is_resizing = self.__is_resizing
        
        # 正在调整则改变窗口大小，否则设置光标样式
        if is_resizing:
            x = event.x()
            y = event.y()

            # 改变大小
            self.__width = self.__width + x - self.__last_pos.x()
            self.__height = self.__height + y - self.__last_pos.y()

            self.resize(self.__width, self.__height)

            # 上次坐标
            self.__last_pos = QPoint(x, y)  

        else:
            is_right = event.x() > self.ui.main.width() - 10
            is_bottom = event.y() > self.ui.main.height() - 10

            # 光标样式
            if is_right and is_bottom: # 右下角
                cursor = Qt.SizeFDiagCursor
            else:
                cursor = Qt.ArrowCursor 

            self.ui.main.setCursor(cursor)

    # 窗口边缘松开
    def on_main_mouseReleaseEvent(self, event):
        self.__is_resizing = False
        self.ui.main.setCursor(Qt.ArrowCursor)
    
    # logo、title 按下
    def on_title_mousePressEvent(self, event):
        self.__is_moving = True # 正在拖动
        self.__move_pos = event.globalPos() - self.pos() # 获取鼠标相对窗口的位置

    # logo、title 拖动
    def on_title_mouseMoveEvent(self, event):
        if self.__is_moving and (not (self.isMaximized() or self.isFullScreen())):
            self.move(event.globalPos() - self.__move_pos) # 更改窗口位置
    
    # logo、title 松开
    def on_title_mouseReleaseEvent(self, event):
        self.__is_moving = False # 结束
        
    # 点击进度条跳转
    def on_bar_mousePressEvent(self, event):        
        position = int(self.ui.bar.maximum() * (event.x() / self.ui.bar.width()))
        
        self.ui.bar.setValue(position)
        
        QSlider.mousePressEvent(self.ui.bar, event)
        self.ui.bar.sliderPressed.emit()

    # 小图片按下
    def on_mimage_mouseReleaseEvent(self, event):
        self.ui.sidebar.setCurrentRow(2)
        self.ui.stacked_tab.setCurrentIndex(2)
        
#         self.ui.side.setVisible(not self.ui.sidebar.isVisible())
            
#         pixmap = self.ui.big_image.pixmap()

#         image = ImageQt.fromqpixmap(pixmap)

#         img_blur = image.filter(ImageFilter.GaussianBlur(radius=5))

#         img_blur.save('datas/cache/cache-background.png')
        
#         self.window_pale = QPalette() 
#         self.window_pale.setBrush(QPalette.Background, 
#                                     QBrush(pixmap)) 
#         self.ui.main.setStyleSheet('''
# #main {
#     border-image: url(datas/cache/cache-background.png);
# }
# ''')
        #self.ui.main.setPalette(self.window_pale)
        # self.setGraphicsEffect(self.effect_blur)
        # self.ui.main_frame.setGraphicsEffect(QGraphicsBlurEffect(self))
        
    # 歌词滚轮滚动
    def on_lrcbox_wheelEvent(self, event):
        def reset():
            # 如果不等于1，说明还有其他等待事件，也就是三秒内有新的滚轮滚动，那么这次作废
            if len(self.__scrolling_timers) == 1:
                self.__is_scrolling = False
                
            del self.__scrolling_timers[0]

        distance = int(event.angleDelta().y() / 120 * self.lrc_height)

        # 计算目标位置
        y = self.ui.lrcs_view_content.y() # 当前位置
        to_y = y + distance
        
        self.scroll_lrcbox(y, to_y) # 滚动歌词
        
        # 计时，三秒内不会滚动歌词
        timer = QTimer(self)
        timer.singleShot(3000, reset)
        self.__scrolling_timers.append(timer)
        
    # 歌词双击
    def on_lrcbox_mouseDoubleClickEvent(self, event):
        # 因为无法获取触发事件的控件，因此传递到父控件获取坐标来转换
        event.ignore() # 忽略，传递到父控件
        
    # 歌词双击忽略，传到歌词区域双击
    def on_lrcs_view_content_mouseDoubleClickEvent(self, event):
        # 获取到是第几个歌词
        index = event.y() // self.lrc_height
        
        # 设置进度，此处不用设置滚动动画，会自动滚动
        position = int(self.lrcs[index][1])        
        self.player.setPosition(position)

# ======== 其他方法 ========

    # 切换到指定界面
    def change_tab(self, index):
        self.ui.sidebar.setCurrentRow(index)
        self.ui.stacked_tab.setCurrentIndex(index)

    # 弹出改变音量菜单
    def volume_controler_pop(self, pos):
        x = pos.x() - 10
        y = pos.y() - 258
        self.volume_menu.exec_(QPoint(x, y))

    # 插入搜索结果
    def insert_search_result(self, datas):
        results_view = self.ui.results_view  

        # 设置行数
        results_view.setRowCount(len(datas))

        for index, data in enumerate(datas[:21]):
            self.insert_songs_datas(results_view, data, index)

    # 添加音乐
    def add_media(self, datas, local=False, play=False) -> int:  
        # 爬取完音乐 URL  
        def music_url_finished(url):   
            if url == 'error:GetError':
                title = '错误'
                warn = '获取歌曲出错，请检查你的网络或重试。'
                QMessageBox.warning(self, title, warn)
                return  

            elif url == 'error:PaidError':
                title = '付费'
                warn = '付费歌曲，获取失败。'
                QMessageBox.warning(self, title, warn)
                return  

            content = QMediaContent(QUrl(url))
            sign = datas[6]
            
            self.current_music_url = sign.split(':')[0] + ':' + url
            # self.current_music_rid = ':'.join(sign.split(':')[1:])
            add_content(content, sign)

        # 添加内容
        def add_content(content, sign) -> int:
            # 去重
            if (len(self.__playlist) == 0) or (sign not in list(zip(*self.__playlist))[0]):
                self.playlist.addMedia(content)
                self.__playlist.append([sign, datas])

                # “播放列表”按钮显示个数
                self.ui.mplaylist.setText(str(len(self.__playlist)))

                # 添加行
                playlist_view = self.ui.playlist_view
                row_count = playlist_view.rowCount()
                playlist_view.setRowCount(row_count + 1)

                # 插入信息
                self.insert_songs_datas(playlist_view, datas, row_count)

            index = list(zip(*self.__playlist))[0].index(sign) # 内容编号

            # 播放
            if play:
                self.start_play(index)

            return index

        sign = datas[6]
        engine, *data = sign.split(':')
        if engine == 'local':  
            # 本地音乐 
            url = ':'.join(data)
            content = QMediaContent(QUrl.fromLocalFile(url))
            add_content(content, sign)
        else:
            # 网络音乐 
            music_url_getter = SubThread(task=SubThread.get_music_url, data=sign)
            music_url_getter.music_url_finished.connect(music_url_finished)
            self.music_url_getters.append(music_url_getter)
            music_url_getter.start()

    # 插入歌曲信息
    def insert_songs_datas(self, widget, datas, row): 
        # 完成爬图片           
        def pixmap_finished(result):
            widget.insert_pixmap(row, result)

        widget.insert_datas(row, datas)

        # 多线程爬取图片
        engine, *data = datas[4].split(':')
        if engine == 'local':
            url = ':'.join(data)
            img_getter = SubThread(task=SubThread.get_local_pixmap, url=url)
        else:            
            img_getter = SubThread(task=SubThread.get_pixmap, data=datas[4])

        img_getter.pixmap_finished.connect(pixmap_finished)
        self.img_getters.append(img_getter)
        img_getter.start()

    # 移动播放列表项
    def move_playlist_view_item(self, from_row, to_row):
        self.ui.playlist_view.move_item(from_row, to_row)

        # 播放列表交换
        datas = self.__playlist.pop(from_row)
        self.__playlist.insert(to_row, datas)

        current_index = self.playlist.currentIndex()

        # 播放列表移动项
        self.playlist.moveMedia(from_row, to_row)

        # 选中对的歌曲
        if current_index == from_row:
            self.playlist.setCurrentIndex(to_row)
        elif current_index == to_row:
            self.playlist.setCurrentIndex(from_row)
        else:
            self.playlist.setCurrentIndex(current_index)
            
        self.player.play()
        self.ui.playlist_view.selectRow(to_row)

    # 播放音乐
    def start_play(self, index): 
        self.ui.mdownload.setStyleSheet('''
#mdownload {background: transparent;}
#mdownload:hover {background: #ddd;}
''')
        self.timer.start()
        self.player.stop()
        self.playlist.setCurrentIndex(index)
        self.player.play()

    # 刷新歌曲信息显示
    def refresh_songsui(self, datas):   
        # 获取完小图       
        def pixmap_finished(pixmap):
            self.ui.mimage.setPixmap(pixmap) # 控制框小图片
        
        # 获取完大图
        def img_finished(pixmap):            
            self.ui.big_image.setPixmap(pixmap) # 歌词界面的歌曲封面大图
            
        # 获取完歌词
        def lrcs_finished(lrcs):
            self.lrcs = lrcs
            self.insert_lrcbox(lrcs)                

        # 初始化信息
        name, artist, album, length, bigimg, pixmap, sign = datas

        engine, *data = sign.split(':')
        if engine == 'local':
            url = ':'.join(data)
            pixmap_getter = SubThread(task=SubThread.get_local_pixmap, url=url)
            img_getter = SubThread(task=SubThread.get_local_img, url=url)
            lrc_getter = SubThread(task=SubThread.get_local_lrcs, url=url)
        else:
            pixmap_getter = SubThread(task=SubThread.get_pixmap, data=pixmap)
            img_getter = SubThread(task=SubThread.get_img, data=bigimg)
            lrc_getter = SubThread(task=SubThread.get_lrcs, data=sign)

        # 初始化
        self.ui.mimage.setPixmap(QPixmap()) # 控制框小图片        
        self.ui.big_image.setPixmap(QPixmap()) # 歌词界面的歌曲封面大图
        self.insert_lrcbox([['无歌词', 0]])

        # 获取小图
        pixmap_getter.pixmap_finished.connect(pixmap_finished)
        self.img_getters.append(pixmap_getter)
        pixmap_getter.start()

        # 获取封面大图
        img_getter.img_finished.connect(img_finished)
        self.img_getters.append(img_getter)
        img_getter.start()     
        
        # 获取歌词
        lrc_getter.lrcs_finished.connect(lrcs_finished)
        self.lrc_getters.append(lrc_getter)
        lrc_getter.start()

        # 显示歌曲信息
        name_ = f'{name} - {artist}'
        self.ui.mname.setText(name_) # 托盘右键菜单歌曲名
        self.menu_widget.menu_name.setText(name_) # 控制框歌曲名
        self.tray_icon.setToolTip('Hi音乐\n' + name_) # 托盘 ToolTip歌曲名
        self.setWindowTitle(name_) # 任务栏歌曲名
        self.ui.big_mname.setText(name) # 歌词界面歌曲名
        self.ui.big_martist.setText(artist) # 歌词界面歌手名

        self.refresh_mcollect_status()

    # 刷新收藏图标按钮状态
    def refresh_mcollect_status(self):
        collections_view = self.ui.collections_view
        collected = []
        color = self.toolbtn_color

        for row in range(collections_view.rowCount()):
            collected.append(collections_view.get_datas(row)[6])

        datas = self.__playlist[self.playlist.currentIndex()][1]

        if datas[6] in collected:
            self.ui.mcollect.setIcon(qta.icon('fa.heart', color='#f33'))
            self.ui.mcollect.setToolTip('已收藏')
        else:
            self.ui.mcollect.setIcon(qta.icon('fa.heart-o', color=color))
            self.ui.mcollect.setToolTip('收藏')

    # 上一曲
    def previous(self):
        index = self.play_plus(-1) # 上一曲

    # 下一曲
    def next(self):
        index = self.play_plus(1) # 下一曲

    # 更高级的 上一曲/下一曲，单曲模式能够切换到下一首
    def play_plus(self, step):
        # 是否在单曲模式
        if self.playlist.playbackMode() in [QMediaPlaylist.CurrentItemOnce, QMediaPlaylist.CurrentItemInLoop]:
            # 计算出序号
            current_index = self.playlist.currentIndex()
            count = self.playlist.mediaCount()
            index = (current_index + step) % count
        else:
            # 上一曲/下一曲 序号
            if step == -1:
                index = self.playlist.previousIndex()
            else:
                index = self.playlist.nextIndex()

        self.player.stop()
        self.playlist.setCurrentIndex(index)
        self.player.play()

    # 插入歌词
    def insert_lrcbox(self, lrcs): 
        lrcs_view_layout = self.ui.lrc_view_layout

        # 清除歌词
        count = lrcs_view_layout.count()
        for i in range(count):
            lrcs_view_layout.itemAt(i).widget().deleteLater()

        # 插入歌词
        width = 0
        height = 0
        item_h = int(self.lrc_height)
        for index, word in enumerate(list(zip(*lrcs))[0]):
            item = QLabel(word)
            item.setMinimumSize(QSize(0, item_h))
            item.setMaximumSize(QSize(166660, item_h))
            item.setObjectName('lrcbox')
            item.setProperty('lrcbox_index', str(index))
            item.wheelEvent = self.on_lrcbox_wheelEvent
            item.mouseDoubleClickEvent = self.on_lrcbox_mouseDoubleClickEvent
            lrcs_view_layout.addWidget(item)

            if item.width() > width:
                width = item.width()
            
        height = len(lrcs) * item_h

        # 设置歌词区域大小和位置
        self.ui.lrcs_view_content.setGeometry(0, item_h * self.lrcs_top, width, height)

    # 匹配歌词
    def match_lrc(self, position) -> int:
        # 歌词的时间列表
        times = list(zip(*self.lrcs))[1]

        # 获取序号
        times = [*times, position]
        index = sorted(times).index(position)

        # 不重合则减一
        if times.count(position) < 2:
            index = index - 1

        return index

    # 歌词同步
    def synchronize_lrcs(self):
        # 不在播放就退出
        if self.player.state() != QMediaPlayer.PlayingState:
            return

        # 获取到对应的歌词序号
        position = self.player.position()

        index = self.match_lrc(position)
        if index < 0:
            return

        # 歌词没变就退出
        if index != self.__lrc_index:        
            # 设置样式
            self.ui.lrcs_view.setStyleSheet('''
#lrcbox[lrcbox_index="%s"] {
    color: #2080f0; 
    font-size: 18px;
}''' % (index))
        
        if not len(self.__scrolling_timers):
            # 计算目标位置
            y = self.ui.lrcs_view_content.y() # 当前位置
            to_y = 0 - (index - self.lrcs_top) * self.lrc_height # 目标位置
            
            self.scroll_lrcbox(y, to_y) # 滚动歌词

        self.__lrc_index = index # 设置当前歌词序号
        
    # 滚动歌词
    def scroll_lrcbox(self, from_y, to_y):
        # 设置滚动动画
        self.lrcs_animation.setStartValue(QPoint(0, from_y)) # 开始坐标
        self.lrcs_animation.setEndValue(QPoint(0, to_y)) # 结束坐标
        self.lrcs_animation.start() # 开始动画
        
    def quit_app(self):
        dump(helper.settings, open('settings.json', 'w'), indent=4)
        
class SubThread(QThread):
    finished = pyqtSignal(list)
    result_finished = pyqtSignal(list)
    pixmap_finished = pyqtSignal(QPixmap)
    img_finished = pyqtSignal(QPixmap)
    lrcs_finished = pyqtSignal(list)
    music_url_finished = pyqtSignal(str)
    music_content_finished = pyqtSignal(bytes)

    arg = [] # 参数
    args = {} # 参数
    task = None # 任务

    def __init__(self, task, finished=None, *arg, **args):
        QThread.__init__(self)

        self.arg = arg # 参数
        self.args = args # 参数
        self.task = task # 任务

        if finished != None:
            self.finished.connect(finished)
    
    # 入口
    def run(self):
        result = self.task(self, *self.arg, **self.args)

    # 获取搜索结果
    def get_result(self, keyword):
        try:
            datas = helper.engine.search(keyword)
        except:
            datas = []

        self.result_finished.emit(datas)

    # 获取小图片
    def get_pixmap(self, data):            
        engine, url = split_sign(data)
        
        if not url:
            return

        try:
            img = helper.engines[engine].get_pic(url)

            # 图片
            img = QImage.fromData(img)
            img = QPixmap.fromImage(img)
            pixmap = img.scaled(40, 40, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
        except:
            return
        
        self.pixmap_finished.emit(pixmap)

    # 获取大图片
    def get_img(self, data):
        if not data:
            return

        engine, url = split_sign(data)

        try:
            content = helper.engines[engine].get_pic(url)

            # 图片
            img = QImage.fromData(content)
            pixmap = QPixmap.fromImage(img).scaled(240, 240, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
        except:
            return
        
        self.img_finished.emit(pixmap)

    def get_local_pixmap(self, url):
        img_url = find_lrc_img_in_path(url, 'img')[0]
        pixmap = QPixmap(img_url)
        try:
            pixmap = pixmap.scaled(40, 40, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
        except:
            pass

        self.pixmap_finished.emit(pixmap)

    def get_local_img(self, url):
        img_url = find_lrc_img_in_path(url, 'img')[0]
        pixmap = QPixmap(img_url)
        try:
            img = pixmap.scaled(240, 240, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
        except:
            pass

        self.img_finished.emit(img)
        
    # 获取歌词
    def get_lrcs(self, data):
        engine, sign = split_sign(data)

        try:
            lrcs = helper.engines[engine].get_music_lrc(sign)
        except:
            return

        self.lrcs_finished.emit(lrcs)

    def get_local_lrcs(self, url):
        lrc_url = find_lrc_img_in_path(url, 'lrc')[1]

        with open(lrc_url, 'r') as f:
            lrcs_str = f.read()

        lrcs = mapi.format_lrc(lrcs_str)

        self.lrcs_finished.emit(lrcs)

    # 获取音乐 URL
    def get_music_url(self, data):
        music_url = ''
        engine, url = split_sign(data)
        try:
            music_url = helper.engines[engine].get_music_url(url)
        except Exception as e:
            music_url = 'error:' + str(e)
        
        self.music_url_finished.emit(music_url)

    def get_music_content(self, data):
        engine, url = split_sign(data)
        try:
            content = helper.engines[engine].get_music_content(url)
        except:
            return

        self.music_content_finished.emit(content)

# 帮助
class CommonHelper: 
    engine = mapi.EngineKuwo
    default_engine = mapi.EngineKuwo
    engines = {}
    settings = {}
    cache = {}
    qss = []

    def __init__(self):
        # 读取 QSS 文件
        self.read_qss('qss/style.qss')
        self.read_qss('qss/buttons.qss')

        # 读取设置
        self.read_settings()
        
        # 读取缓存
        self.read_cache()

        # 设置引擎
        self.set_engine()

    # 读取QSS文件
    def read_qss(self, style):
        with open(style, 'r', encoding='utf-8') as f:
            self.qss.append(f.read())

    # 读取设置
    def read_settings(self):
        try:
            settings = load(open('datas/settings.json', 'r'))
        except:
            with open('datas/settings.json', 'w') as f:
                f.write('{}')
            settings = {}
        settings.setdefault('general', {})
        settings.setdefault('lrcs', {})
        settings.setdefault('download', {})
        self.settings = settings
        
    # 读取缓存
    def read_cache(self):
        try:
            cache = load(open('datas/cache.json', 'r'))
        except:
            with open('datas/cache.json', 'w') as f:
                f.write('{}')
            cache = {}
        cache.setdefault('last_song', [])
        cache.setdefault('last_playlist', [])
        cache.setdefault('collections', [])
        self.cache = cache

    # 设置搜索引擎
    def set_engine(self):
        self.engines = {}
        for s in dir(mapi):
            if s.startswith('Engine'):
                engine = eval(f'mapi.{s}')
                self.engines[engine.pre] = engine
                if engine.pre == self.settings['general'].setdefault('default_engine', 'kuwo'):
                    self.engine = engine
                    self.default_engine = engine
                    
    # 保存设置
    def save_settings(self):
        dump(self.settings, open('datas/settings.json', 'w'), indent=4)
        
    # 保存缓存
    def save_cache(self):
        dump(self.cache, open('datas/cache.json', 'w'), indent=4)

# 分离sign
def split_sign(sign):
    engine, *datas = sign.split(':')
    data = ':'.join(datas)

    return engine, data

# 毫秒格式化
def format_position(position) -> str:
    secs = position / 1000   # 秒
    mins = int(secs / 60)         # 分钟
    secs = int(secs % 60)       # 余数秒
    
    return '{:0>2,d}:{:0>2,d}'.format(mins, secs)

# 寻找目录下歌词文件和图片文件
def find_lrc_img_in_path(url, mode='lrcimg'):

    img_file = ''
    lrc_file = ''

    # 匹配后缀
    allowed_imgs = ['jpg', 'png']
    allowed_lrcs = ['lrc']

    # 遍历
    *paths, name = url.split('/')
    path = '/'.join(paths)
    file_name = '.'.join(name.split('.')[:-1])
    all_files = walk(path)

    # 结果
    lrc_file = ''
    img_file = ''

    # 目标路径正则
    lrc_path_regex = f'{path}(/((lrc)|(lrcs)))?'
    img_path_regex = f'{path}(/((image)|(img)|(images)|(imgs)))?'

    # 遍历
    for path, dir, filelist in all_files:
        # 格式化
        path = path.replace('\\', '/')

        # 路径是否合法
        is_lrc_path_valid = bool(fullmatch(lrc_path_regex, path, I))
        is_img_path_valid = bool(fullmatch(img_path_regex, path, I))
        if not (is_lrc_path_valid or is_img_path_valid):
            continue

        # 遍历文件
        for file in filelist:
            # 文件名和后缀
            name = '.'.join(file.split('.')[:-1])
            suffix = file.split('.')[-1]

            # 文件名不匹配
            if name != file_name:
                continue
            # 文件未有 且 后缀匹配 且 路径匹配
            if (not lrc_file) and (suffix in allowed_lrcs) and is_lrc_path_valid:
                lrc_file = path + '/' + file
                break
            if (not img_file) and (suffix in allowed_imgs) and is_img_path_valid:
                img_file = path + '/' + file
                break

        # 如果两个文件都有就退出
        if all([lrc_file, img_file]):
            break


    return img_file, lrc_file

def is_memory_attach(key):
    global share
    
    share = QSharedMemory()
    share.setKey(key)

    if share.attach():
        QMessageBox.warning(None, '程序已在运行', '程序已在运行，请关闭后重试。')
        return True
    else:
        share.create(1)
        return False

def main():
    global app, window, helper

    helper = CommonHelper()

    app = QApplication(sys.argv) 

    if is_memory_attach('HiMusic'):
        return  
    
    window = MainWindow()

    # 显示窗体并运行
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()