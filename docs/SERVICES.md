# 可选服务清单

全部默认不选；以下是候选项及关闭影响，不代表每台设备都应停用。清单源于 BOOX Leaf2 P，其他固件中未安装的包自动跳过。

## 可选文石应用

| 名称 | 包名 | 关闭后的影响 |
| --- | --- | --- |
| 邮件 | `com.onyx.mail` | 无法使用文石邮件应用。 |
| 音乐 | `com.onyx.musicplayer` | 无法使用文石音乐播放器，可能影响本地音频播放。 |
| 录音 | `com.onyx.voicerecorder` | 无法使用文石录音功能。 |
| AI 助手 | `com.onyx.aiassistant` | 无法使用文石 AI 助手。 |
| 计算器 | `com.onyx.calculator` | 无法使用文石计算器。 |
| 时钟 | `com.onyx.clock` | 无法使用文石时钟，可能影响闹钟。 |
| 图库 | `com.onyx.gallery` | 无法使用文石图库查看图片。 |
| 应用商店 | `com.onyx.appmarket` | 无法从文石应用商店安装或更新应用。 |
| 书城应用 | `com.onyx.igetshop` | 无法使用对应的文石书城入口。 |
| 浏览器 | `org.chromium.chrome` | 无法使用此 Chromium 浏览器；网页登录或跳转功能需另行验证。 |
| 词典 | `com.onyx.dict` | 无法使用此词典；阅读中查词可能受影响。 |
| 快捷传书 | `com.onyx.easytransfer` | 无法使用文石快捷传书。 |

## Google 服务（可单独选择）

| 名称 | 包名 | 关闭后的影响 |
| --- | --- | --- |
| Google Play 服务 | `com.google.android.gms` | 依赖 Google Play 服务的登录、推送、定位、授权及应用可能失效。 |
| Google 服务框架 | `com.google.android.gsf` | Google 账号及依赖 Google 框架的应用可能失效。 |
| Google 联系人同步 | `com.google.android.syncadapters.contacts` | Google 联系人同步停止。 |
| Google 日历同步 | `com.google.android.syncadapters.calendar` | Google 日历同步停止。 |
| Google 数据恢复 | `com.google.android.apps.restore` | Google 应用及数据恢复功能停止。 |
| Google 位置记录 | `com.google.android.gms.location.history` | Google 位置记录功能不可用。 |

## 其他可选系统功能

| 名称 | 包名 | 关闭后的影响 |
| --- | --- | --- |
| 系统打印服务 | `com.android.bips` | 无法使用系统打印功能。 |
| 打印服务推荐 | `com.android.printservice.recommendation` | 无法使用打印服务推荐。 |
| 系统搜索框 | `com.android.quicksearchbox` | 无法使用该系统搜索框。 |
| Android 彩蛋 | `com.android.egg` | 无法打开 Android 彩蛋。 |
| Android 互动屏保 | `com.android.dreams.basic` | 无法使用 Android 互动屏保；原验证设备的文石屏保不依赖它。 |
| Android 照片互动屏保 | `com.android.dreams.phototable` | 无法使用照片互动屏保；原验证设备的文石屏保不依赖它。 |
| 高通语音激活工具 | `com.qualcomm.qti.sva` | 高通语音唤醒可能不可用。 |

Google 服务存在依赖关系，逐项选择不代表其他依赖仍能正常工作。需要 Google 账号、推送或相关应用时建议保留整组。停用框架后 Google Play 商店可能无法正常使用，即使商店本身未停用。

文石互动屏保与 Android 互动屏保在原验证设备上属于不同功能；其他型号仍需核对。
