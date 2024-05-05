import subprocess

import pytest

from immersion_controller.cli import parse_args


def test_parse_args():
    octopus_electricity_tariff_url = "http://electricity"
    octopus_gas_tariff_url = "http://gas"
    shelly_url = "http://shelly"

    args = parse_args(
        [
            "-gas",
            octopus_gas_tariff_url,
            "-elec",
            octopus_electricity_tariff_url,
            "-shelly",
            shelly_url,
        ]
    )

    assert args.octopus_electricity_tariff_url == octopus_electricity_tariff_url
    assert args.octopus_gas_tariff_url == octopus_gas_tariff_url
    assert args.shelly_url == shelly_url


def test_main_invokes_cli():
    completed_process = subprocess.run(["immersion-controller"], capture_output=True)
    assert b"usage:" in completed_process.stderr


def test_mandatory_electricity_argument():
    with pytest.raises(SystemExit):
        parse_args(["-gas", "https://gas", "-shelly", "https://shelly"])


def test_mandatory_shelly_argument():
    with pytest.raises(SystemExit):
        parse_args(["-gas", "https://gas", "-elec", "https://elec"])


def test_mandatory_gas_argument():
    with pytest.raises(SystemExit):
        parse_args(["-elec", "https://elec", "-shelly", "https://shelly"])
