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

    def test_reset_requires_confirmation_but_cleaning_buttons_are_direct(self):
        for action in ['reset']:
            with self.assertRaises(ValueError):
                panel.validate_action(action, '')
        panel.validate_action('reset', 'PADS SERVICED')
        for action in ['clean', 'power', 'nozzle']:
            panel.validate_action(action, '')
        with self.assertRaises(ValueError):
            panel.validate_action('arbitrary-command', 'PADS SERVICED')

    def test_bad_confirmation_never_reaches_printer(self):
        with patch.object(panel, 'connection') as connect:
            with self.assertRaises(ValueError):
                panel.maintenance('reset', 'wrong')
            connect.assert_not_called()

class MaintenanceIdentityTests(unittest.TestCase):
    def load_worker(self, printer):
        modules = {'epson_print_conf': types.SimpleNamespace(EpsonPrinter=lambda **_: printer),
                   'epson_escp2': types.ModuleType('epson_escp2'),
                   'epson_escp2.epson_encode': types.SimpleNamespace(EpsonEscp2=object),
                   'pyprintlpr': types.SimpleNamespace(LprClient=object)}
        with patch.dict(sys.modules, modules):
            spec = importlib.util.spec_from_file_location('worker', PATH.parent / 'maintenance' / 'worker.py')
            worker = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(worker)
        return worker

    def test_wrong_printer_is_rejected_before_reset(self):
        from unittest.mock import Mock
        printer = Mock()
        printer.get_snmp_info.return_value = {'Model': 'EPSON ET-2550 Series'}
        worker = self.load_worker(printer)
        with self.assertRaises(ValueError):
            worker.execute('reset', 'printer.local')
        printer.reset_waste_ink_levels.assert_not_called()
        printer.read_eeprom.assert_not_called()

    def test_status_works_without_eeprom_model_field(self):
        from unittest.mock import Mock
        printer = Mock()
        printer.get_snmp_info.return_value = {'Model': 'EPSON ET-2500 Series'}
        printer.get_printer_status.return_value = {'status': [4, 'Idle']}
        printer.get_waste_ink_levels.return_value = {'main_waste': 54.25}
        result = self.load_worker(printer).execute('status', 'printer.local')
        self.assertEqual(result['waste']['main_waste'], 54.25)
        printer.get_printer_model.assert_not_called()
        printer.reset_waste_ink_levels.assert_not_called()

class JobHistoryProtocolTests(unittest.TestCase):
    def test_requests_ids_and_fields_needed_by_history(self):
        from unittest.mock import Mock
        conn = Mock()
        conn.getPrinterAttributes.return_value = {'printer-state': 3}
        def get_jobs(**kwargs):
            requested = kwargs.get('requested_attributes', ['job-id', 'job-uri'])
            if 'job-id' not in requested:
                return {}
            values = {'job-name': 'Test document', 'job-state': 9, 'time-at-creation': 1}
            return {1: {key: value for key, value in values.items() if key in requested}}
        conn.getJobs.side_effect = get_jobs
        with patch.object(panel, 'connection', return_value=conn):
            job = panel.snapshot()['jobs'][0]
        self.assertEqual(job['state'], 'Completed')
        self.assertEqual(job['name'], 'Test document')
