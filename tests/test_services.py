import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('boox_tool', Path(__file__).resolve().parents[1] / 'tools/boox_tool.py')
tool = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tool)


class FakeADB:
    def __init__(self, states, fail=None):
        self.states = dict(states)
        self.fail = fail
        self.operations = []
        self.backup_dir = None

    def installed(self):
        return set(self.states)

    def state(self, pkg):
        return self.states[pkg]

    def identity(self):
        return {'serial': 'test-device', 'fingerprint': 'test-firmware', 'model': 'Test BOOX'}

    def set_state(self, pkg, state):
        if state == 3:
            # Original states must be on disk before ANY device mutation.
            record = json.loads(next(self.backup_dir.glob('*.json')).read_text())
            assert record['entries'] and all('before' in e for e in record['entries'])
        self.operations.append((pkg, state))
        if pkg == self.fail:
            # Simulate command failure after the device accepted the change.
            self.states[pkg] = state
            raise tool.ToolError('simulated interrupted command')
        self.states[pkg] = state


class ServicesTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.p1 = 'com.onyx.dict'
        self.p2 = 'com.onyx.easytransfer'

    def adb(self, states, fail=None):
        adb = FakeADB(states, fail)
        adb.backup_dir = self.directory
        return adb

    def record(self):
        return next(self.directory.glob('*.json'))

    def test_parse_only_user_zero_and_all_original_states(self):
        for state in range(5):
            self.assertEqual(tool.parse_state(f'User 0: installed=true hidden=false enabled={state}\nUser 10: enabled=4'), state)
        for invalid in ['User 0: installed=true enabled=9', 'User 0: installed=false enabled=0', 'User 10: installed=true enabled=0']:
            with self.assertRaises(tool.ToolError):
                tool.parse_state(invalid)

    def test_preview_has_no_writes(self):
        adb = self.adb({self.p1: 0})
        tool.apply_services(adb, [self.p1], self.directory, dry_run=True)
        self.assertEqual(adb.operations, [])
        self.assertEqual(list(self.directory.iterdir()), [])

    def test_cancel_has_no_writes(self):
        adb = self.adb({self.p1: 0})
        with patch('builtins.input', return_value='no'), self.assertRaises(tool.ToolError):
            tool.apply_services(adb, [self.p1], self.directory)
        self.assertEqual(adb.operations, [])
        self.assertEqual(list(self.directory.iterdir()), [])

    def test_missing_and_previously_disabled_are_untouched(self):
        adb = self.adb({self.p1: 2})
        tool.apply_services(adb, [self.p1, self.p2], self.directory)
        self.assertEqual(adb.operations, [])

    def test_restore_exact_original_state_and_repeat(self):
        adb = self.adb({self.p1: 0, self.p2: 1})
        with patch('builtins.input', return_value='YES'):
            tool.apply_services(adb, [self.p1, self.p2], self.directory)
            tool.restore_services(adb, self.record())
        self.assertEqual(adb.states, {self.p1: 0, self.p2: 1})
        operations = list(adb.operations)
        tool.restore_services(adb, self.record())
        self.assertEqual(adb.operations, operations)

    def test_partial_failure_recover_pending_entry_too(self):
        adb = self.adb({self.p1: 0, self.p2: 1}, fail=self.p2)
        with patch('builtins.input', return_value='YES'), self.assertRaises(tool.ToolError):
            tool.apply_services(adb, [self.p1, self.p2], self.directory)
        data = json.loads(self.record().read_text())
        self.assertEqual([e['status'] for e in data['entries']], ['applied', 'pending'])
        adb.fail = None
        with patch('builtins.input', return_value='YES'):
            tool.restore_services(adb, self.record())
        self.assertEqual(adb.states, {self.p1: 0, self.p2: 1})

    def test_wrong_device_rejected(self):
        adb = self.adb({self.p1: 0})
        with patch('builtins.input', return_value='YES'):
            tool.apply_services(adb, [self.p1], self.directory)
        adb.identity = lambda: {'serial': 'other', 'fingerprint': 'test-firmware'}
        with self.assertRaises(tool.ToolError):
            tool.restore_services(adb, self.record())
        self.assertEqual(adb.states[self.p1], 3)

    def test_external_changes_rejected_before_restore(self):
        adb = self.adb({self.p1: 0, self.p2: 1})
        with patch('builtins.input', return_value='YES'):
            tool.apply_services(adb, [self.p1, self.p2], self.directory)
        adb.states[self.p2] = 4
        before = list(adb.operations)
        with self.assertRaises(tool.ToolError):
            tool.restore_services(adb, self.record())
        self.assertEqual(adb.operations, before)

    def test_malformed_restore_records_rejected(self):
        for record in [[], {}, {'schema': 1, 'kind': 'services', 'entries': []},
                       {'schema': 1, 'kind': 'services', 'device': {'serial': 'test', 'fingerprint': 'test'}, 'entries': [None]}]:
            with self.assertRaises(tool.ToolError):
                tool.validate_record(record)

    def test_multiple_devices_requires_serial(self):
        adb = tool.ADB('unused')
        adb.run = lambda *args, **kwargs: 'List of devices attached\none\tdevice\ntwo\tdevice'
        with self.assertRaises(tool.ToolError):
            adb.connect(None)

    def test_failed_readback_stops_modification(self):
        adb = tool.ADB('unused')
        adb.run = lambda *args, **kwargs: ''
        adb.state = lambda pkg: 0
        with self.assertRaises(tool.ToolError):
            adb.set_state(self.p1, 3)

    def test_unlisted_package_in_record_rejected(self):
        data = {'schema': 1, 'kind': 'services', 'device': {'serial': 'test', 'fingerprint': 'test'}, 'entries': [{'package': 'com.android.systemui', 'before': 0, 'after': 3}]}
        with self.assertRaises(tool.ToolError):
            tool.validate_record(data)


if __name__ == '__main__':
    unittest.main()
