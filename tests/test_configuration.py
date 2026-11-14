import pathlib
import subprocess
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
APP = ROOT / 'airprint_bridge'

class DeploymentTests(unittest.TestCase):
    def test_a4_color_simplex_and_airprint_formats(self):
        attrs = subprocess.check_output(['bash', str(APP / 'make_attrs.sh'), 'A4', 'Epson ET-2500 (HA)', 'true', 'false'], text=True)
        self.assertIn('iso_a4_210x297mm', attrs)
        self.assertNotIn('na_letter', attrs)
        self.assertIn('image/urf', attrs)
        self.assertIn('SRGB24', attrs)
        self.assertIn('ATTR keyword sides-supported one-sided\n', attrs)

    def test_invalid_media_fails(self):
        result = subprocess.run(['bash', str(APP / 'make_attrs.sh'), 'INVALID', 'Epson', 'true', 'false'], capture_output=True)
        self.assertNotEqual(result.returncode, 0)

    def test_cups_is_local_and_does_not_retain_completed_documents(self):
        config = (APP / 'cupsd.conf').read_text()
        self.assertIn('Listen 127.0.0.1:631', config)
        self.assertNotIn('Listen *', config)
        self.assertIn('WebInterface No', config)
        self.assertIn('PreserveJobFiles No', config)

    def test_shell_syntax(self):
        for path in APP.glob('*.sh'):
            subprocess.run(['bash', '-n', str(path)], check=True)

if __name__ == '__main__':
    unittest.main()
