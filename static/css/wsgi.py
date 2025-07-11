"""
WSGI entry point for PythonAnywhere deployment.

This file is used ONLY when deploying on PythonAnywhere or another WSGI server.
If you are running the app locally for development, you should use:

    flask run

or

    python app.py

You do NOT need to run this file directly.

It exposes the WSGI-compatible 'application' object for the server to run.
"""

import sys
import os

# Add your project directory to the sys.path
project_home = os.path.dirname(os.path.abspath(__file__))
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Set environment variable (optional, but good practice)
os.environ['FLASK_ENV'] = 'production'

# Import your Flask app
from app import app as application