from marshmallow import EXCLUDE, Schema, fields, validate


class AgreementSchema(Schema):
    tariff_code = fields.Str()
    valid_from = fields.AwareDateTime()
    valid_to = fields.AwareDateTime(allow_none=True)


class MeterPointSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    agreements = fields.Nested(AgreementSchema, many=True)


class PropertySchema(Schema):
    class Meta:
        unknown = EXCLUDE

    electricity_meter_points = fields.Nested(MeterPointSchema, many=True)
    gas_meter_points = fields.Nested(MeterPointSchema, many=True)


class AccountDetailSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    properties = fields.Nested(PropertySchema, many=True, unknown=EXCLUDE)


class UnitRateSchema(Schema):
    value_inc_vat = fields.Float()
    value_exc_vat = fields.Float()
    valid_from = fields.AwareDateTime()
    valid_to = fields.AwareDateTime(allow_none=True)
    payment_method = fields.String(
        validate=validate.OneOf(["DIRECT_DEBIT", "NON_DIRECT_DEBIT"]), allow_none=True
    )


class UnitRateResponseSchema(Schema):
    count = fields.Integer()
    next = fields.String(allow_none=True)
    previous = fields.String(allow_none=True)
    results = fields.List(fields.Nested(UnitRateSchema))
