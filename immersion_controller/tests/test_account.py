from datetime import datetime, timedelta, timezone

import pytest
import responses
from responses.matchers import query_param_matcher

from immersion_controller.octopus.account import Agreement


@pytest.fixture
def setup_mock_accounts_endpoint():
    def mock(api_key, account_number, account_endpoint_url):
        responses.get(
            account_endpoint_url + f"/{account_number}/",
            json={
                "number": account_number,
                "properties": [
                    {
                        "electricity_meter_points": [
                            {
                                "agreements": [
                                    {
                                        "tariff_code": "E-1R-VAR-22-10-01-M",
                                        "valid_from": "2023-01-01T00:00:00Z",
                                        "valid_to": "2023-03-22T00:00:00Z",
                                    },
                                    {
                                        "tariff_code": "E-1R-AGILE-FLEX-22-11-25-M",
                                        "valid_from": "2023-03-22T00:00:00Z",
                                        "valid_to": "2024-02-15T00:00:00Z",
                                    },
                                    {
                                        "tariff_code": "E-1R-AGILE-23-12-06-M",
                                        "valid_from": "2024-02-15T00:00:00Z",
                                        "valid_to": "2025-02-15T00:00:00Z",
                                    },
                                ],
                            }
                        ],
                        "gas_meter_points": [
                            {
                                "agreements": [
                                    {
                                        "tariff_code": "G-1R-VAR-22-10-01-M",
                                        "valid_from": "2023-01-01T00:00:00Z",
                                        "valid_to": "2023-04-01T00:00:00+01:00",
                                    },
                                    {
                                        "tariff_code": "G-1R-VAR-22-11-01-M",
                                        "valid_from": "2023-04-01T00:00:00+01:00",
                                        "valid_to": None,
                                    },
                                ],
                            }
                        ],
                    }
                ],
            },
        )

    return mock


@responses.activate
def test_get_gas_agreement(setup_mock_accounts_endpoint):
    api_key = "api_key"
    account_number = "account_number"
    account_endpoint_url = "https://hostname/accounts"
    setup_mock_accounts_endpoint(api_key, account_number, account_endpoint_url)

    gas_agreement = Agreement.get_gas_agreement(
        api_key, account_number, account_endpoint_url
    )
    assert gas_agreement.valid_from == datetime(
        2023, 4, 1, 0, 0, 0, tzinfo=timezone(timedelta(hours=1))
    )
    assert gas_agreement.valid_to is None
    assert gas_agreement.tariff_code == "G-1R-VAR-22-11-01-M"
    assert gas_agreement.product_code == "VAR-22-11-01"
    assert gas_agreement.is_current
    assert gas_agreement.energy_type == "gas"


@responses.activate
def test_get_gas_unit_rate():
    valid_from = datetime(2023, 1, 1, tzinfo=timezone.utc)
    valid_to = datetime(2024, 1, 1, tzinfo=timezone.utc)
    agreement = Agreement(valid_from, valid_to, "G-1R-VAR-22-11-01-M")
    when = datetime(2023, 6, 1, 12, 0, tzinfo=timezone.utc)

    responses.get(
        (
            f"https://api.octopus.energy/v1/products/{agreement.product_code}/"
            f"{agreement.energy_type}-tariffs/{agreement.tariff_code}/"
            "standard-unit-rates/"
        ),
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
                            when.replace(minute=0) + ((i + 1) * timedelta(minutes=30))
                        ).isoformat(),
                        "payment_method": "DIRECT_DEBIT",
                    }
                    for i in range(4)
                ]
                + [
                    {
                        "value_inc_vat": 1.1,
                        "valid_from": (
                            when.replace(minute=0) + (i * timedelta(minutes=30))
                        ).isoformat(),
                        "valid_to": (
                            when.replace(minute=0) + ((i + 1) * timedelta(minutes=30))
                        ).isoformat(),
                        "payment_method": "NON_DIRECT_DEBIT",
                    }
                    for i in range(4)
                ],
                key=lambda unit_rate: unit_rate["valid_from"],
                reverse=True,
            )
        },
    )

    rate = agreement.get_rate(when)
    assert rate.value == 1.0
    assert rate.valid_from == when
    assert rate.valid_to == when.replace(minute=30)


@responses.activate
def test_get_electricity_agreement(setup_mock_accounts_endpoint):
    api_key = "api_key"
    account_number = "account_number"
    account_endpoint_url = "https://hostname/accounts"
    setup_mock_accounts_endpoint(api_key, account_number, account_endpoint_url)

    electricity_agreement = Agreement.get_electricity_agreement(
        api_key, account_number, account_endpoint_url
    )
    assert electricity_agreement.valid_from == datetime(
        2024, 2, 15, 0, 0, 0, tzinfo=timezone.utc
    )
    assert electricity_agreement.valid_to == datetime(
        2025, 2, 15, 0, 0, 0, tzinfo=timezone.utc
    )
    assert electricity_agreement.tariff_code == "E-1R-AGILE-23-12-06-M"
    assert electricity_agreement.product_code == "AGILE-23-12-06"
    assert electricity_agreement.is_current
    assert electricity_agreement.energy_type == "electricity"


@responses.activate
def test_get_electricity_unit_rate():
    valid_from = datetime(2023, 1, 1, tzinfo=timezone.utc)
    valid_to = datetime(2024, 1, 1, tzinfo=timezone.utc)
    agreement = Agreement(valid_from, valid_to, "E-1R-AGILE-23-12-06-M")
    when = datetime(2023, 6, 1, 12, 0, tzinfo=timezone.utc)

    responses.get(
        (
            f"https://api.octopus.energy/v1/products/"
            f"{agreement.product_code}/{agreement.energy_type}-tariffs/"
            f"{agreement.tariff_code}/standard-unit-rates/"
        ),
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
                            when.replace(minute=0) + ((i + 1) * timedelta(minutes=30))
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

    rate = agreement.get_rate(when)
    assert rate.value == 1.0
    assert rate.valid_from == when
    assert rate.valid_to == when.replace(minute=30)


def test_agreement_is_current():
    past_agreement = Agreement(
        valid_from=datetime(2023, 1, 1, tzinfo=timezone.utc),
        valid_to=datetime(2024, 1, 1, tzinfo=timezone.utc),
        tariff_code="E-1R-AGILE-23-12-06-M",
    )
    assert not past_agreement.is_current

    future_agreement = Agreement(
        valid_from=datetime(2050, 1, 1, tzinfo=timezone.utc),
        valid_to=datetime(2051, 1, 1, tzinfo=timezone.utc),
        tariff_code="E-1R-AGILE-23-12-06-M",
    )
    assert not future_agreement.is_current

    current_agreement = Agreement(
        valid_from=datetime.now(tz=timezone.utc) - timedelta(days=1),
        valid_to=datetime.now(tz=timezone.utc) + timedelta(days=1),
        tariff_code="E-1R-AGILE-23-12-06-M",
    )
    assert current_agreement.is_current

    current_indefinite_agreement = Agreement(
        valid_from=datetime.now(tz=timezone.utc) - timedelta(days=1),
        valid_to=None,
        tariff_code="E-1R-AGILE-23-12-06-M",
    )
    assert current_indefinite_agreement.is_current


def test_agreement_product_code():
    valid_from = datetime.now(tz=timezone.utc) - timedelta(days=1)
    cases = [
        (
            Agreement(
                valid_from=valid_from,
                valid_to=None,
                tariff_code="E-1R-AGILE-23-12-06-M",
            ),
            "AGILE-23-12-06",
        ),
        (
            Agreement(
                valid_from=valid_from, valid_to=None, tariff_code="G-1R-VAR-22-11-01-M"
            ),
            "VAR-22-11-01",
        ),
    ]
    for agreement, expected_product_code in cases:
        assert agreement.product_code == expected_product_code
