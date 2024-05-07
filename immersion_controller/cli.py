import argparse
import logging.config

from immersion_controller.control import Controller
from immersion_controller.switches import ShellyProEM
from immersion_controller.tariffs import OctopusEnergyTariff

logging.config.dictConfig(
    {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {"format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"},
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "standard",
            },
        },
        "root": {
            "handlers": ["console"],
            "level": "INFO",
        },
    }
)


def parse_args(args=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("-elec", "--octopus-electricity-tariff-url", required=True)
    parser.add_argument("-gas", "--octopus-gas-tariff-url", required=True)
    parser.add_argument("-shelly", "--shelly-url", required=True)
    return parser.parse_args(args)


def main(args=None):
    args = parse_args(args)
    electricity_tariff = OctopusEnergyTariff(args.octopus_electricity_tariff_url)
    gas_tariff = OctopusEnergyTariff(args.octopus_gas_tariff_url)
    shelly_switch = ShellyProEM(args.shelly_url)
    controller = Controller(electricity_tariff, gas_tariff, shelly_switch)
    controller.run()
