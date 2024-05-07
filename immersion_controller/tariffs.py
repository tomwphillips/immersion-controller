from typing import Optional
from dataclasses import dataclass
from datetime import datetime
from marshmallow import Schema, fields,  validate
import requests


@dataclass
class UnitRate:
    value: float
    valid_from: datetime
    valid_to: Optional[datetime]


class Tariff:
    def get_rate(self, when):
        raise NotImplementedError()


class TariffException(Exception):
    pass


class OctopusEnergyUnitRateSchema(Schema):
    value_inc_vat = fields.Float()
    value_exc_vat = fields.Float()
    valid_from = fields.AwareDateTime()
    valid_to = fields.AwareDateTime(allow_none=True)
    payment_method = fields.String(validate=validate.OneOf(["DIRECT_DEBIT", "NON_DIRECT_DEBIT"]), allow_none=True)


class OctopusEnergyUnitRateResponseSchema(Schema):
    count = fields.Integer()
    next = fields.String(allow_none=True)
    previous = fields.String(allow_none=True)
    results = fields.List(fields.Nested(OctopusEnergyUnitRateSchema))


class OctopusEnergyUnitRate(UnitRate):
    @classmethod
    def from_api(cls, unit_rate):
        return cls(
            value=unit_rate["value_inc_vat"],
            valid_from=unit_rate["valid_from"],
            valid_to=unit_rate.get("valid_to"),
        )


class OctopusEnergyTariff(Tariff):
    unit_rate_response_schema = OctopusEnergyUnitRateResponseSchema()

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

        decoded_response = self.unit_rate_response_schema.loads(response.content)

        unit_rates = [
            OctopusEnergyUnitRate.from_api(unit_rate)
            for unit_rate in decoded_response['results']
            if unit_rate.get("payment_method") != "NON_DIRECT_DEBIT"
        ]

        try:
            return unit_rates[-1]
        except IndexError as exception:
            raise TariffException(f"rate for {when} unavailable") from exception
