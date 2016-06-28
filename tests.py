from unittest import TestCase
import logging
import io
from closure.tracker import analyze_modules
import sys
import os

handler = logging.StreamHandler(sys.stderr)
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s') 
handler.setFormatter(formatter)
    
root_logger = logging.getLogger()
root_logger.addHandler(handler)
root_logger.setLevel(logging.DEBUG)

log = logging.getLogger(__name__)

def read_test_file(fn):
    filename = os.path.join(os.path.join(os.path.dirname(__file__),"testdata"),fn)
    with io.open(filename) as file:
        return file.read()
        
class TestTracker(TestCase):

    def testSample1(self):
        modules,requirements,isbase = analyze_modules(read_test_file("sample1.js"))
        log.info("modules = [%s]"%modules)
        log.info("requirements = [%s]"%requirements)
        log.info("isbase = [%s]"%isbase)
        self.assertEqual(["redundant.stuff","redundant.stuff.Foo"],modules)
        self.assertEqual(["redundant.stuff.Baz","redundant.stuff.Bar"],requirements)
        self.assertEqual(False,isbase)

    def testSample2(self):
        modules,requirements,isbase = analyze_modules(read_test_file("sample2.js"))
        log.info("modules = [%s]"%modules)
        log.info("requirements = [%s]"%requirements)
        log.info("isbase = [%s]"%isbase)
        self.assertEqual([],modules)
        self.assertEqual([],requirements)
        self.assertEqual(True,isbase)
