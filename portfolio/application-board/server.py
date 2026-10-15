"""Static, loopback-only launcher. Never accepts or persists application data."""
import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

ROOT=Path(__file__).resolve().parent/'dist'
FILES={'/':('index.html','text/html; charset=utf-8'),'/app.mjs':('app.mjs','text/javascript; charset=utf-8'),'/core.mjs':('core.mjs','text/javascript; charset=utf-8'),'/style.css':('style.css','text/css; charset=utf-8')}
for name in ['radar.mjs','matching.mjs','positions.mjs','explore.mjs','journey.mjs','pdf-text.mjs','pdf.min.mjs','pdf.worker.min.mjs','data-quality.mjs','i18n.mjs','tracker-language.mjs']:
    FILES['/'+name]=(name,'text/javascript; charset=utf-8')
FILES['/radar.css']=('radar.css','text/css; charset=utf-8')
FILES['/tracker.html']=('tracker.html','text/html; charset=utf-8')

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        host=self.headers.get('Host','')
        allowed={f'127.0.0.1:{self.server.server_port}',f'localhost:{self.server.server_port}'}
        if host not in allowed or self.headers.get('Sec-Fetch-Site','')=='cross-site':
            self.send_error(403);return
        item=FILES.get(urlsplit(self.path).path)
        if not item:self.send_error(404);return
        data=(ROOT/item[0]).read_bytes()
        self.send_response(200);self.send_header('Content-Type',item[1]);self.send_header('Content-Length',str(len(data)));self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff');self.send_header('Referrer-Policy','no-referrer');self.send_header('Content-Security-Policy',"default-src 'none'; script-src 'self'; worker-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self'; connect-src 'none'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'none'");self.end_headers();self.wfile.write(data)
    def do_POST(self):self.send_error(405)
    def log_message(self,*args):pass

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--port',type=int,default=8907);args=parser.parse_args()
    with ThreadingHTTPServer(('127.0.0.1',args.port),Handler) as server:
        print(f'Application Board: http://127.0.0.1:{server.server_port}/',flush=True);server.serve_forever()
if __name__=='__main__':main()
