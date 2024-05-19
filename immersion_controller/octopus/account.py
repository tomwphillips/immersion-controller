import dataclasses
from datetime import datetime, timezone

import requests

from immersion_controller.octopus.schemas import (
    AccountDetailSchema,
    UnitRateResponseSchema,
)

API_URL = "https://api.octopus.energy/v1"

account_detail_schema = AccountDetailSchema()
unit_rate_response_schema = UnitRateResponseSchema()


def tariff_to_product_code(tariff_code):
    return "-".join(tariff_code.split("-")[2:-1])


class AgreementException(Exception):
    pass


@dataclasses.dataclass
class Agreement:
    valid_from: ...
    valid_to: ...
    tariff_code: ...
    product_code: ... = dataclasses.field(init=False)
    is_current: ... = dataclasses.field(init=False)
    energy_type: ... = dataclasses.field(init=False)
    unit_rates_url: ... = dataclasses.field(init=False)

    def __post_init__(self):
        self.product_code = tariff_to_product_code(self.tariff_code)
        self.is_current = self.valid_from < datetime.now(tz=timezone.utc) and (
            self.valid_to is None or self.valid_to > datetime.now(tz=timezone.utc)
        )

        if self.tariff_code.startswith("E"):
            self.energy_type = "electricity"
        elif self.tariff_code.startswith("G"):
            self.energy_type = "gas"
        else:
            raise ValueError(
                f"Unable to infer energy type from tariff code {self.tariff_code}"
            )

        self.unit_rates_url = (
            f"{API_URL}/products/{self.product_code}/"
            f"{self.energy_type}-tariffs/{self.tariff_code}/standard-unit-rates/"
        )

    def get_rate(self, when):
        response = requests.get(
            self.unit_rates_url, params={"period_from": when.isoformat()}
        )
        response.raise_for_status()
        decoded_response = unit_rate_response_schema.loads(response.content)

        unit_rates = [
            UnitRate.from_api(unit_rate)
            for unit_rate in decoded_response["results"]
            if unit_rate.get("payment_method") != "NON_DIRECT_DEBIT"
        ]

        try:
            return unit_rates[-1]
        except IndexError as exception:
            raise AgreementException(f"rate for {when} unavailable") from exception

    @classmethod
    def get_gas_agreement(
        cls, api_key, account_number, account_endpoint=API_URL + "/accounts"
    ):
        response = requests.get(
            f"{account_endpoint}/{account_number}/", auth=(api_key, "")
        )
        account_detail = account_detail_schema.loads(response.content)
        return cls(
            **account_detail["properties"][0]["gas_meter_points"][0]["agreements"][-1]
        )

    @classmethod
    def get_electricity_agreement(
        cls, api_key, account_number, account_endpoint=API_URL + "/accounts"
    ):
        response = requests.get(
            f"{account_endpoint}/{account_number}/", auth=(api_key, "")
        )
        account_detail = account_detail_schema.loads(response.content)
        return cls(
            **account_detail["properties"][0]["electricity_meter_points"][0][
                "agreements"
            ][-1]
        )


@dataclasses.dataclass
class UnitRate:
    value: ...
    valid_from: ...
    valid_to: ...

    @classmethod
    def from_api(cls, unit_rate):
        return cls(
            value=unit_rate["value_inc_vat"],
            valid_from=unit_rate["valid_from"],
            valid_to=unit_rate.get("valid_to"),
        )
