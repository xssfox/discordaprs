import requests
import os
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import logging

class TimeoutHTTPAdapter(HTTPAdapter):
    def __init__(self, *args, **kwargs):
        self.timeout = 0.5
        if "timeout" in kwargs:
            self.timeout = kwargs["timeout"]
            del kwargs["timeout"]
        super().__init__(*args, **kwargs)

    def send(self, request, **kwargs):
        timeout = kwargs.get("timeout")
        if timeout is None:
            kwargs["timeout"] = self.timeout
        return super().send(request, **kwargs)

retry_strategy = Retry(
    total=3,
    method_whitelist=["POST"]
)

adapter = TimeoutHTTPAdapter(max_retries=retry_strategy)
server = url = "http://205.233.35.46:8080"
def send_message(to_call,from_call,passcode,message):
    s = requests.Session()
    s.mount("http://", adapter)

    to_call = to_call.upper()
    from_call = from_call.upper()
    message_callsign = to_call.ljust(9, ' ')
    message_payload = f"{os.getenv('SERVER_NAME')}>APRS,TCPIP*::{message_callsign}:{message}"
    http_payload = f"user {from_call} pass {passcode} vers xssfox-discordaprs\n{message_payload}"
    logging.debug(f"sending message:\n {http_payload}")
    headers = {
    'Accept-Type': 'text/plain',
    'Content-Type': 'application/octet-stream'
    }


    response = s.request("POST", url, headers=headers, data=http_payload)

    return response.status_code