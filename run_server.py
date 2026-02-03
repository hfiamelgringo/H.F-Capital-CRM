"""Run Django with Waitress (Windows production WSGI server)."""
import os
import sys

# When run as a Windows service there is no console; stdout/stderr can raise
# OSError on flush and cause exit. Redirect to a log file if requested.
_log_path = os.environ.get("RUN_SERVER_LOG")
if _log_path:
    try:
        _log = open(_log_path, "a", encoding="utf-8")
        sys.stdout = sys.stderr = _log
    except OSError:
        pass

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "crm_project.settings")

from waitress import serve
from crm_project.wsgi import application

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    serve(application, host="127.0.0.1", port=port)
