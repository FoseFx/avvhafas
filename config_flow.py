"""Config flow for the avv hafas integration."""

from __future__ import annotations

import logging
from typing import Any, TypedDict

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.config_entries import SOURCE_RECONFIGURE, ConfigFlowResult
from homeassistant.const import CONF_LATITUDE, CONF_LONGITUDE, CONF_NAME
from homeassistant.helpers.selector import (
    EntitySelector,
    EntitySelectorConfig,
    LocationSelector,
    NumberSelector,
    NumberSelectorConfig,
)

from .const import CONF_DESTINATION, CONF_INTERVAL, CONF_ORIGIN, CONF_SCHEDULE, DOMAIN

_LOGGER = logging.getLogger(__name__)


class LatLongDict(TypedDict):
    latitude: float
    longitude: float


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for avv hafas.

    Steps are:
    1. async_step_user
    2. async_step_origin
    3. async_step_destination
    """

    VERSION = 1

    def __init__(self) -> None:
        """Init _inputs with empty dict at creation."""
        super().__init__()
        self._inputs = {}

    async def async_step_reconfigure(
        self,
        input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Reconfigure flow. Just starts the normal flow."""
        return await self.async_step_user(input)

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Handle the initial step."""

        if user_input is not None:
            # we got user input, go to next step
            self._inputs = user_input
            return await self.async_step_origin()

        defaults = self._get_default_values()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_NAME,
                        default=defaults[CONF_NAME],
                    ): str,
                    vol.Required(
                        CONF_INTERVAL,
                        default=defaults[CONF_INTERVAL],
                    ): NumberSelector(
                        NumberSelectorConfig(
                            min=1,
                            step=1,
                            unit_of_measurement="min",
                        ),
                    ),
                    vol.Required(
                        CONF_SCHEDULE,
                        default=defaults[CONF_SCHEDULE],
                    ): EntitySelector(EntitySelectorConfig(domain="schedule")),
                }
            ),
        )

    async def async_step_origin(
        self,
        origin_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Ask for trip origin."""

        if origin_input is None:
            # no input for step yet, ask for it
            return await self._show_location_form("origin", CONF_ORIGIN)

        # move to next step with joined inputs
        self._inputs = self._inputs | origin_input
        return await self.async_step_destination()

    async def async_step_destination(
        self,
        destination_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Ask for trip destination."""

        if destination_input is None:
            # no input for step yet, ask for it
            return await self._show_location_form("destination", CONF_DESTINATION)

        # move to next step with joined inputs
        self._inputs = self._inputs | destination_input
        return await self._finalize()

    async def _finalize(self):
        inputs = self._inputs

        if self._reconfiguring():
            return self.async_update_reload_and_abort(
                self._get_reconfigure_entry(),
                data_updates=inputs,
            )

        return self.async_create_entry(
            title=inputs[CONF_NAME],
            data=inputs,
        )

    async def _show_location_form(self, step_id: str, schema_key: str):
        return self.async_show_form(
            step_id=step_id,
            data_schema=vol.Schema(
                {
                    vol.Required(
                        schema_key,
                        default=self._get_default_values()[schema_key],
                    ): LocationSelector(),
                }
            ),
        )

    def _reconfiguring(self) -> bool:
        return self.source == SOURCE_RECONFIGURE

    def _get_default_values(self):
        # if we are re-configuring, use previous values as defaults
        if self._reconfiguring():
            prev_entry = self._get_reconfigure_entry()
            return prev_entry.data

        # without a default the HA frontend refuses to render location selectors :)
        home_location = {
            CONF_LATITUDE: self.hass.config.latitude,
            CONF_LONGITUDE: self.hass.config.longitude,
        }
        return {
            CONF_NAME: vol.UNDEFINED,
            CONF_INTERVAL: 5,
            CONF_SCHEDULE: vol.UNDEFINED,
            CONF_ORIGIN: home_location,
            CONF_DESTINATION: home_location,
        }
