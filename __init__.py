"""The avv hafas integration."""

from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY, CONF_HOST, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv

import httpx

from .const import DOMAIN
from .config_flow import LatLongDict

_LOGGER = logging.getLogger(__name__)

_PLATFORMS: list[Platform] = [Platform.SENSOR]


type AvvHafasConfigEntry = ConfigEntry[AvvHafasApi]

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_HOST): cv.string,
                vol.Required(CONF_API_KEY): cv.string,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


class AvvHafasApi:
    def __init__(self, host: str, key: str) -> None:
        """Initialize."""
        self._host = host
        self._key = key

    def _headers(self):
        return {
            "Authorization": f"Bearer {self._key}",
            "Accept": "application/json",
        }

    async def validate_connection(self):
        # If you cannot connect:
        # throw CannotConnect
        # If the authentication is wrong:
        # InvalidAuth
        return True  # TODO

    async def trip(
        self,
        origin: LatLongDict,
        destination: LatLongDict,
        client: httpx.AsyncClient,
    ):
        params = {
            "originCoordLat": origin["latitude"],
            "originCoordLong": origin["longitude"],
            "destCoordLat": destination["latitude"],
            "destCoordLong": destination["longitude"],
        }

        resp = await client.get(
            f"{self._host}/trip",
            params=params,
            headers=self._headers(),
        )
        resp.raise_for_status()
        return resp.json()


def setup(hass: HomeAssistant, config: dict) -> bool:
    """This should be the first thing that is called, and only be called if a config for this domain exists."""
    domain_config = config.get(DOMAIN)

    if not domain_config:
        _LOGGER.warning("%s not configured", DOMAIN)
        return False  # Integration not configured in YAML

    host = domain_config[CONF_HOST]
    api_key = domain_config[CONF_API_KEY]

    # We could do some API key validation here, but why bother

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][CONF_HOST] = host
    hass.data[DOMAIN][CONF_API_KEY] = api_key
    return True


async def async_setup_entry(hass: HomeAssistant, entry: AvvHafasConfigEntry) -> bool:
    """Set up avv hafas from a config entry."""
    domain_config = hass.data[DOMAIN]

    # create api object for sensor to use
    api = AvvHafasApi(domain_config[CONF_HOST], domain_config[CONF_API_KEY])
    await api.validate_connection()
    entry.runtime_data = api

    # create sensor
    await hass.config_entries.async_forward_entry_setups(entry, _PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: AvvHafasConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, _PLATFORMS)
