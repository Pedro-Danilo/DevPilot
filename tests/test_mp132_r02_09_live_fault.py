"""Real localhost HTTP process crash mid-request: no Ollama instance touched."""
from __future__ import annotations
import concurrent.futures
import socket
import subprocess
import sys
import urllib.error
import urllib.request
import pytest

SERVER = r'''
from http.server import BaseHTTPRequestHandler,HTTPServer
import sys
class Handler(BaseHTTPRequestHandler):
 def do_POST(self):
  print('REQUEST_RECEIVED',flush=True)
  import time
  time.sleep(15)
 def log_message(self,*args): pass
h=HTTPServer(('127.0.0.1',int(sys.argv[1])),Handler)
print('READY',flush=True)
h.serve_forever()
'''


def test_real_loopback_server_terminated_during_request():
    with socket.socket() as s:
        s.bind(('127.0.0.1',0)); port=s.getsockname()[1]
    proc=subprocess.Popen([sys.executable,'-u','-c',SERVER,str(port)],
        stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    try:
        assert proc.stdout.readline().strip()=='READY'
        request=urllib.request.Request(f'http://127.0.0.1:{port}/api/generate',data=b'{}',method='POST')
        def perform():
            try:
                urllib.request.urlopen(request,timeout=4).read()
            except (urllib.error.URLError,OSError,ConnectionError) as e:
                return type(e).__name__
            return 'UNEXPECTED_SUCCESS'
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            future=pool.submit(perform)
            assert proc.stdout.readline().strip()=='REQUEST_RECEIVED'
            proc.kill()
            assert future.result(timeout=6)!='UNEXPECTED_SUCCESS'
    finally:
        if proc.poll() is None: proc.kill()
        proc.communicate(timeout=5)
