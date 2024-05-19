import time
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, call

import pytest

from immersion_controller.control import Controller, sleep_until
from immersion_controller.octopus.account import Agreement, AgreementException, UnitRate
from immersion_controller.switches import Switch, SwitchException


def test_controller_for_specified_loops():
    gas_rate = UnitRate(
        value=1,
        valid_from=datetime(2024, 1, 1, tzinfo=timezone.utc),
        valid_to=datetime(2034, 1, 1, tzinfo=timezone.utc),
    )
    gas_agreement = Mock(spec_set=Agreement, **{"get_rate.return_value": gas_rate})

    less_than_gas = gas_rate.value - 1
    more_than_gas = gas_rate.value + 1
    electricity_rates = [
        UnitRate(
            value=more_than_gas,
            valid_from=datetime(2024, 4, 1, 0, 0, 0, tzinfo=timezone.utc),
            valid_to=datetime(2024, 4, 1, 0, 30, 0, tzinfo=timezone.utc),
        ),
        UnitRate(
            value=less_than_gas,
            valid_from=datetime(2024, 4, 1, 0, 30, 0, tzinfo=timezone.utc),
            valid_to=datetime(2024, 4, 1, 1, 0, 0, tzinfo=timezone.utc),
        ),
        UnitRate(
            value=more_than_gas,
            valid_from=datetime(2024, 4, 1, 1, 0, 0, tzinfo=timezone.utc),
            valid_to=datetime(2024, 4, 1, 1, 30, 0, tzinfo=timezone.utc),
        ),
        UnitRate(
            value=gas_rate.value,
            valid_from=datetime(2024, 4, 1, 1, 30, 0, tzinfo=timezone.utc),
            valid_to=datetime(2024, 4, 1, 2, 0, 0, tzinfo=timezone.utc),
        ),
    ]
    electricity_agreement = Mock(
        spec_set=Agreement, **{"get_rate.side_effect": electricity_rates}
    )

    switch = Mock(spec_set=Switch)
    sleep_until = Mock()

    controller = Controller(electricity_agreement, gas_agreement, switch, sleep_until)
    controller.run(len(electricity_rates))

    switch.turn_on.assert_has_calls(
        [
            call.turn_on(electricity_rates[1].valid_to),
            call.turn_on(electricity_rates[3].valid_to),
        ]
    )
    sleep_until.assert_has_calls(
        [call(electricity_rate.valid_to) for electricity_rate in electricity_rates]
    )


def test_controller_shutdown_on_electricity_agreement_exception():
    gas_rate = UnitRate(
        value=1,
        valid_from=datetime(2024, 1, 1, tzinfo=timezone.utc),
        valid_to=datetime(2034, 1, 1, tzinfo=timezone.utc),
    )
    gas_agreement = Mock(spec_set=Agreement, **{"get_rate.return_value": gas_rate})

    less_than_gas = gas_rate.value - 1
    more_than_gas = gas_rate.value + 1
    electricity_rates = [
        UnitRate(
            value=more_than_gas,
            valid_from=datetime(2024, 4, 1, 0, 0, 0, tzinfo=timezone.utc),
            valid_to=datetime(2024, 4, 1, 0, 30, 0, tzinfo=timezone.utc),
        ),
        UnitRate(
            value=less_than_gas,
            valid_from=datetime(2024, 4, 1, 0, 30, 0, tzinfo=timezone.utc),
            valid_to=datetime(2024, 4, 1, 1, 0, 0, tzinfo=timezone.utc),
        ),
        AgreementException,
    ]
    electricity_agreement = Mock(
        spec_set=Agreement, **{"get_rate.side_effect": electricity_rates}
    )

    switch = Mock(spec_set=Switch)
    sleep_until = Mock()

    controller = Controller(electricity_agreement, gas_agreement, switch, sleep_until)
    with pytest.raises(AgreementException):
        controller.run()  # run forever, but shuts down on exception

    switch.turn_on.assert_has_calls(
        [
            call.turn_on(electricity_rates[1].valid_to),
        ]
    )
    sleep_until.assert_has_calls(
        [call(electricity_rate.valid_to) for electricity_rate in electricity_rates[:-1]]
    )


def test_controller_shutdown_on_gas_agreement_exception():
    gas_rate = UnitRate(
        value=1,
        valid_from=datetime(2024, 1, 1, tzinfo=timezone.utc),
        valid_to=datetime(2034, 1, 1, tzinfo=timezone.utc),
    )
    gas_agreement = Mock(
        spec_set=Agreement, **{"get_rate.side_effect": [gas_rate, AgreementException]}
    )

    less_than_gas = gas_rate.value - 1
    more_than_gas = gas_rate.value + 1
    electricity_rates = [
        UnitRate(
            value=more_than_gas,
            valid_from=datetime(2024, 4, 1, 0, 0, 0, tzinfo=timezone.utc),
            valid_to=datetime(2024, 4, 1, 0, 30, 0, tzinfo=timezone.utc),
        ),
        UnitRate(
            value=less_than_gas,
            valid_from=datetime(2024, 4, 1, 0, 30, 0, tzinfo=timezone.utc),
            valid_to=datetime(2024, 4, 1, 1, 0, 0, tzinfo=timezone.utc),
        ),
    ]
    electricity_agreement = Mock(
        spec_set=Agreement, **{"get_rate.side_effect": electricity_rates}
    )

    switch = Mock(spec_set=Switch)
    sleep_until = Mock()

    controller = Controller(electricity_agreement, gas_agreement, switch, sleep_until)
    with pytest.raises(AgreementException):
        controller.run()  # run forever, but shuts down on exception

    switch.turn_on.assert_not_called()
    sleep_until.assert_called_once_with(electricity_rates[0].valid_to)


def test_controller_shutdown_on_switch_exception():
    gas_rate = UnitRate(
        value=1,
        valid_from=datetime(2024, 1, 1, tzinfo=timezone.utc),
        valid_to=datetime(2034, 1, 1, tzinfo=timezone.utc),
    )
    gas_agreement = Mock(spec_set=Agreement, **{"get_rate.return_value": gas_rate})

    less_than_gas = gas_rate.value - 1
    electricity_rate = UnitRate(
        value=less_than_gas,
        valid_from=datetime(2024, 4, 1, 0, 30, 0, tzinfo=timezone.utc),
        valid_to=datetime(2024, 4, 1, 1, 0, 0, tzinfo=timezone.utc),
    )
    electricity_agreement = Mock(
        spec_set=Agreement, **{"get_rate.return_value": electricity_rate}
    )

    switch = Mock(spec_set=Switch, **{"turn_on.side_effect": SwitchException})
    sleep_until = Mock()

    controller = Controller(electricity_agreement, gas_agreement, switch, sleep_until)
    with pytest.raises(SwitchException):
        controller.run()

    gas_agreement.get_rate.assert_called_once()
    electricity_agreement.get_rate.assert_called_once()
    switch.turn_on.assert_called_once_with(electricity_rate.valid_to)
    sleep_until.assert_not_called()


def test_sleep_until(monkeypatch):
    mock_sleep = Mock()
    monkeypatch.setattr(time, "sleep", mock_sleep)

    tic = datetime.now(tz=timezone.utc)
    pause_for = timedelta(seconds=1)
    sleep_until(tic + pause_for)

    mock_sleep.assert_called_once()
    (called_seconds,), _ = mock_sleep.call_args
    assert round(called_seconds) == pause_for.seconds
