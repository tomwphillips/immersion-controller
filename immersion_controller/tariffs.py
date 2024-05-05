from dataclasses import dataclass
from datetime import datetime, timezone

import requests

"""
Octopus return datetimes as ISO8601 strings in UTC.
datetime.fromisoformat only supported these in Python 3.11.
"""
DATETIME_FORMAT_STRING = "%Y-%m-%dT%H:%M:%SZ"


def decode_iso8601(encoded):
    return datetime.strptime(encoded, DATETIME_FORMAT_STRING).replace(
        tzinfo=timezone.utc
    )


def encode_iso8601(dt):
    if dt.tzinfo != timezone.utc:
        raise ValueError(f"timezone must be UTC, got {dt.tzinfo}")
    return dt.strftime(DATETIME_FORMAT_STRING)


@dataclass
class UnitRate:
    value: float
    valid_from: datetime
    valid_to: datetime


class Tariff:
    def get_rate(self, when):
        raise NotImplementedError()


class TariffException(Exception):
    pass


class OctopusEnergyUnitRate(UnitRate):
    @classmethod
    def from_api(cls, unit_rate):
        return cls(
            value=unit_rate["value_inc_vat"],
            valid_from=decode_iso8601(unit_rate["valid_from"]),
            valid_to=decode_iso8601(unit_rate["valid_to"]),
        )


class OctopusEnergyTariff(Tariff):
    def __init__(self, price_url):
        self.price_url = price_url

    def get_rate(self, when):
        response = requests.get(
            self.price_url, params={"period_from": when.isoformat()}
        )
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as exception:
            raise TariffException("status code != 200") from exception

        unit_rates = [
            OctopusEnergyUnitRate.from_api(unit_rate)
            for unit_rate in response.json()["results"]
        ]

        try:
            return sorted(unit_rates, key=lambda unit_rate: unit_rate.valid_from)[0]
        except IndexError as exception:
            raise TariffException(f"rate for {when} unavailable") from exception
