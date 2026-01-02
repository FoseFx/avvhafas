"""Sensor for HaFAS."""

from datetime import UTC, date, datetime, time, timedelta
import logging
from zoneinfo import ZoneInfo

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_ON
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.httpx_client import get_async_client

from . import AvvHafasApi
from .const import CONF_DESTINATION, CONF_ORIGIN, CONF_SCHEDULE, CONF_INTERVAL

_LOGGER = logging.getLogger(__name__)

ICON = "mdi:timetable"
SCAN_INTERVAL = timedelta(minutes=1)


async def async_setup_entry(
    hass: HomeAssistant, config: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up HaFAS sensor entity based on a config entry."""
    update_before_add = True
    async_add_entities([HaFAS(hass, config)], update_before_add)


class HaFAS(SensorEntity):
    """Implementation of a HaFAS sensor."""

    def __init__(self, hass: HomeAssistant, config: ConfigEntry) -> None:
        """Initialize the sensor."""
        self.hass = hass
        self.config = config

        # https://developers.home-assistant.io/docs/api/native-app-integration/sensors#registering-a-sensor
        self._attr_device_class = SensorDeviceClass.TIMESTAMP
        self._attr_icon = ICON
        self._attr_name = config.title
        self._attr_type = "sensor"
        self._attr_unique_id = config.entry_id

        self._attr_extra_state_attributes = {
            "connections": [],
            "active": True,
            "last_query": datetime.fromtimestamp(0, UTC),
        }

    def _in_schedule(self) -> bool:
        schedule_entity_id = self.config.data[CONF_SCHEDULE]

        state = self.hass.states.get(schedule_entity_id)
        if state is None:
            raise RuntimeError("referenced state is missing")

        return state.state == STATE_ON

    def _is_query_due(self) -> bool:
        interval_mins = self.config.data[CONF_INTERVAL]
        next_query_due_at = (
            self._attr_extra_state_attributes["last_query"]
            + timedelta(
                minutes=interval_mins,
                seconds=-10,  # added as HA wont schedule update() in precise 1-min intervals which could lead to us waiting for another whole interval
            )
        )
        return datetime.now(UTC) >= next_query_due_at

    async def async_update(self) -> None:
        """Update the journeys."""

        self._attr_extra_state_attributes["active"] = self._in_schedule()

        # only query, when in schedule (due to rate-limiting)
        if not self._attr_extra_state_attributes["active"]:
            return

        # we are scheduled at 1-minute invervals,
        # but the user can configure the actual interval
        # this way we might abort early here when we dont want to query
        # note, that the "active" attribute is updated in 1-min intervals regardless
        # in order not to drift too far (time-wise) from the schedule-sensor
        if not self._is_query_due():
            return

        self._attr_extra_state_attributes["last_query"] = datetime.now(UTC)

        api: AvvHafasApi = self.config.runtime_data

        try:
            journeys = await api.trip(
                self.config.data[CONF_ORIGIN],
                self.config.data[CONF_DESTINATION],
                get_async_client(self.hass),
            )
            if not journeys:
                _LOGGER.warning("W: journeys empty for %s", self._attr_unique_id)
                return

            connections = [
                {
                    "legs": [
                        {
                            "origin": leg["Origin"]["name"],
                            "departure": parseDate(
                                leg["Origin"]["date"],
                                leg["Origin"]["time"],
                            ),
                            "platform": maybeGet(
                                thisOrThatOf(
                                    leg["Origin"],
                                    "rtPlatform",
                                    "platform",
                                ),
                                "text",
                            ),
                            "delay": diffToRt(
                                parseDate(leg["Origin"]["date"], leg["Origin"]["time"]),
                                optParseDate(
                                    leg["Origin"].get("rtDate"),
                                    leg["Origin"].get("rTime"),
                                ),
                            ),
                            "destination": leg["Destination"]["name"],
                            "arrival": parseDate(
                                leg["Destination"]["date"],
                                leg["Destination"]["time"],
                            ),
                            "platform_arrival": maybeGet(
                                thisOrThatOf(
                                    leg["Destination"],
                                    "rtPlatform",
                                    "platform",
                                ),
                                "text",
                            ),
                            "delay_arrival": diffToRt(
                                parseDate(
                                    leg["Destination"]["date"],
                                    leg["Destination"]["time"],
                                ),
                                optParseDate(
                                    leg["Destination"].get("rtDate"),
                                    leg["Destination"].get("rTime"),
                                ),
                            ),
                            "mode": modeOf(leg),
                            "name": thisOrThatOf(leg, "number", "name"),
                        }
                        for leg in j["LegList"]["Leg"]
                    ]
                }
                for j in journeys["Trip"]
            ]
            self._attr_extra_state_attributes["connections"] = connections

            # native value = start of next leg out of here
            first_leg = next(
                (leg for conn in connections for leg in conn.get("legs", [])),
                None,
            )
            self._attr_native_value = (
                first_leg["departure"] + parseDelay(first_leg.get("delay"))
                if first_leg is not None
                else None
            )

        except BaseException as e:
            _LOGGER.warning(
                "Couldn't fetch journeys for %s: %s",
                self._attr_unique_id,
                e,
                exc_info=True,
            )


def optParseDate(date_str: str | None, time_str: str | None) -> datetime | None:
    if not date_str or not time_str:
        return None
    return parseDate(date_str, time_str)


def parseDate(date_str: str, time_str: str) -> datetime:
    d = date.fromisoformat(date_str)
    t = time.fromisoformat(time_str)
    dt = datetime.combine(d, t)
    return dt.replace(tzinfo=ZoneInfo("Europe/Berlin"))


def diffToRt(time: datetime, rtTime: datetime | None):
    delta = timedelta()  # 0-delta
    if rtTime:
        delta = rtTime - time
    hours, remainder = divmod(delta.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def parseDelay(delay_str: str | None) -> timedelta:
    """Convert 'HH:MM:SS' string to timedelta."""
    if not delay_str:
        return timedelta(0)

    h, m, s = map(int, delay_str.split(":"))
    return timedelta(hours=h, minutes=m, seconds=s)


def thisOrThatOf(obj, key1, key2):
    val = obj.get(key1)
    if not val:
        return obj.get(key2)
    return val


def maybeGet(obj, key):
    if not obj:
        return None
    return obj.get(key)


def modeOf(leg):
    if leg["type"] == "WALK":
        return "walking"
    if leg["type"] == "JNY":
        train_cats = ["DRE", "NRE", "ICE"]
        if leg.get("category", "") in train_cats:
            return "train"
    return "bus"
