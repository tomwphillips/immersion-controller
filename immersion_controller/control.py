import logging
import time
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class ControllerException(Exception):
    pass


def sleep_until(dt):
    now = datetime.now(tz=timezone.utc)
    duration = dt - now
    logger.info(f"sleeping until {dt}")
    time.sleep(duration.total_seconds())


class Controller:
    def __init__(
        self, electricity_agreement, gas_agreement, switch, sleep_until=sleep_until
    ):
        self.electricity_agreement = electricity_agreement
        self.gas_agreement = gas_agreement
        self.switch = switch
        self.sleep_until = sleep_until

    def run(self, periods=None):
        def loop(periods):
            if periods is not None:
                yield from range(periods)
            else:
                count = 0
                while True:
                    count += 1
                    yield count

        for _ in loop(periods):
            now = datetime.now(tz=timezone.utc)
            electricity_rate = self.electricity_agreement.get_rate(now)
            gas_rate = self.gas_agreement.get_rate(now)

            turn_on = electricity_rate.value <= gas_rate.value

            logger.info(
                f"gas rate = {gas_rate.value}, "
                f"electricity rate = {electricity_rate.value}, "
                f"turn on = {turn_on}"
            )
            if turn_on:
                self.switch.turn_on(electricity_rate.valid_to)

            self.sleep_until(electricity_rate.valid_to)
