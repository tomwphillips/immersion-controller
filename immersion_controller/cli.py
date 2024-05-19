import logging.config

import click

from immersion_controller.control import Controller
from immersion_controller.octopus.account import Agreement
from immersion_controller.switches import ShellyProEM

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

logger = logging.getLogger(__name__)


@click.command()
@click.option(
    "--api-key", required=True, help="Octopus Energy API key", envvar="IC_API_KEY"
)
@click.option(
    "--account-number",
    required=True,
    help="Octopus Energy account number",
    envvar="IC_ACCOUNT_NUMBER",
)
@click.option(
    "--shelly-url",
    required=True,
    help="URL of your Shelly device",
    envvar="IC_SHELLY_URL",
)
def main(api_key, account_number, shelly_url):
    electricity_agreement = Agreement.get_electricity_agreement(api_key, account_number)
    logger.info(electricity_agreement)
    gas_agreement = Agreement.get_gas_agreement(api_key, account_number)
    logger.info(gas_agreement)
    shelly_switch = ShellyProEM(shelly_url)
    controller = Controller(electricity_agreement, gas_agreement, shelly_switch)
    controller.run()
