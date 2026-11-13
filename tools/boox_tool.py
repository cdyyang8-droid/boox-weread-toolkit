#!/usr/bin/env python3
"""BOOX WeRead Toolkit. Python 3.9+, standard library only. MIT licensed."""
import argparse
import datetime as dt
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import uuid

ROOT = Path(__file__).resolve().parents[1]
CATALOG = json.loads((ROOT / 'profiles/services.json').read_text(encoding='utf-8'))
ITEMS = {item['package']: item for item in CATALOG['items']}
HOME = 'local.weread.home/.HomeActivity'
STATE_COMMANDS = {0: 'default-state', 1: 'enable', 2: 'disable', 3: 'disable-user', 4: 'disable-until-used'}


class ToolError(Exception):
    pass


class ADB:
    def __init__(self, executable, serial=None):
        self.executable = executable
        self.serial = serial

    def run(self, *args, shell=True):
        command = [self.executable]
        if self.serial:
            command += ['-s', self.serial]
        if shell:
            command += ['shell']
        result = subprocess.run(command + list(args), capture_output=True, text=True, timeout=45)
        if result.returncode:
            raise ToolError((result.stderr or result.stdout).strip() or 'ADB 命令失败')
        return result.stdout.strip()

    def connect(self, requested):
        rows = [line.split() for line in self.run('devices', shell=False).splitlines()[1:] if line.strip()]
        if requested:
            matches = [r for r in rows if r[0] == requested and len(r) > 1 and r[1] == 'device']
            if not matches:
                raise ToolError('指定设备未就绪。请检查数据线和 USB 调试授权。')
            self.serial = requested
        else:
            if len(rows) != 1 or rows[0][1] != 'device':
                raise ToolError('需要恰好一台已授权设备；多设备时使用 --serial。可先运行 adb devices 查看。')
            self.serial = rows[0][0]
        if self.run('am', 'get-current-user') != '0':
            raise ToolError('本版只支持当前用户为主用户 0 的设备。')
        maker = self.run('getprop', 'ro.product.manufacturer').lower()
        brand = self.run('getprop', 'ro.product.brand').lower()
        if not any(word in maker + ' ' + brand for word in ('onyx', 'boox')):
            raise ToolError('本工具仅面向 BOOX/ONYX 设备，已停止。')

    def identity(self):
        fingerprint = self.run('getprop', 'ro.build.fingerprint')
        if not self.serial or not fingerprint:
            raise ToolError('无法读取完整设备标识，停止写入。')
        return {'serial': self.serial, 'fingerprint': fingerprint,
                'model': self.run('getprop', 'ro.product.model')}

    def state(self, package):
        return parse_state(self.run('dumpsys', 'package', package))

    def installed(self):
        return {line[8:] for line in self.run('pm', 'list', 'packages', '--user', '0').splitlines()
                if line.startswith('package:')}

    def set_state(self, package, state):
        self.run('pm', STATE_COMMANDS[state], '--user', '0', package)
        actual = self.state(package)
        if actual != state:
            raise ToolError(f'{package} 状态未达到预期（期望 {state}，实际 {actual}），停止后续修改。')


def parse_state(text):
    line = re.search(r'^\s*User 0:\s*([^\n]*)', text, re.MULTILINE)
    if not line or not re.search(r'\binstalled=true\b', line.group(1)):
        raise ToolError('无法确认该包在用户 0 中已安装。')
    state = re.search(r'\benabled=(\d+)\b', line.group(1))
    if not state or int(state.group(1)) not in STATE_COMMANDS:
        raise ToolError('无法解析原始启用状态；未进行修改。')
    return int(state.group(1))


def save(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    os.replace(temporary, path)


def new_record(adb, kind, backup_dir):
    data = {'schema': 1, 'kind': kind, 'created': dt.datetime.now(dt.timezone.utc).isoformat(),
            'device': adb.identity(), 'entries': []}
    path = Path(backup_dir) / (dt.datetime.now().strftime('%Y%m%d-%H%M%S-') + uuid.uuid4().hex[:8] + '.json')
    return path, data


def confirm(text):
    print(text)
    if input('输入 YES 执行，其他输入取消：').strip() != 'YES':
        raise ToolError('已取消。')


def selection(args):
    if args.packages:
        unknown = set(args.packages) - set(ITEMS)
        if unknown:
            raise ToolError('仅允许清单中的包名：' + ', '.join(sorted(unknown)))
        return list(dict.fromkeys(args.packages))
    print('默认全部不选。以下每项均可独立停用；输入编号（空格分隔），直接回车取消。')
    all_items = list(ITEMS.values())
    for index, item in enumerate(all_items, 1):
        print(f"\n[ ] {index:2}. {item['label']} [{CATALOG['groups'][item['group']]}]\n    {item['package']}\n    影响：{item['effect']}")
    raw = input('\n选择编号：').strip()
    if not raw:
        raise ToolError('未选择任何项。')
    try:
        numbers = list(dict.fromkeys(int(n) for n in raw.split()))
        if any(n < 1 or n > len(all_items) for n in numbers):
            raise ValueError()
        return [all_items[n - 1]['package'] for n in numbers]
    except ValueError:
        raise ToolError('请输入清单范围内的整数编号。')


def apply_services(adb, packages, backup_dir, dry_run=False):
    installed = adb.installed()
    changes = []
    for pkg in packages:
        if pkg not in installed:
            print(f'跳过（未安装）：{ITEMS[pkg]["label"]}')
            continue
        state = adb.state(pkg)
        if state in (2, 3, 4):
            print(f'跳过（原已停用）：{ITEMS[pkg]["label"]}')
            continue
        changes.append({'package': pkg, 'before': state, 'after': 3, 'status': 'pending'})
        print(f"停用：{ITEMS[pkg]['label']} ({pkg})\n  {ITEMS[pkg]['effect']}")
    if not changes:
        print('没有需要改动的项目。')
        return
    if dry_run:
        print('预览结束，未写入设备或备份。')
        return
    confirm(f'将停用 {len(changes)} 项。修改前会保存原始状态。')
    path, data = new_record(adb, 'services', backup_dir)
    data['entries'] = changes
    save(path, data)  # Persist ALL original states before the first mutation.
    print('恢复记录：' + str(path.resolve()))
    try:
        for entry in data['entries']:
            if adb.state(entry['package']) != entry['before']:
                raise ToolError('执行前状态发生变化，已停止。')
            adb.set_state(entry['package'], 3)
            entry['status'] = 'applied'
            save(path, data)
    except (Exception, KeyboardInterrupt):
        print('操作中断，保留恢复记录。请用 restore 命令恢复，勿删除此文件。', file=sys.stderr)
        raise
    print('所选项目已停用并核对。书籍和应用数据未清除。')


def validate_record(data):
    if not isinstance(data, dict) or data.get('schema') != 1 or data.get('kind') != 'services':
        raise ToolError('不支持此恢复记录格式。')
    device = data.get('device')
    if not isinstance(device, dict) or not all(isinstance(device.get(k), str) and device[k] for k in ('serial', 'fingerprint')):
        raise ToolError('恢复记录缺少完整设备标识。')
    entries = data.get('entries')
    if not isinstance(entries, list):
        raise ToolError('恢复记录缺少条目。')
    seen = set()
    for entry in entries:
        if not isinstance(entry, dict):
            raise ToolError('恢复记录条目格式无效。')
        pkg = entry.get('package')
        if not isinstance(pkg, str) or pkg not in ITEMS or pkg in seen or type(entry.get('before')) is not int or entry['before'] not in STATE_COMMANDS or entry.get('after') != 3:
            raise ToolError('恢复记录包含无效或重复条目。')
        seen.add(pkg)


def restore_services(adb, path):
    path = Path(path)
    data = json.loads(path.read_text(encoding='utf-8'))
    validate_record(data)
    current = adb.identity()
    if any(current[k] != data.get('device', {}).get(k) for k in ('serial', 'fingerprint')):
        raise ToolError('设备或固件与记录不一致，停止恢复。升级前请先恢复；升级后的处理需人工核对。')
    pending = []
    for entry in data['entries']:
        state = adb.state(entry['package'])
        if state == entry['before']:
            continue
        if state != 3:
            raise ToolError('设备状态与本次操作不一致，请先核对其他工具造成的修改。')
        pending.append(entry)
        print(f"恢复：{entry['package']} → 原状态 {entry['before']}")
    if not pending:
        print('所有条目均已处于原始状态。')
        return
    confirm(f'将恢复 {len(pending)} 项。请先恢复最近一份记录，再处理更早的记录。')
    for entry in pending:
        adb.set_state(entry['package'], entry['before'])
        entry['status'] = 'restored'
        save(path, data)
    print('原始启用状态已恢复并核对。')


def restore_home(adb, backup_dir):
    # Restrict to a known, actually resolvable BOOX launcher before changing HOME.
    component = 'com.onyx/.StartupActivity'
    resolved = adb.run('cmd', 'package', 'resolve-activity', '--brief', '--user', '0', '-n', component)
    if not any(line.startswith('com.onyx/') for line in resolved.splitlines()):
        raise ToolError('无法确认原厂桌面可用，请通过系统设置选择默认首页。')
    previous = adb.run('cmd', 'package', 'resolve-activity', '--brief', '-a',
                       'android.intent.action.MAIN', '-c', 'android.intent.category.HOME')
    confirm('将默认首页改回文石原厂桌面。服务停用状态保持。')
    path, data = new_record(adb, 'home-recovery', backup_dir)
    data['previous_home'] = previous
    save(path, data)
    adb.run('cmd', 'package', 'set-home-activity', '--user', '0', component)
    actual = adb.run('cmd', 'package', 'resolve-activity', '--brief', '-a',
                     'android.intent.action.MAIN', '-c', 'android.intent.category.HOME')
    if not any(line.startswith('com.onyx/') for line in actual.splitlines()):
        raise ToolError('原厂默认首页未确认生效，请在系统设置中手动选择。')
    adb.run('am', 'start', '-n', component)
    print('已恢复原厂首页。记录：' + str(path.resolve()))


def main():
    parser = argparse.ArgumentParser(description='文石微信读书极简工具箱：逐项选择、预览、停用与恢复')
    parser.add_argument('--adb', help='ADB 可执行文件路径（默认从 PATH 查找）')
    parser.add_argument('--serial', help='明确选择设备的序列号')
    parser.add_argument('--backup-dir', default=str(ROOT / 'backups'), help='本地恢复记录目录')
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('list', help='离线查看所有可选项目和影响')
    sub.add_parser('status', help='读取已连接设备上的清单状态')
    choose = sub.add_parser('select', help='交互式逐项选择服务并预览确认')
    choose.add_argument('--packages', nargs='+', help='直接列出要停用的清单包名；仍需确认')
    choose.add_argument('--dry-run', action='store_true', help='仅预览，不修改设备')
    restore = sub.add_parser('restore', help='按记录恢复原始状态')
    restore.add_argument('record')
    sub.add_parser('restore-home', help='恢复已启用的文石原厂桌面为默认首页')
    args = parser.parse_args()
    if args.command == 'list':
        for item in ITEMS.values():
            print(f"[{CATALOG['groups'][item['group']]}] {item['label']} · {item['package']}\n  {item['effect']}")
        return
    executable = args.adb or shutil.which('adb')
    if not executable:
        raise ToolError('未找到 ADB。安装官方 Platform Tools 并加入 PATH，或使用 --adb 路径。')
    adb = ADB(executable)
    adb.connect(args.serial)
    if args.command == 'status':
        installed = adb.installed()
        names = {0: '默认', 1: '启用', 2: '停用', 3: '用户停用', 4: '停用直到使用'}
        for item in ITEMS.values():
            state = names[adb.state(item['package'])] if item['package'] in installed else '未安装'
            print(f"{item['label']}: {state} ({item['package']})")
    elif args.command == 'select':
        apply_services(adb, selection(args), args.backup_dir, args.dry_run)
    elif args.command == 'restore':
        restore_services(adb, args.record)
    elif args.command == 'restore-home':
        restore_home(adb, args.backup_dir)


if __name__ == '__main__':
    try:
        main()
    except (ToolError, OSError, ValueError, subprocess.SubprocessError) as error:
        print('错误：' + str(error), file=sys.stderr)
        sys.exit(1)
    except (KeyboardInterrupt, EOFError):
        print('\n操作结束。若执行已开始，请保留恢复记录。', file=sys.stderr)
        sys.exit(130)
