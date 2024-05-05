# Immersion Controller

An application to switch on my immersion heater when the price of electricity is less than gas, saving money and reducing CO2 emissions.

## Set up

### Get your tariff's unit rate endpoints

You could certainly script this but it's one-off set up, so I've done it manually.

[Login to your account](https://octopus.energy/dashboard/new/accounts/personal-details) to get your API key and account number. Then make a request to the account end point:

```commandline
#!/bin/bash

API_KEY="your_key"
ACCOUNT_NUMBER="your_account_number"
curl -u "$API_KEY:" "https://api.octopus.energy/v1/accounts/${ACCOUNT_NUMBER}/" | jq
```

You'll get back the tariffs on your gas and electricity meters.
Take note of the `tariff_code` under `agreements`.
Make sure to look at `valid_from` and `valid_to` to ensure you pick your current tariff, not past ones.
For me, my gas and electricity tariff codes are `G-1R-VAR-22-11-01-M` and `E-1R-AGILE-23-12-06-M`, respectively.

Gas unit rates are of the form:

```
https://api.octopus.energy/v1/products/{product-code}/gas-tariffs/{tariff-code}/standard-unit-rates/
```

So for my gas tariff, the unit rate endpoint is:

```commandline
https://api.octopus.energy/v1/products/VAR-22-11-01/gas-tariffs/G-1R-VAR-22-11-01-M/standard-unit-rates/
```

Note that the endpoint returns different prices for whether you pay on direct debit or not. Only direct debit tariffs are supported. 

Electricity tariffs are of the form:

```commandline
 https://api.octopus.energy/v1/products/{product-code}/electricity-tariffs/{tariff-code}/standard-unit-rates/
```

So for my electricity tariff, the unit rate endpoint is:

```commandline
https://api.octopus.energy/v1/products/AGILE-23-12-06/electricity-tariffs/E-1R-AGILE-23-12-06-M/standard-unit-rates/
```
