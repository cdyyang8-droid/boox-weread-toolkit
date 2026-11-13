#!/usr/bin/env python3
"""Build an installable debug APK using the official SDK tools, without Gradle."""
import argparse
import os
from pathlib import Path
import shutil
import subprocess
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[1]
ANDROID = 'http://schemas.android.com/apk/res/android'
ET.register_namespace('android', ANDROID)


def build():
    parser = argparse.ArgumentParser(description='构建测试 APK；发布版请使用私有发布签名')
    parser.add_argument('--android-jar', type=Path, required=True, help='SDK platforms/android-30/android.jar')
    parser.add_argument('--build-tools', type=Path, required=True, help='SDK build-tools/35.0.0 目录')
    parser.add_argument('--java-home', type=Path, help='JDK 17 Home；也可设置 JAVA_HOME')
    args = parser.parse_args()
    java_home = args.java_home or (Path(os.environ['JAVA_HOME']) if os.environ.get('JAVA_HOME') else None)
    tool_env = dict(os.environ)
    if java_home:
        tool_env['JAVA_HOME'] = str(java_home)
        tool_env['PATH'] = str(java_home / 'bin') + os.pathsep + tool_env.get('PATH', '')
    ext = '.exe' if os.name == 'nt' else ''
    def java_tool(name):
        return str(java_home / 'bin' / (name + ext)) if java_home else name
    def sdk_tool(name):
        suffix = '.bat' if os.name == 'nt' and name in ('d8', 'apksigner') else ext
        return str(args.build_tools.resolve() / (name + suffix))
    def run(*command):
        subprocess.run([str(x) for x in command], check=True, env=tool_env)
    out = ROOT / 'app/build/manual'
    if out.exists():
        shutil.rmtree(out)
    (out / 'classes').mkdir(parents=True)
    (out / 'dex').mkdir()
    manifest = ET.parse(ROOT / 'app/src/main/AndroidManifest.xml')
    node = manifest.getroot()
    node.set('package', 'local.weread.home')
    node.set('{' + ANDROID + '}versionCode', '3')
    node.set('{' + ANDROID + '}versionName', '0.1.0')
    uses = ET.SubElement(node, 'uses-sdk')
    uses.set('{' + ANDROID + '}minSdkVersion', '26')
    uses.set('{' + ANDROID + '}targetSdkVersion', '30')
    node.find('application').set('{' + ANDROID + '}debuggable', 'true')
    manifest.write(out / 'AndroidManifest.xml', encoding='utf-8', xml_declaration=True)
    jar = args.android_jar.resolve()
    run(sdk_tool('aapt'), 'package', '-f', '-M', out / 'AndroidManifest.xml', '-I', jar, '-S', ROOT / 'app/src/main/res', '-F', out / 'unsigned.apk')
    sources = sorted((ROOT / 'app/src/main/java').rglob('*.java'))
    run(java_tool('javac'), '-encoding', 'UTF-8', '-source', '8', '-target', '8', '-bootclasspath', str(jar) + os.pathsep + str(args.build_tools.resolve() / 'core-lambda-stubs.jar'),
        '-d', out / 'classes', *sources)
    classes = sorted((out / 'classes').rglob('*.class'))
    run(sdk_tool('d8'), '--lib', jar, '--min-api', '26', '--output', out / 'dex', *classes)
    with zipfile.ZipFile(out / 'unsigned.apk', 'a', zipfile.ZIP_DEFLATED) as archive:
        archive.write(out / 'dex/classes.dex', 'classes.dex')
    run(sdk_tool('zipalign'), '-f', '4', out / 'unsigned.apk', out / 'aligned.apk')
    # A local test key only. Never use this public, well-known password for a release key.
    key = ROOT / 'app/build/debug.keystore'
    if not key.exists():
        run(java_tool('keytool'), '-genkeypair', '-keystore', key, '-storepass', 'android',
            '-keypass', 'android', '-alias', 'androiddebugkey', '-dname', 'CN=Android Debug,O=Android,C=US',
            '-keyalg', 'RSA', '-keysize', '2048', '-validity', '10000')
    apk = out / 'boox-weread-toolkit-0.1.0-debug.apk'
    run(sdk_tool('apksigner'), 'sign', '--ks', key, '--ks-pass', 'pass:android', '--ks-key-alias',
        'androiddebugkey', '--out', apk, out / 'aligned.apk')
    run(sdk_tool('apksigner'), 'verify', '--verbose', apk)
    print('测试 APK：' + str(apk))


if __name__ == '__main__':
    build()
