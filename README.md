# 文石微信读书极简工具箱

**BOOX WeRead Toolkit** · `boox-weread-toolkit` · MIT

[下载预发布版与 APK](https://github.com/cdyyang8-droid/boox-weread-toolkit/releases/tag/v0.1.0) · [自动检查](https://github.com/cdyyang8-droid/boox-weread-toolkit/actions/workflows/check.yml)

把文石阅读器变成微信读书专用设备，也可以保留一个简洁的阅读首页。按自己的需要选择停用应用、后台组件和 Google 服务，并保留恢复入口。

> 当前版本：0.1.0，预发布。本项目由 BOOX Leaf2 P 上的一次个人配置整理而来；新版 APK 已编译验证，新增模式与通用服务工具尚未在真实设备上完整回归。请先阅读[支持范围](docs/COMPATIBILITY.md)。

## 四个重点

| 功能 | 使用方式 |
| --- | --- |
| **微信读书专用模式** | 首页中开启后，开机及返回首页自动进入微信读书；4 秒内连续返回首页两次可回到设置页。 |
| **关闭不需要的服务** | 电脑端逐项选择邮件、音乐、词典、快捷传书等；默认全部不选，每项显示影响。 |
| **关闭 Google 服务** | Google Play 服务、框架、同步及恢复等单列为一组，可逐项选择；需要 Google 功能的人可以保留。 |
| **文石极简首页** | 默认展示阅读、Wi-Fi、系统设置和原厂桌面入口，可随时切换专用模式或恢复原厂首页。 |

首页应用不申请联网权限，没有后台服务。服务管理通过电脑端 Python + ADB 完成，手机端普通应用没有直接停用其他系统应用的权限。两部分可以独立使用；只安装首页不会改变任何服务。

## 快速开始

### 使用首页

1. 从本项目的发布附件获取 APK，或按[构建说明](docs/BUILD.md)自行编译。源码压缩包不包含 APK。
2. 在阅读器安装 APK，打开“阅读器设置”，点击“设为默认首页”并在系统中确认。
3. 默认是极简首页；需要专用版时点“切换为微信读书专用模式”。
4. 如果原厂系统会自动冻结不常用应用，请将本首页加入解冻/不冻结名单。

微信读书需要自行安装。优先打开墨水屏版 `com.tencent.weread.eink`，找不到时尝试普通版 `com.tencent.weread`。不包含微信读书 APK、账号服务或文石固件。

### 按需关闭服务

电脑准备 Python 3.9+ 和[官方 Android Platform Tools](https://developer.android.com/tools/releases/platform-tools)，在阅读器开启 USB 调试并授权。无需 root。Windows 命令可把 `python3` 换成 `py -3`。

在项目目录运行：

```sh
# 查看可选项目；此命令不连接设备
python3 tools/boox_tool.py list

# 读取设备现状
python3 tools/boox_tool.py status

# 交互式选择：默认不勾选，输入编号，预览后输入 YES 执行
python3 tools/boox_tool.py select
```

也可以明确指定某些项并只做预览：

```sh
python3 tools/boox_tool.py select --packages com.onyx.dict com.onyx.easytransfer --dry-run
```

工具会跳过未安装及原已停用的包。真正执行前先保存原始状态；中途失败会停止并保留恢复记录。**这些记录是启用状态记录，不是书籍、应用数据或整机备份。**

- Mac 可双击 `启动工具.command` 打开菜单。
- Windows 可双击 `启动工具.bat`。
- ADB 不在 PATH 时：`python3 tools/boox_tool.py --adb "/path/to/adb" status`。
- 多设备时：`python3 tools/boox_tool.py --serial DEVICE_SERIAL status`。

详细步骤见[安装与使用](docs/USAGE.md)，逐项影响见[服务清单](docs/SERVICES.md)。

## 如何恢复

恢复服务：使用执行时输出的本地记录路径，先恢复最近的一次操作，再恢复更早的操作。

```sh
python3 tools/boox_tool.py restore backups/你的记录文件.json
```

恢复首页：在首页设置中点击“恢复原来的文石首页”，或运行：

```sh
python3 tools/boox_tool.py restore-home
```

恢复首页和恢复服务相互独立。电脑端恢复首页要求原厂桌面处于可用状态；找不到时会停止。更多情况见[恢复指南](docs/RECOVERY.md)。

## 支持与限制

- 旧版专用首页已在 BOOX Leaf2 P、Android 11、文石固件 4.0.2 上验证重启、微信读书打开、设置入口及恢复。
- 25 项清单来自同一设备的实测记录，共含 12 项应用、6 项 Google 组件和 7 项可选系统功能。
- 新版支持 Android 8.0+ 的编译配置，但实机证据限于上述 Android 11 设备。其他型号、固件和普通版微信读书的行为待验证。
- 不保证续航增幅；没有长期对照测量。停用不会释放系统分区的应用占用。
- 不自动停用系统桌面、输入法、系统界面、网络、WebView、更新或权限管理组件。
- Google 依赖应用、登录、推送、定位等可能因停用受影响；使用前逐项阅读说明。

## 开发与贡献

- [构建 APK](docs/BUILD.md)
- [测试与已知问题](docs/VALIDATION.md)
- [参与贡献](CONTRIBUTING.md)
- [更新记录](CHANGELOG.md)
- [发布前清单](docs/RELEASING.md)

源码与原创文档采用 [MIT](LICENSE)。本项目与文石 BOOX、腾讯及微信读书没有官方关联。相关商标归各自权利人所有。
