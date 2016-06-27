from unittest import TestCase
import logging
import io
from closure.tracker import analyse_modules
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
        modules = analyse_modules(read_test_file("sample1.js"))
        log.info("modules = [%s]"%modules)
        self.assertEqual(["redundant.stuff","redundant.stuff.Foo"],modules)

