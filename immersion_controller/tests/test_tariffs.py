from datetime import datetime, timedelta, timezone

import pytest
import responses
from responses.matchers import query_param_matcher

from immersion_controller.tariffs import (
    OctopusEnergyTariff,
    Tariff,
    TariffException,
    decode_iso8601,
    encode_iso8601,
)


def test_decode_iso8601_timestamp():
    got = decode_iso8601("2023-03-26T01:00:00Z")
    want = datetime(2023, 3, 26, 1, 0, 0, tzinfo=timezone.utc)
    assert got == want


def test_encode_iso8601_timestamp():
    got = encode_iso8601(datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc))
    want = "2024-01-01T00:00:00Z"
    assert got == want


def test_encode_iso8601_timestamp_requires_utc():
    with pytest.raises(ValueError):
        encode_iso8601(datetime.now())


class TestTariff:
    def test_get_rate_is_not_implemented(self):
        with pytest.raises(NotImplementedError):
            Tariff().get_rate(datetime.now(tz=timezone.utc))


class TestOctopusEnergyElectricityTariff:
    @responses.activate
    def test_get_electricity_rate(self):
        price_url = "https://host"
        when = datetime(2024, 1, 1, 12, 3, tzinfo=timezone.utc)

        # electricity rates are returned reverse chronologically
        responses.get(
            price_url,
            match=[query_param_matcher({"period_from": when.isoformat()})],
            json={
                "results": sorted(
                    [
                        {
                            "value_inc_vat": 1.0,
                            "valid_from": encode_iso8601(
                                when.replace(minute=0) + (i * timedelta(minutes=30))
                            ),
                            "valid_to": encode_iso8601(
                                when.replace(minute=0)
                                + ((i + 1) * timedelta(minutes=30))
                            ),
                        }
                        for i in range(4)
                    ],
                    key=lambda unit_rate: unit_rate["valid_from"],
                    reverse=True,
                )  # API returns it in reverse order
            },
        )
        tariff = OctopusEnergyTariff(price_url)
        current_rate = tariff.get_rate(when)
        assert when >= current_rate.valid_from
        assert when < current_rate.valid_to

    @responses.activate
    def test_get_gas_rate(self):
        price_url = "https://host"
        when = datetime(2024, 5, 5, 20, 32, tzinfo=timezone.utc)

        # gas tariffs return two prices depending on payment method
        responses.get(
            price_url,
            match=[query_param_matcher({"period_from": when.isoformat()})],
            json={
            "results": [
                {
                    "value_exc_vat": 5.728,
                    "value_inc_vat": 6.0144,
                    "valid_from": "2024-03-31T23:00:00Z",
                    "valid_to": None,
                    "payment_method": "DIRECT_DEBIT"
                },
                {
                    "value_exc_vat": 5.902,
                    "value_inc_vat": 6.1971,
                    "valid_from": "2024-03-31T23:00:00Z",
                    "valid_to": None,
                    "payment_method": "NON_DIRECT_DEBIT"
                },
            ]
        }
        )
        tariff = OctopusEnergyTariff(price_url)
        current_rate = tariff.get_rate(when)
        assert current_rate.valid_from == datetime(2024, 3, 31, 23, tzinfo=timezone.utc)
        assert current_rate.valid_to is None
        assert current_rate.value == 6.0144

    @responses.activate
    def test_exception_raised_when_non_200_status_returned(self):
        price_url = "https://host"
        when = datetime(2024, 1, 1, 12, 3, tzinfo=timezone.utc)

        responses.get(
            price_url,
            match=[query_param_matcher({"period_from": when.isoformat()})],
            json={},
            status=400,
        )
        tariff = OctopusEnergyTariff(price_url)
        with pytest.raises(TariffException, match="status code != 200"):
            tariff.get_rate(when)

    @responses.activate
    def test_exception_raised_when_rate_unavailable(self):
        price_url = "https://host"
        when = datetime(2024, 1, 1, 12, 3, tzinfo=timezone.utc)

        responses.get(
            price_url,
            match=[query_param_matcher({"period_from": when.isoformat()})],
            json={"results": []},
        )
        tariff = OctopusEnergyTariff(price_url)
        with pytest.raises(TariffException, match="rate for .* unavailable"):
            tariff.get_rate(when)


# TODO: drop non-direct debit payments