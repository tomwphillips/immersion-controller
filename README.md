# Immersion Controller [WIP]

An application to switch on my immersion heater when the price of electricity is less than gas, saving money and reducing CO2 emissions.

## Set up

Install with `pip` (or pipx):

```commandline
pipx install git+https://github.com/tomwphillips/immersion-controller
```

You need to run the application continuously. I use systemd.

In `/etc/systemd/system/immersion_controller.service`:

```commandline
[Unit]
Description=Immersion controller
After=network.target

[Service]
EnvironmentFile=/etc/immersion_controller.env
ExecStart=/home/pi/.local/bin/immersion-controller 
Restart=always
User=pi
Group=pi

[Install]
WantedBy=multi-user.target
```

Get your API key and account number from your Octopus account. In `/etc/immersion_controller.env`:

```
IC_API_KEY="api key"
IC_ACCOUNT_NUMBER="account number"
IC_SHELLY_URL="http://shelly-immersion"
```

Then edit the permissions, start up the service and check out the logs:

```
sudo chmod 600 /etc/immersion_controller.env
sudo systemctl enable immersion_controller
sudo systemctl start immersion_controller
journalctl -ef -u immersion_controller.service
```