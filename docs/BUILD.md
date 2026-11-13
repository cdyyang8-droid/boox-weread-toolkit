# 从源码构建

源码不含 SDK、JDK、Gradle 二进制或签名私钥。应用只使用 Android 原生 API，无第三方运行时依赖。

## Android Studio / Gradle

用 Android Studio 打开项目根目录，安装 Android SDK Platform 30。配置为 Android Gradle Plugin 8.7.3、Gradle 8.9、JDK 17。可使用 Studio 配置 Gradle 8.9，或自行安装 Gradle 8.9 后执行：

```sh
gradle :app:assembleDebug
```

产物通常为 `app/build/outputs/apk/debug/app-debug.apk`。本项目暂未分发 Gradle Wrapper；Gradle 路径没有在本次离线整理中执行。

## 无 Gradle 的离线构建

也可使用 Python 3.9+、JDK 17、Android SDK Platform 30 与 Build Tools 35.0.0。将下方路径替换为自己的本地 SDK 路径；Windows 使用 `py -3`。

```sh
python3 tools/build_debug.py --android-jar /path/to/sdk/platforms/android-30/android.jar --build-tools /path/to/sdk/build-tools/35.0.0 --java-home /path/to/jdk17
```

流程为 aapt 打包、javac 编译、d8 转换、zipalign 对齐、apksigner 签名及验证。运行产生 `app/build/manual/boox-weread-toolkit-0.1.0-debug.apk`。

脚本生成的 debug key 位于忽略目录 `app/build/`，密码为 Android 标准测试密码，仅供本地测试。源码包不包含此 key。脚本生成的 APK 标记为 debuggable，不能当作正式发布签名版。

## 正式发布

使用自己妥善保存的发布签名私钥，在 Android Studio 中执行 Generate Signed APK。签名配置、密码和私钥只保存在本地或受控的 CI Secrets 中，不要写入构建文件或提交到仓库。

之后版本沿用同一发布签名；否则已安装用户无法直接覆盖升级。源码中的 `versionCode` 与 `versionName` 在 Gradle 配置和手工构建脚本中都需要同步更新。

运行 `apksigner verify --verbose --print-certs your-release.apk` 核验签名，并发布 SHA-256 校验值。默认 `assembleRelease` 未配置签名，不能直接作为可安装发布包。
