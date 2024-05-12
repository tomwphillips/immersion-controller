import datetime

import pytest
import responses
from responses.matchers import query_param_matcher

from immersion_controller.switches import ShellyProEM, SwitchException


class TestShellyProEM:
    @responses.activate
    def test_on_with_timer(self):
        url = "http://192.168.0.2"
        on_for = datetime.timedelta(seconds=5)

        turn_on_response = responses.get(
            url + "/relay/0",
            match=[
                query_param_matcher(
                    params={
                        "turn": "on",
                        "timer": on_for.seconds,
                    }
                )
            ],
            json={
                "ison": True,
                "has_timer": True,
                "timer_duration": 5.0,
            },  # also timer_started_at and timer_remaining but don't need those
        )

        shelly = ShellyProEM(url)
        off_at = datetime.datetime.now(tz=datetime.timezone.utc) + on_for
        shelly.turn_on(until=off_at)

        assert turn_on_response.call_count == 1

    def test_on_without_timer_raises_not_implemented_error(self):
        with pytest.raises(NotImplementedError):
            ShellyProEM("http://whatever").turn_on()

    @responses.activate
    def test_turn_on_raises_exception_if_not_200_response(self):
        url = "http://192.168.0.2"
        responses.get(url + "/relay/0", status=400)
        with pytest.raises(SwitchException):
            ShellyProEM(url).turn_on(
                until=datetime.datetime.now(tz=datetime.timezone.utc)
                + datetime.timedelta(seconds=1)
            )
