# avvhafas

HomeAssistant integration exposing a sensor for public-transport trips using the Aachener Verkehrsverbund (AVV) HaFas API.

Requires access to the REST-API. You can request an access id here: https://avv.de/de/fahrplaene/opendata-service

Notice: In my experience rate-limits are rather strict.

## Setup

### Install this integration via HACS (WIP)

- Ensure you have [HACS](https://www.hacs.xyz/docs/use/) installed.
- On the [HACS repositories](https://www.hacs.xyz/docs/use/repositories/dashboard/#browsing-repositories) page, add a new custom repository:

```plain
Repository: FoseFx/avvhafas
Type: Integration
```

- On the same page: Search for `avvhafas` and download the component.
- Continue with Configuration

### Configuration

Extend your configuration.yaml

```yaml
avvhafas:
  host: "<...>/restproxy"
  api_key: "<...>"
```

And restart Home Assistant.

### Create Trips

You can now configure new trip sensors from the integration configuration page.

- Settings -> Devices & Service -> Add Integration
- Search `avv hafas`
- Follow the configuration wizard

You now have a new sensor!

### (Optional) Install avvhafas-cards

You can now write templates against this sensor.
For the format of the sensor data, have a look at the sensor.py.

You can also install the avvhafas-cards dashboard.

See https://github.com/FoseFx/avvhafas-cards#installation

## Disclaimers

This project is unaffiliated with the AVV.

No warranty of any kind, see LICENSE for details.

This project does not take feature requests.
