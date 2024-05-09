from datetime import datetime, timedelta, timezone

import pytest
import responses
from responses.matchers import query_param_matcher

from immersion_controller.tariffs import (
    OctopusEnergyTariff,
    OctopusEnergyUnitRateResponseSchema,
    Tariff,
    TariffException,
)


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
                            "valid_from": (
                                when.replace(minute=0) + (i * timedelta(minutes=30))
                            ).isoformat(),
                            "valid_to": (
                                when.replace(minute=0)
                                + ((i + 1) * timedelta(minutes=30))
                            ).isoformat(),
                            "payment_method": None,
                        }
                        for i in range(4)
                    ],
                    key=lambda unit_rate: unit_rate["valid_from"],
                    reverse=True,
                )
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
                        "payment_method": "DIRECT_DEBIT",
                    },
                    {
                        "value_exc_vat": 5.902,
                        "value_inc_vat": 6.1971,
                        "valid_from": "2024-03-31T23:00:00Z",
                        "valid_to": None,
                        "payment_method": "NON_DIRECT_DEBIT",
                    },
                ]
            },
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


def test_unit_rate_api_response_deserialisation():
    json_encoded_api_response = """{
  "count": 4,
  "next": null,
  "previous": null,
  "results": [
    {
      "value_exc_vat": 5.728,
      "value_inc_vat": 6.0144,
      "valid_from": "2024-03-31T23:00:00Z",
      "valid_to": null,
      "payment_method": "DIRECT_DEBIT"
    },
    {
      "value_exc_vat": 5.902,
      "value_inc_vat": 6.1971,
      "valid_from": "2024-03-31T23:00:00Z",
      "valid_to": null,
      "payment_method": "NON_DIRECT_DEBIT"
    },
    {
      "value_exc_vat": 7.165,
      "value_inc_vat": 7.52325,
      "valid_from": "2024-01-01T00:00:00Z",
      "valid_to": "2024-03-31T23:00:00Z",
      "payment_method": "NON_DIRECT_DEBIT"
    },
    {
      "value_exc_vat": 6.999,
      "value_inc_vat": 7.34895,
      "valid_from": "2024-01-01T00:00:00Z",
      "valid_to": "2024-03-31T23:00:00Z",
      "payment_method": "DIRECT_DEBIT"
    }
  ]
}"""
    expected_deserialized_api_response = {
        "count": 4,
        "next": None,
        "previous": None,
        "results": [
            {
                "value_exc_vat": 5.728,
                "value_inc_vat": 6.0144,
                "valid_from": datetime(2024, 3, 31, 23, 0, 0, tzinfo=timezone.utc),
                "valid_to": None,
                "payment_method": "DIRECT_DEBIT",
            },
            {
                "value_exc_vat": 5.902,
                "value_inc_vat": 6.1971,
                "valid_from": datetime(2024, 3, 31, 23, 0, 0, tzinfo=timezone.utc),
                "valid_to": None,
                "payment_method": "NON_DIRECT_DEBIT",
            },
            {
                "value_exc_vat": 7.165,
                "value_inc_vat": 7.52325,
                "valid_from": datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
                "valid_to": datetime(2024, 3, 31, 23, 0, 0, tzinfo=timezone.utc),
                "payment_method": "NON_DIRECT_DEBIT",
            },
            {
                "value_exc_vat": 6.999,
                "value_inc_vat": 7.34895,
                "valid_from": datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
                "valid_to": datetime(2024, 3, 31, 23, 0, 0, tzinfo=timezone.utc),
                "payment_method": "DIRECT_DEBIT",
            },
        ],
    }
    actual_deserialized_api_response = OctopusEnergyUnitRateResponseSchema().loads(
        json_encoded_api_response
    )
    assert actual_deserialized_api_response == expected_deserialized_api_response
