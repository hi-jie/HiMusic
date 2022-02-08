import sys
from os import walk
from re import search, fullmatch, I
from json import load, dump

from PyQt5.QtWidgets import (QApplication, QMainWindow, QLabel, 
                             QListView, 
                             QTableWidgetItem,
                             QGraphicsDropShadowEffect, QGraphicsBlurEffect,
                             QFileDialog, QMessageBox,
                             QSystemTrayIcon, QMenu, QAction, QWidgetAction)
from PyQt5.QtCore import (Qt, QSize, QPoint, QMetaObject, pyqtSignal, pyqtSlot, QThread, QUrl, QTimer, QDir)
from PyQt5.QtGui import (QIcon, QFont, QImage, QPixmap, QPalette, QBrush)
from PyQt5.QtMultimedia import (QMediaPlayer, QMediaPlaylist, QMediaContent)
from PyQt5.Qt import QPropertyAnimation
import qtawesome as qta

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

    current_music_url = '' # 当前音乐网址

    toolbtn_color = '#555' # 工具按钮的颜色

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
        self.setup_volume_menu() # 设置音量菜单
        self.setup_ui() # 组件初始化
        self.setup_cache() # 设置缓存
        self.setup_settings() # 设置
        self.setup_engine() # 导入引擎
        self.setup_media() # 设置播放器
        self.setup_timer() # 设置定时器
        self.setup_animation() # 设置歌词滚动动画  
        self.setup_slots() # 组件槽连接
        self.setup_events() # 组件事件连接

    def setup_ui(self):  
        # 窗口背景自动填充，不可透明
        self.ui.main_frame.setAutoFillBackground(True)
        
        # 设置搜索引擎列表模型
        self.ui.input_engine.setView(QListView())
        self.ui.settings_default_engine.setView(QListView())
        
        # 搜索栏搜索按钮
        self.ui.input_ok.setIcon(qta.icon('fa.search', color='#888'))
        self.ui.input_ok.setCursor(Qt.PointingHandCursor)
        
        # 菜单栏图标
        font = qta.font('fa', 14)
        self.ui.logo.setText('Hi 音乐')
        self.ui.logo.setFont(font)
        self.ui.sidebar.item(0).setText(chr(0xf015) + '      首页     ')
        self.ui.sidebar.item(1).setText(chr(0xf002) + '   搜索结果 ')
        self.ui.sidebar.item(2).setText(chr(0xf0db) + '      歌词     ')
        # self.ui.sidebar.item(2).setText(chr(0xf08a) + '   我的收藏 ')
        self.ui.sidebar.item(3).setText(chr(0xf03a) + '   播放列表 ')
        self.ui.sidebar.item(4).setText(chr(0xf013) + '      设置     ')
        self.ui.sidebar.item(0).setFont(font)
        self.ui.sidebar.item(1).setFont(font)
        self.ui.sidebar.item(2).setFont(font)
        self.ui.sidebar.item(3).setFont(font)
        self.ui.sidebar.item(4).setFont(font)
        # self.ui.sidebar.item(5).setFont(font)
      
        # 菜单栏选中首页
        self.ui.sidebar.setCurrentRow(0)
        
        # 首页“上次在听”
        self.ui.last_song.horizontalHeader().setVisible(False)
        self.ui.last_song.setRowCount(1) # 一行
        self.ui.last_song.verticalHeader().setDefaultSectionSize(50) # 高50px
        color = '#555'
        self.ui.last_song_play.setIcon(qta.icon('fa.play-circle-o', color=color))
        self.ui.last_playlist_addall.setIcon(qta.icon('fa.plus', color=color))
        
        # 首页“上次播放列表”
        self.ui.last_playlist.verticalHeader().setDefaultSectionSize(50) # 高50px

        # 工具按钮图标
        color = self.toolbtn_color
        self.ui.mmode.setIcon(qta.icon(self.play_modes[1][0], color=color))
        self.menu_widget.menu_mode.setIcon(qta.icon(self.play_modes[1][0], color=color))
        self.ui.mdownload.setIcon(qta.icon('fa.download', color=color))
        self.ui.mdetail.setIcon(qta.icon('fa.ellipsis-h', color=color))
        self.ui.mcollect.setIcon(qta.icon('fa.heart-o', color=color))
        self.ui.mvolume.setIcon(qta.icon('fa.volume-up', color=color))
        self.menu_widget.menu_volume.setIcon(qta.icon('fa.volume-up', color=color))
        self.ui.mplaylist.setIcon(qta.icon('fa.list-ul', color=color))
        self.ui.settings.setIcon(qta.icon('fa.bars', color=color))

        # 小图片
        self.ui.mimage.setCursor(Qt.PointingHandCursor)
        
        # 歌词列表字体变大
        list_font = QFont('', 12)
        self.ui.lrcs_view.setFont(list_font)

        # 初始化歌词
        self.insert_lrcbox([['无歌词', 0]])
        
        # 设置
        self.ui.settings_close_trayicon.setCursor(Qt.PointingHandCursor)
        
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

    # 设置
    def setup_settings(self):
        settings = helper.settings
        # QSS
        qss = helper.qss
        self.setStyleSheet(''.join(qss))
        
        # 关闭按钮最小化到托盘 
        close_trayicon = settings['window'].get('close_trayicon', True)
        self.ui.settings_close_trayicon.setChecked(close_trayicon)
        QApplication.setQuitOnLastWindowClosed(not close_trayicon)

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

        self.ui.results_view.itemPlay.connect(self.music_selected) # 选中搜索结果歌曲
        self.ui.playlist_view.itemPlay.connect(self.music_selected) # 选中播放列表歌曲

        self.ui.mlast.clicked.connect(self.previous) # 界面点击上一曲
        self.menu_widget.menu_last.clicked.connect(self.previous) # 托盘点击上一曲
        self.ui.mnext.clicked.connect(self.next) # 界面点击下一曲
        self.menu_widget.menu_next.clicked.connect(self.next) # 托盘点击下一曲

        self.ui.mmode.clicked.connect(self.change_playbackmode) # 界面点击播放模式
        self.menu_widget.menu_mode.clicked.connect(self.change_playbackmode) # 托盘点击播放模式

        self.ui.mvolume.clicked.connect(self.on_mvolume_clicked) # 界面调整音量
        self.menu_widget.menu_volume.clicked.connect(self.on_menu_volume_clicked) # 托盘调整音量

        self.volume_widget.volumeChanged.connect(self.on_volume_widget_volumeChanged)

        self.player.positionChanged.connect(self.position_changed) # 播放器进度变化
        self.player.durationChanged.connect(self.__durationchanged) # 播放器长度变化
        self.player.stateChanged.connect(self.state_changed) # 播放器状态变化

        self.playlist.currentIndexChanged.connect(self.music_changed) # 播放器音乐变化

        self.ui.playlist_view_editbar.fromLocal.connect(self.on_from_local_clicked)

    # 组件事件连接        
    def setup_events(self):
        self.ui.main_frame.mousePressEvent = self.on_main_frame_mousePressEvent # 窗口边缘按下
        self.ui.main_frame.mouseMoveEvent = self.on_main_frame_mouseMoveEvent # 调整窗口大小
        self.ui.main_frame.mouseReleaseEvent = self.on_main_frame_mouseReleaseEvent # 窗口边缘松开
        self.ui.logo.mousePressEvent = self.on_logo_mousePressEvent # logo 按下
        self.ui.logo.mouseMoveEvent = self.on_logo_mouseMoveEvent  # logo 拖动
        self.ui.logo.mouseReleaseEvent = self.on_logo_mouseReleaseEvent # logo 松开
        self.ui.mimage.mouseReleaseEvent = self.on_mimage_mouseReleaseEvent # 小图片按下
        
    # 定义特效
    def set_effect(self):
        self.effect_shadow = QGraphicsDropShadowEffect(self) # 创建阴影
        self.effect_shadow.setOffset(0, 0) # 偏移
        self.effect_shadow.setBlurRadius(10) # 阴影半径
        self.effect_shadow.setColor(Qt.black) # 阴影颜色
        
        self.effect_blur = QGraphicsBlurEffect(self)
        self.effect_blur.setBlurRadius(40)
    
    # 设置窗口阴影
    def set_shadow(self):
        self.setAttribute(Qt.WA_TranslucentBackground)   #将窗口设置为透明
        self.setGraphicsEffect(self.effect_shadow) # 将设置套用到窗口中
        
    # 导入引擎
    def setup_engine(self):
        for index, engine in enumerate(helper.engines.values()):        
            self.ui.input_engine.addItem(engine.name, engine)       
            self.ui.settings_default_engine.addItem(engine.name, engine.sign)

            if engine.sign == helper.default_engine.sign:
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

        color = '#555'
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
        self.tray_icon.setIcon(QIcon('imgs/ico.ico'))#qta.icon('fa.music', color='#2080f0'))
        self.tray_icon.setToolTip('Hi 音乐\n无歌曲')
        self.tray_icon.activated.connect(self.on_tray_icon_activated)
        self.tray_icon.show()

    # 设置音量菜单
    def setup_volume_menu(self):
        self.volume_widget = VolumeControler.QVolumeControler(self)
        self.volume_widget.setObjectName('volume_widget')

        self.act_volume = QWidgetAction(self.volume_widget)
        self.act_volume.setDefaultWidget(self.volume_widget)

        self.volume_menu = QMenu(self)
        self.volume_menu.addAction(self.act_volume)

    # 设置定时器
    def setup_timer(self):
        self.timer = QTimer()
        self.timer.stop()
        self.timer.setInterval(400)
        self.timer.timeout.connect(self.synchronize_lrcs)

    # 设置歌词滚动动画
    def setup_animation(self):
        self.lrcs_animation = QPropertyAnimation(self.ui.lrcs_view_content, b'pos', self)
        self.lrcs_animation.setDuration(150)

# ======== 自动关联的槽函数 ========

    # 标题栏“更多”按钮
    @pyqtSlot()
    def on_settings_clicked(self):
        self.ui.sidebar.setCurrentRow(4)
        self.ui.stacked_tab.setCurrentIndex(4)

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
            
    # 切换菜单
    @pyqtSlot(int)
    def on_sidebar_currentRowChanged(self, index):
        self.ui.stacked_tab.setCurrentIndex(index)

    # 拖动进度条
    @pyqtSlot()
    def on_bar_sliderReleased(self):
        position = self.ui.bar.value()
        self.player.setPosition(position)

    # “下载”按钮按下
    @pyqtSlot()
    def on_mdownload_clicked(self):
        # 获取完音乐
        def music_content_finished(content):
            name = self.ui.mname.text()

            if not content:
                title = '错误'
                warn = '下载出错，请重试。'
                QMessageBox.warning(self, title, warn)

                return

            with open(f'musics/{name}.mp3', 'wb') as f:
                f.write(content)

            self.ui.mdownload.setStyleSheet('''
#mdownload {background: #ddd;}
#mdownload:hover {background: #ccc;}
''')

        # 当前音乐的 URL
        url = self.current_music_url
        
        if not url:
            return
        
        # 获取音乐
        music_content_getter = SubThread(task=SubThread.get_music_content, data=url)
        music_content_getter.music_content_finished.connect(music_content_finished)
        self.music_content_getters.append(music_content_getter)
        music_content_getter.start()

    # “播放列表”按钮按下
    @pyqtSlot()
    def on_mplaylist_clicked(self):
        self.ui.sidebar.setCurrentRow(3)
        self.ui.stacked_tab.setCurrentIndex(3)

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
            
    # “上次的播放列表”添加全部
    @pyqtSlot()
    def on_last_playlist_addall_clicked(self):
        for row in range(self.ui.last_playlist.rowCount()):
            datas = self.ui.last_playlist.get_datas(row)
            self.add_media(datas)
        
    # 搜索结果添加到列表
    @pyqtSlot(list)
    def on_results_view_itemAdd(self, rows):
        for row in rows:
            self.add_media(self.ui.results_view.get_datas(row))

    # 播放列表选中歌曲变化
    @pyqtSlot()
    def on_playlist_view_itemSelectionChanged(self):
        playlist_view = self.ui.playlist_view
        playlist_view_editbar = self.ui.playlist_view_editbar
        selected_items = playlist_view.selectedItems()

        # “删除”按钮
        if len(selected_items) != 0:
            playlist_view_editbar.setRemoveEnabled(True)
        else:
            playlist_view_editbar.setRemoveEnabled(False)

        # “上移”、“下移”按钮
        if len(selected_items) != 1 * 5:
            playlist_view_editbar.setUpmoveEnabled(False)
            playlist_view_editbar.setDownmoveEnabled(False)

            return

        row = playlist_view.row(selected_items[0])

        if row != 0:
            playlist_view_editbar.setUpmoveEnabled(True)
        else:
            playlist_view_editbar.setUpmoveEnabled(False)

        if row != playlist_view.rowCount() - 1:
            playlist_view_editbar.setDownmoveEnabled(True)
        else:
            playlist_view_editbar.setDownmoveEnabled(False)

    # 删除列表项
    @pyqtSlot()
    def on_playlist_view_editbar_removed(self):
        playlist_view = self.ui.playlist_view
        rows = playlist_view.get_selected_rows()
        current_index = self.playlist.currentIndex()

        for row in rows[::-1]:
            del self.__playlist[row]
            self.playlist.removeMedia(row)
            self.ui.playlist_view.remove_item(row)
            if row < current_index:
                current_index -= 1

        self.playlist.setCurrentIndex(current_index)
        self.player.play()

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
    @pyqtSlot()
    def on_from_local_clicked(self):
        cur_path = QDir.currentPath()
        title = '打开'
        filt = '所有文件(*.*);;mp3文件(*.mp3)'
        filelist, file_filter = QFileDialog.getOpenFileNames(self, title, cur_path, filt)

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

            img_file, _ = find_lrc_img_in_path(url, 'img')

            datas = [song_name, artist, album, '', *['local:' + url] * 3]

            self.add_media(datas)


# ======== 自定义槽函数 ========

    # 退出程序
    def app_quit(self):
        self.close()
        app.quit()

    # 界面音量按钮点击
    def on_mvolume_clicked(self):
        sender = self.sender()
        pos = sender.pos()
        global_pos = self.mapToGlobal(pos)

        self.volume_controler_pop(global_pos)

    # 界面音量按钮点击
    def on_menu_volume_clicked(self):
        sender = self.sender()
        pos = sender.pos()
        x = pos.x() - 8
        y = pos.y() - 8
        pos = QPoint(x, y)
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
            QApplication.processEvents()

    # 选中歌曲
    def music_selected(self, row):
        widget = self.sender()

        # 初始化数据
        datas = widget.get_datas(row)
            
        # 添加音乐
        index = self.add_media(datas, play=True)

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
        if state == QMediaPlayer.PlayingState:
            style_sheet = '''
#mpause, #menu_pause {border-image: url("imgs/pause.svg");}
#mpause:hover, #menu_pause:hover {border-image: url("imgs/pause1.svg");}
'''
            self.ui.mpause.setStyleSheet(style_sheet)
            self.menu_widget.menu_pause.setStyleSheet(style_sheet)
        else:
            style_sheet = '''
#mpause, #menu_pause {border-image: url("imgs/play.svg");}
#mpause:hover, #menu_pause:hover {border-image: url("imgs/play1.svg");}
'''
            self.ui.mpause.setStyleSheet(style_sheet)
            self.menu_widget.menu_pause.setStyleSheet(style_sheet)

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

# ======== 组件事件 ========

    # 窗口关闭事件
    def closeEvent(self, event):
        # 设置
        helper.settings['window']['close_trayicon'] = self.ui.settings_close_trayicon.isChecked() # 关闭时最小化到托盘
        helper.settings['search']['default_engine'] = self.ui.settings_default_engine.currentData() # 默认搜索引擎
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
        helper.save_cache() # 保存缓存

    # 窗口边缘按下
    def on_main_frame_mousePressEvent(self, event):
        if self.isMaximized() or self.isFullScreen():
            return

        if event.button() == Qt.LeftButton:
            self.__width = self.width()
            self.__height = self.height()

            self.__is_resizing = (event.x() > self.ui.main_frame.width() - 5) and (event.y() > self.ui.main_frame.height() - 5)

            self.__last_pos = event.pos()

    # 调整窗口大小
    def on_main_frame_mouseMoveEvent(self, event):
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
            is_right = event.x() > self.ui.main_frame.width() - 5
            is_bottom = event.y() > self.ui.main_frame.height() - 5

            # 光标样式
            if is_right and is_bottom: # 右下角
                cursor = Qt.SizeFDiagCursor
            else:
                cursor = Qt.ArrowCursor 

            self.ui.main_frame.setCursor(cursor)

    # 窗口边缘松开
    def on_main_frame_mouseReleaseEvent(self, event):
        self.__is_resizing = False
        self.ui.main_frame.setCursor(Qt.ArrowCursor)
    
    # logo 按下
    def on_logo_mousePressEvent(self, event):
        self.__is_moving = True # 正在拖动
        self.__move_pos = event.globalPos() - self.pos() # 获取鼠标相对窗口的位置

    # logo 拖动
    def on_logo_mouseMoveEvent(self, event):
        if self.__is_moving and (not (self.isMaximized() or self.isFullScreen())):
            self.move(event.globalPos() - self.__move_pos) # 更改窗口位置
    
    # logo 松开
    def on_logo_mouseReleaseEvent(self, event):
        self.__is_moving = False # 结束

    # 小图片按下
    def on_mimage_mouseReleaseEvent(self, event):
        self.ui.sidebar.setCurrentRow(2)
        self.ui.stacked_tab.setCurrentIndex(2)

# ======== 其他方法 ========

    # 弹出改变音量菜单
    def volume_controler_pop(self, pos):
        x = pos.x() - 2
        y = pos.y() - 250
        self.volume_menu.exec_(QPoint(x, y))
        
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

    # 插入搜索结果
    def insert_search_result(self, datas):
        results_view = self.ui.results_view  

        # 设置行数
        results_view.setRowCount(20)

        for index, data in enumerate(datas[:21]):
            self.insert_songs_datas(results_view, data, index)

    # 添加音乐
    def add_media(self, datas, local=False, play=False) -> int:  
        # 爬取完音乐 URL       
        def music_url_finished(url):
            if not url:
                title = '错误'
                warn = '获取歌曲出错，请重试。'
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

        datas = self.__playlist.pop(from_row)
        self.__playlist.insert(to_row, datas)

        current_index = self.playlist.currentIndex()

        # 播放列表移动项
        self.playlist.moveMedia(from_row, to_row)

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
            pixmap = pixmap
            
            self.ui.big_image.setPixmap(pixmap)
            
            pixmap = pixmap.scaled(self.ui.main_frame.size(), 
                                   Qt.KeepAspectRatioByExpanding, 
                                   Qt.SmoothTransformation)
            
            self.window_pale = QPalette() 
            self.window_pale.setBrush(QPalette.Background, 
                                      QBrush(pixmap)) 
            #self.ui.main_frame.setStyleSheet('background-color: transparent; border-radius: 3px;')
            #self.ui.main_frame.setAutoFillBackground(True)
            #self.ui.main_frame.setPalette(self.window_pale)
            #self.setGraphicsEffect(self.effect_blur)
            #self.ui.main_frame.setGraphicsEffect(QGraphicsBlurEffect(self))
            
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
        self.tray_icon.setToolTip('Hi 音乐\n' + name_) # 托盘 ToolTip歌曲名
        self.ui.big_mname.setText(name) # 歌词界面歌曲名
        self.ui.big_martist.setText(artist) # 歌词界面歌手名

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
            lrcs_view_layout.addWidget(item)

            if item.width() > width:
                width = item.width()
            height = height + item_h

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
        if index == self.__lrc_index:
            return
        
        # 设置样式
        self.ui.lrcs_view.setStyleSheet('''
#lrcbox[lrcbox_index="%s"] {
    color: #2080f0; 
    font-size: 18px;
}''' % (index))

        # 计算目标位置
        y = self.ui.lrcs_view_content.y() # 当前位置
        to_y = 0 - (index - self.lrcs_top) * self.lrc_height # 目标位置

        # 设置滚动动画
        self.lrcs_animation.setStartValue(QPoint(0, y)) # 开始坐标
        self.lrcs_animation.setEndValue(QPoint(0, to_y)) # 结束坐标
        self.lrcs_animation.start() # 开始动画

        self.__lrc_index = index # 设置当前歌词序号
        
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
        datas = helper.engine.search(keyword)

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
        pixmap = pixmap.scaled(40, 40, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)

        self.pixmap_finished.emit(pixmap)

    def get_local_img(self, url):
        img_url = find_lrc_img_in_path(url, 'img')[0]
        pixmap = QPixmap(img_url)
        img = pixmap.scaled(240, 240, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)

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
        except:
            music_url = ''
        
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
        self.read_settings('app/settings.json')
        
        # 读取缓存
        self.read_cache()

        # 设置引擎
        self.set_engine()

    # 读取QSS文件
    def read_qss(self, style):
        with open(style, 'r', encoding='utf-8') as f:
            self.qss.append(f.read())

    # 读取设置
    def read_settings(self, file):
        settings = load(open(file, 'r'))
        settings.setdefault('window', {})
        settings.setdefault('search', {})
        self.settings = settings
        
    # 读取缓存
    def read_cache(self):
        self.cache = load(open('app/cache.json', 'r'))

    # 设置搜索引擎
    def set_engine(self):
        self.engines = {}
        for s in dir(mapi):
            if s.startswith('Engine'):
                engine = eval(f'mapi.{s}')
                self.engines[engine.sign] = engine
                if engine.sign == self.settings['search'].get('default_engine', 'kuwo'):
                    self.engine = engine
                    self.default_engine = engine
                    
    # 保存设置
    def save_settings(self):
        dump(self.settings, open('app/settings.json', 'w'), indent=4)
        
    # 保存缓存
    def save_cache(self):
        dump(self.cache, open('app/cache.json', 'w'), indent=4)

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

def main():
    global app, window, helper

    helper = CommonHelper()

    app = QApplication(sys.argv)   
    
    window = MainWindow()

    # 显示窗体并运行
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()