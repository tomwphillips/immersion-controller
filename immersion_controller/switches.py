import datetime
import logging

import requests

logger = logging.getLogger(__name__)


class Switch:
    def turn_on(self, until=None):
        raise NotImplementedError()

    def turn_off(self):
        raise NotImplementedError()


class SwitchException(Exception):
    pass


class ShellyProEM(Switch):
    def __init__(self, url):
        self.url = url

    def turn_on(self, until=None):
        if until is None:
            raise NotImplementedError()
        on_for = until - datetime.datetime.now(tz=datetime.timezone.utc)
        response = requests.get(
            f"{self.url}/relay/0",
            params={"turn": "on", "timer": round(on_for.total_seconds())},
        )

        try:
            response.raise_for_status()
        except requests.HTTPError as http_error:
            raise SwitchException(http_error) from http_error

        decoded_body = response.json()
        if is_on := decoded_body.get("ison") is not True:
            raise SwitchException(f"Expected ison to be True, got {is_on}")

        if has_timer := decoded_body.get("has_timer") is not True:
            raise SwitchException(f"Expected has_timer to be True, got {has_timer}")

        logger.info(f"switch on until {until}")
