import importlib.util
import pathlib
import sys
import types
import unittest
from unittest.mock import patch

PATH = pathlib.Path(__file__).resolve().parents[1] / 'airprint_bridge' / 'panel.py'
with patch.dict(sys.modules, {'cups': types.ModuleType('cups')}):
    spec = importlib.util.spec_from_file_location('panel', PATH)
    panel = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(panel)

class PanelBoundaryTests(unittest.TestCase):
    def test_only_ingress_peer_is_accepted(self):
        self.assertTrue(panel.allowed_peer('172.30.32.2'))
        for peer in ['127.0.0.1', '192.168.2.1', '172.30.32.3']:
            self.assertFalse(panel.allowed_peer(peer))

    def test_no_reset_or_clean_without_matching_confirmation(self):
        for action in ['reset', 'clean', 'power', 'nozzle']:
            with self.assertRaises(ValueError):
                panel.validate_action(action, '')
        panel.validate_action('reset', 'PADS SERVICED')
        with self.assertRaises(ValueError):
            panel.validate_action('arbitrary-command', 'PADS SERVICED')

    def test_bad_confirmation_never_reaches_printer(self):
        with patch.object(panel, 'connection') as connect:
            with self.assertRaises(ValueError):
                panel.maintenance('reset', 'wrong')
            connect.assert_not_called()
