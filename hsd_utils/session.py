"""
Shared HSD REST API session factory and constants.
"""
import requests
import urllib3
from requests_kerberos import HTTPKerberosAuth, OPTIONAL

urllib3.disable_warnings()

BASE    = "https://hsdes-api.intel.com/rest"
TENANT  = "server"
HSD_URL = "https://hsdes.intel.com/appstore/article-one/#/{}"

# Email notification preference
# ──────────────────────────────
# Adding {"send_mail": "false"} inside fieldValues suppresses HSD email
# notifications and returns HTTP 200.  Do NOT add it as a top-level body key
# — that causes HTTP 400.  set_field() in operations.py handles this correctly.
SEND_MAIL = False  # sentinel — actual suppression is done in operations.set_field()

_HEADERS = {
    "Accept": "application/json",
    "Content-Type": "application/json",
}


def get_session() -> requests.Session:
    """Return a requests.Session pre-configured with Kerberos auth and JSON headers."""
    s = requests.Session()
    s.auth = HTTPKerberosAuth(mutual_authentication=OPTIONAL)
    s.verify = False
    s.headers.update(_HEADERS)
    return s
