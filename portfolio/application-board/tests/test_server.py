import http.client
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
import importlib.util

path=Path(__file__).resolve().parents[1]/'server.py'
spec=importlib.util.spec_from_file_location('board_server',path)
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)

class ServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server=ThreadingHTTPServer(('127.0.0.1',0),module.Handler)
        cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True);cls.thread.start()
    @classmethod
    def tearDownClass(cls):cls.server.shutdown();cls.server.server_close();cls.thread.join()
    def request(self,path='/',method='GET',headers=None):
        conn=http.client.HTTPConnection('127.0.0.1',self.server.server_port)
        conn.request(method,path,headers=headers or {});r=conn.getresponse();result=(r.status,dict(r.getheaders()),r.read());conn.close();return result
    def test_index(self):self.assertEqual(self.request()[0],200)
    def test_only_allowlisted_files(self):self.assertEqual(self.request('/server.py')[0],404)
    def test_traversal(self):self.assertEqual(self.request('/../README.md')[0],404)
    def test_host_guard(self):self.assertEqual(self.request(headers={'Host':'evil.invalid'})[0],403)
    def test_cross_site_guard(self):self.assertEqual(self.request(headers={'Sec-Fetch-Site':'cross-site'})[0],403)
    def test_no_data_write_api(self):self.assertEqual(self.request(method='POST')[0],405)
    def test_csp_blocks_network_clients(self):self.assertIn("connect-src 'none'",self.request()[1]['Content-Security-Policy'])
    def test_javascript_mime(self):self.assertIn('text/javascript',self.request('/core.mjs')[1]['Content-Type'])
    def test_new_modules_with_version_queries(self):
        for name in ['explore.mjs','journey.mjs','positions.mjs','radar.mjs']:
            self.assertEqual(self.request('/'+name+'?v=04')[0],200)
if __name__=='__main__':unittest.main()
