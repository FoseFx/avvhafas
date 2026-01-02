# avvhafas

HomeAssistant integration exposing a sensor for public-transport trips using the Aachener Verkehrsverbund (AVV) HaFas API.

Requires access to the REST-API. You can request an access id here: https://avv.de/de/fahrplaene/opendata-service

Notice: In my experience rate-limits are rather strict.

## Setup

### Install this integration via HACS (WIP)

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

TODO

### (Optional) Install avvhafas-cards

TODO

## Disclaimers

This project is unaffiliated with the AVV.

No warranty of any kind, see LICENSE for details.

