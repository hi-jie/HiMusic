<h1 align="center">Hi音乐</h1>

<p align="center">四大平台全音乐搜索、收听与下载的强大音乐播放器</p>

<p align="center">
<a href="./README.md">中文介绍</a> |
<a href="./README.en.md">English Description</a> 
</p>


<p align="center">
<img src="https://img.shields.io/badge/HiMusic-v1.0.0-brightgreen.svg" title="HiMusic" />
<img src="https://img.shields.io/badge/Python-3.8+-blue.svg" title="Python" />
<img src="https://img.shields.io/badge/Django-v2.2-important.svg" title="Django" />
</p>

<p align="center">
<a href="https://hi_jie.gitee.io/HiMusic">官网</a> | 
<a href="https://hi_jie.gitee.io/HiMusic/example">演示站点</a> |
<a href="http://shang.qq.com/wpa/qunwpa?idkey=143c23a4ffbd0ba9137d2bce3ee86c83532c05259a0542a69527e36615e64dba">QQ群</a>
</p>

<p align="center">
<a href="https://doc.mrdoc.pro/project-7/">安装手册</a> | 
<a href="https://doc.mrdoc.pro/project-54/">使用手册</a> |
<a href="https://doc.mrdoc.pro/project-20/">文档效果</a>
</p>

<p align="center">源码：<a href="https://gitee.com/hi_jie/HiMusic">码云</a></p>

## 简介

`HiMusic` 是基于`Python`开发的网络音乐播放器。

HiMusic 适合作为个人和中小型团队的私有云文档、云笔记和知识管理工具，致力于成为优秀的私有化在线文档部署方案

你可以简单粗暴地将 MrDoc 视为「可私有部署的语雀」和「可在线编辑文档的GitBook」。

## 演示站点

开源版 - [http://mrdoc.zmister.com](http://mrdoc.zmister.com)

专业版 - [https://doc.mrdoc.pro](https://doc.mrdoc.pro)

开源版与专业版差异 - [https://doc.mrdoc.pro/project-7/doc-3441/](https://doc.mrdoc.pro/project-7/doc-3441/)

用户名：test1  密码：123456

## 适用场景

个人云笔记、在线产品手册、团队内部知识库、在线电子教程等私有化部署场景。

## 功能特性

- **基础功能**
	- 集成QQ音乐、酷狗音乐、网易云音乐、酷我音乐歌曲搜索与下载；
	- 支持歌词同步滚动，进度条控制音乐进度
	- 多种播放模式选择

- **音乐管理**
	- 可登录四大平台账号，收听VIP、付费音乐，同步获取歌单
	- 登录Gitee账号，在多个设备之间同步
	- 
	- 
	- 
	- 
	- 
	
- **个性化界面**
	- 
	- 
	- 
	- 

- **文档阅读**
	- 
	- 
	- 
	- 
	- 
	- 

完整更新记录详见：[CHANGES.md](./CHANGES.md)

## 简明运行教程

### 1、安装依赖库
```
pip install -r requirements.txt
```

### 2、初始化数据库

在安装完所需的第三方库并配置好数据库信息之后，我们需要对数据库进行初始化。

在项目路径下打开命令行界面，运行如下命令生成数据库迁移：

```
python manage.py makemigrations 
```

运行如下命令执行数据库迁移:

```
python manage.py migrate
```
执行完毕之后，数据库就初始化完成了。

### 3、创建管理员账户
在初始化完数据库之后，需要创建一个管理员账户来管理整个MrDoc，在项目路径下打开命令行终端，运行如下命令：
```
python manage.py createsuperuser
```
按照提示输入用户名、电子邮箱地址和密码即可。

### 4、测试运行
在完成上述步骤之后，即可运行使用MrDoc。

在测试环境中，可以使用Django自带的服务器运行MrDoc，其命令为：

```
python manage.py runserver
```

## 交流

<p>微信：JIE（ID：zmister2016）</p>
<img src="http://mrdoc.zmister.com/media//202010/2020-10-29_213550.png" height=150 />

## 依赖

HiMusic基于以下项目进行开发，在此表示感谢：

- Python
- PyQt5

## 协议

<a href="./LICENSE">GPL-3.0</a>

开源版的使用者必须保留 MrDoc 和觅思文档相关版权标识，禁止对 MrDoc 和 觅思文档相关版权标识进行修改和删除。

如果违反，开发者保留对侵权者追究责任的权利。

商业授权（专业版）请联系QQ咨询：3280350050