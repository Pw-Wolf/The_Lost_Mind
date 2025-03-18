import time
import requests

try:
    from updates.constant import VERSION
except:
    from updates.constant import VERSION

# Suppress only the single InsecureRequestWarning from urllib3 needed for this use case
requests.packages.urllib3.disable_warnings()

URL = "https://localhost:1234"


def structure_scoreboard(text):
    """
    Structure the scoreboard data
    This is not available for public use
    """


def get_score(limit=10, name=""):
    """
    Get the scoreboard from the server
    This is not available for public use
    """


def send_score(score, name):
    """
    Send score to the server
    This is not available for public use
    """
