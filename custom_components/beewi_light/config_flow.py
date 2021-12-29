"""Config flow for yeelight_bt"""
import logging
from homeassistant import config_entries
from homeassistant.const import CONF_NAME, CONF_MAC
import voluptuous as vol
from homeassistant.helpers import device_registry as dr

_LOGGER = logging.getLogger(__name__)

DOMAIN = "beewi_light"

class Beewi_lightConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):  # type: ignore
    """Handle a config flow for yeelight_bt."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    @property
    def data_schema(self):
        """Return the data schema for integration."""
        return vol.Schema({vol.Required(CONF_NAME): str, vol.Required(CONF_MAC): str})

    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user."""
        self.devices = []
        return await self.async_step_device()

    async def async_step_device(self, user_input=None):
        """Handle setting up a device."""
        # _LOGGER.debug(f"User_input: {user_input}")
        if not user_input:
            schema_mac = str
            if self.devices:
                schema_mac = vol.In(self.devices)
            schema = vol.Schema(
                {vol.Required(CONF_NAME): str, vol.Required(CONF_MAC): schema_mac}
            )
            return self.async_show_form(step_id="device", data_schema=schema)

        user_input[CONF_MAC] = user_input[CONF_MAC][:17]
        unique_id = dr.format_mac(user_input[CONF_MAC])
        _LOGGER.debug(f"Yeelight UniqueID: {unique_id}")

        await self.async_set_unique_id(unique_id)
        self._abort_if_unique_id_configured()

        return self.async_create_entry(title=user_input[CONF_NAME], data=user_input)

    async def async_step_import(self, import_info):
        """Handle import from config file."""
        return await self.async_step_device(import_info)