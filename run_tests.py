
import unittest
import os
import sys

# Ensure root dir is in path
ROOT_DIR = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, ROOT_DIR)

if __name__ == '__main__':
    loader = unittest.TestLoader()
    start_dir = os.path.join(ROOT_DIR, 'tests')
    
    # Discovery
    suite = loader.discover(start_dir, pattern='test_*.py')

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    sys.exit(not result.wasSuccessful())
