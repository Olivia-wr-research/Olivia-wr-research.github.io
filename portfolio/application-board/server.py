"""Static, loopback-only launcher. Never accepts or persists application data."""
import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

ROOT=Path(__file__).resolve().parent/'dist'
PUBLIC_JSON={'mentor-pilot.json','research-pilot.json','geography-sources.json','geography-official-sources.json','vendor/world-110m.geojson'}
def static_files(root):
    kinds={'.mjs':'text/javascript; charset=utf-8','.js':'text/javascript; charset=utf-8','.css':'text/css; charset=utf-8','.html':'text/html; charset=utf-8','.svg':'image/svg+xml','.png':'image/png','.jpg':'image/jpeg','.jpeg':'image/jpeg','.webp':'image/webp','.ico':'image/x-icon','.woff2':'font/woff2'}
    files={}
    for p in root.rglob('*'):
        if p.is_file() and not p.is_symlink() and p.resolve().is_relative_to(root.resolve()) and (p.suffix in kinds or p.relative_to(root).as_posix() in PUBLIC_JSON) and not any(part.startswith('.') for part in p.relative_to(root).parts):
            files['/'+p.relative_to(root).as_posix()]=(p.relative_to(root).as_posix(),kinds.get(p.suffix,'application/json; charset=utf-8'))
    if '/index.html' in files:files['/']=files['/index.html']
    return files
FILES=static_files(ROOT)

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        host=self.headers.get('Host','')
        allowed={f'127.0.0.1:{self.server.server_port}',f'localhost:{self.server.server_port}'}
        if host not in allowed or self.headers.get('Sec-Fetch-Site','')=='cross-site':
            self.send_error(403);return
        item=FILES.get(urlsplit(self.path).path)
        if not item:self.send_error(404);return
        data=(ROOT/item[0]).read_bytes()
        connect="'none'"
        if getattr(self.server,'preview_static_fetch',False):
            connect=' '.join('http://'+host+'/'+name for name in sorted(PUBLIC_JSON|{'api/mentors','api/research'}))
        self.send_response(200);self.send_header('Content-Type',item[1]);self.send_header('Content-Length',str(len(data)));self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff');self.send_header('Referrer-Policy','no-referrer');self.send_header('Content-Security-Policy',f"default-src 'none'; script-src 'self'; worker-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self'; connect-src {connect}; object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'none'");self.end_headers();self.wfile.write(data)
    def do_POST(self):self.send_error(405)
    def log_message(self,*args):pass

def main():
    global ROOT,FILES
    parser=argparse.ArgumentParser();parser.add_argument('--port',type=int,default=8907);parser.add_argument('--root',type=Path,default=ROOT);parser.add_argument('--preview-static-fetch',action='store_true');args=parser.parse_args()
    ROOT=args.root.resolve();FILES=static_files(ROOT)
    with ThreadingHTTPServer(('127.0.0.1',args.port),Handler) as server:
        server.preview_static_fetch=args.preview_static_fetch
        print(f'Application Board: http://127.0.0.1:{server.server_port}/',flush=True);server.serve_forever()
if __name__=='__main__':main()
