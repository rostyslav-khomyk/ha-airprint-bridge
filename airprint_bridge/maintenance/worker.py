# SPDX-License-Identifier: EUPL-1.2
# Adapter to Ircama/epson_print_conf (see accompanying license and source).
import json
import pathlib
import re
import sys
import time
from epson_print_conf import EpsonPrinter
from epson_escp2.epson_encode import EpsonEscp2
from pyprintlpr import LprClient

ACTIONS = {'status', 'nozzle', 'clean', 'power', 'reset'}

def execute(action, host, backup_dir='/data/maintenance'):
    if action not in ACTIONS:
        raise ValueError('Unknown maintenance action')
    printer = EpsonPrinter(model='ET-2500', hostname=host, timeout=2, retries=0, verify_writes=True)
    model = printer.get_printer_model()
    if not re.fullmatch(r'(?:EPSON\s+)?ET-2500(?:\s+Series)?', str(model).strip(), re.I):
        raise ValueError('Printer identity is not a verified ET-2500: ' + str(model))
    if action == 'status':
        return {'model': model, 'status': printer.get_printer_status(), 'waste': printer.get_waste_ink_levels()}
    if action == 'reset':
        cells = printer.parm['raw_waste_reset']
        before = {str(cell): printer.read_eeprom(cell) for cell in cells}
        if any(value is None for value in before.values()):
            raise ValueError('Could not read every counter byte; reset refused')
        folder = pathlib.Path(backup_dir)
        folder.mkdir(mode=0o700, parents=True, exist_ok=True)
        path = folder / ('counter-before-' + str(time.time_ns()) + '.json')
        path.write_text(json.dumps({'model': model, 'serial': printer.get_serial_number(), 'bytes': before}))
        path.chmod(0o600)
        report = []
        ok = printer.reset_waste_ink_levels(report=report)
        result = {'success': bool(ok), 'backup': path.name, 'verification': report, 'waste': printer.get_waste_ink_levels()}
        (folder / (path.stem + '-result.json')).write_text(json.dumps(result, default=str))
        return result
    codec = EpsonEscp2()
    if action == 'nozzle':
        pattern = codec.check_nozzles(type=0)
    else:
        pattern = codec.clean_nozzles(0, power_clean=(action == 'power'), has_alt_mode=None)
    if not pattern:
        raise ValueError('The maintenance library did not produce a command')
    with LprClient(host, port='LPR', label='Epson maintenance', timeout=30) as client:
        client.send(pattern)
    return {'success': True, 'message': 'Command sent; physical completion is not verified.'}

if __name__ == '__main__':
    try:
        print(json.dumps(execute(sys.argv[1], sys.argv[2]), default=str))
    except Exception as error:
        print(json.dumps({'success': False, 'error': str(error)}))
        sys.exit(1)
