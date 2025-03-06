import os
import sys

# Add the project toor directory to the Python path so we can import it in the tests
current_dir = os.path.dirname(os.path.realpath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, os.pardir))
# project_root = os.path.abspath(os.path.join(current_dir, os.pardir, "sanitext"))
sys.path.insert(0, project_root)
