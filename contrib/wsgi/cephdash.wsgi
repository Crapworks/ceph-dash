import sys
import os

# insert the path where the application resided to
# pythons search path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

# application holds the actual wsgi application
from app import app as application
