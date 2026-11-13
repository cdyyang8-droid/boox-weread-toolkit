#!/usr/bin/env python3
"""Small local launcher. The service selections live in boox_tool.py."""
import os
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)


def main():
    print('文石微信读书极简工具箱\n服务管理需要连接阅读器，开启 USB 调试并授权。')
    while True:
        print('\n1. 查看可选服务与影响\n2. 读取设备现状\n3. 逐项选择服务并停用\n4. 逐项选择，仅预览\n5. 按记录恢复服务\n6. 恢复文石原厂首页\n0. 退出')
        choice = input('选择：').strip()
        commands = {'1': ['list'], '2': ['status'], '3': ['select'],
                    '4': ['select', '--dry-run'], '6': ['restore-home']}
        if choice == '0':
            return
        if choice == '5':
            records = []
            for path in sorted((ROOT / 'backups').glob('*.json'), reverse=True):
                try:
                    if json.loads(path.read_text(encoding='utf-8')).get('kind') == 'services':
                        records.append(path)
                except (OSError, ValueError, AttributeError):
                    continue
            if not records:
                print('默认 backups 目录没有记录。如使用了自定义目录，请运行 restore 命令指定路径。')
                continue
            for i, path in enumerate(records, 1):
                print(f'{i}. {path.name}')
            value = input('选择恢复记录编号（先恢复最新记录），回车取消：').strip()
            if not value:
                continue
            try:
                index = int(value)
                if index < 1 or index > len(records):
                    raise ValueError()
                args = ['restore', str(records[index - 1])]
            except ValueError:
                print('编号无效。')
                continue
        elif choice in commands:
            args = commands[choice]
        else:
            print('编号无效。')
            continue
        subprocess.run([sys.executable, str(ROOT / 'tools/boox_tool.py'), *args])


if __name__ == '__main__':
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print('\n已退出。')
