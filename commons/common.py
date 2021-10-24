import os
import time
import io
import logging
import google.cloud.logging

# setup logging

def setup_logging() -> None:
    client = google.cloud.logging.Client()
    client.get_default_handler()
    client.setup_logging(log_level=logging.DEBUG)

class MissingEnvironmentVariable(Exception):
    pass