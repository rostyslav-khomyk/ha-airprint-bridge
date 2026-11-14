"""Admin-only HA ingress panel. All printer writes require explicit POST actions."""
import hmac
import html
import datetime
from collections import deque
import json
import pathlib
import secrets
import subprocess
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit
import cups

CSRF = secrets.token_urlsafe(32)
LOCK = threading.Lock()
QUEUE = 'bridge'
EVENTS = deque(maxlen=50)
EVENT_LOCK = threading.Lock()

def event(action, outcome, message):
    with EVENT_LOCK:
        EVENTS.appendleft({'time': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'action': action, 'outcome': outcome, 'message': message})

STATES = {3: 'Pending', 4: 'Held', 5: 'Processing', 6: 'Stopped', 7: 'Cancelled', 8: 'Aborted', 9: 'Completed'}

def connection():
    return cups.Connection(host='127.0.0.1', port=631)

def allowed_peer(peer):
    return peer == '172.30.32.2'

def validate_action(action, confirmation):
    required = {'nozzle': 'PRINT', 'clean': 'CLEAN', 'power': 'POWER CLEAN', 'reset': 'PADS SERVICED'}
    if action not in {'status', *required}:
        raise ValueError('Unknown action')
    if action in required and confirmation != required[action]:
        raise ValueError('The confirmation phrase does not match')

def printer_host():
    opts = json.loads(pathlib.Path('/data/options.json').read_text())
    return urlsplit(opts['printer_uri']).hostname

def maintenance(action, confirmation):
    validate_action(action, confirmation)
    if not LOCK.acquire(blocking=False):
        raise ValueError('A maintenance operation is already running')
    try:
        conn = connection()
        if action != 'status' and conn.getJobs(which_jobs='not-completed'):
            raise ValueError('Wait for all print jobs to finish first')
        result = subprocess.run(['/opt/maintenance-venv/bin/python', '/opt/epson-maintenance/worker.py', action, printer_host()], capture_output=True, text=True, timeout=120)
        data = json.loads(result.stdout)
        if result.returncode:
            raise ValueError(data.get('error', 'Maintenance failed'))
        return data
    finally:
        LOCK.release()

def snapshot():
    conn = connection()
    printer = conn.getPrinterAttributes(QUEUE)
    jobs = conn.getJobs(which_jobs='all')
    return {'printer': {'state': printer.get('printer-state'), 'message': printer.get('printer-state-message'), 'reasons': printer.get('printer-state-reasons'), 'model': printer.get('printer-make-and-model')},
            'jobs': [{'id': key, 'name': value.get('job-name', ''), 'state': STATES.get(value.get('job-state'), 'Unknown'), 'created': value.get('time-at-creation'), 'pages': value.get('job-impressions-completed')} for key, value in sorted(jobs.items(), reverse=True)][:20]}

class Handler(BaseHTTPRequestHandler):
    def reply(self, code, payload, content_type='application/json'):
        body = payload.encode() if isinstance(payload, str) else json.dumps(payload).encode()
        self.send_response(code)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.end_headers()
        self.wfile.write(body)

    def authorized(self):
        if not allowed_peer(self.client_address[0]):
            self.reply(403, {'error': 'Use Home Assistant Open Web UI'})
            return False
        return True

    def do_GET(self):
        if not self.authorized():
            return
        try:
            if self.path == '/health':
                subprocess.run(['pgrep', '-x', 'ippeveprinter'], check=True, capture_output=True)
                subprocess.run(['pgrep', '-x', 'avahi-daemon'], check=True, capture_output=True)
                connection().getPrinters()
                self.reply(200, {'healthy': True})
            elif self.path == '/api/activity':
                with EVENT_LOCK:
                    self.reply(200, list(EVENTS))
            elif self.path == '/api/status':
                self.reply(200, snapshot())
            elif self.path == '/':
                base = self.headers.get('X-Ingress-Path', '').rstrip('/') + '/'
                page = pathlib.Path('/opt/panel/panel.html').read_text().replace('__CSRF__', CSRF).replace('__BASE__', html.escape(base, quote=True))
                self.reply(200, page, 'text/html; charset=utf-8')
            else:
                self.reply(404, {'error': 'Not found'})
        except Exception as error:
            self.reply(503, {'error': str(error)})

    def do_POST(self):
        if not self.authorized():
            return
        if not hmac.compare_digest(self.headers.get('X-CSRF-Token', ''), CSRF):
            self.reply(403, {'error': 'Reload this panel before continuing'})
            return
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if not 0 < length <= 4096:
                raise ValueError('Invalid request size')
            data = json.loads(self.rfile.read(length))
            action = data.get('action', 'unknown')
            if self.path != '/api/maintenance':
                self.reply(404, {'error': 'Not found'})
                return
            event(action, 'started', 'Request received')
            result = maintenance(action, data.get('confirmation', ''))
            if result.get('success') is False:
                raise ValueError('The printer did not verify the operation. Review /data/maintenance before retrying.')
            event(action, 'completed', 'Request completed; check physical output for print/clean actions')
            self.reply(200, result)
        except Exception as error:
            event(locals().get('action', 'request'), 'failed', str(error))
            self.reply(400, {'error': str(error)})

    def log_message(self, *_):
        pass

if __name__ == '__main__':
    ThreadingHTTPServer(('0.0.0.0', 8098), Handler).serve_forever()
