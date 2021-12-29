"""Platform for light integration."""
import logging
import time
import voluptuous as vol

from homeassistant.const import CONF_ADDRESS, CONF_DEVICES, CONF_NAME
from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_RGBW_COLOR,
    COLOR_MODE_RGBW,
    LightEntity,
    PLATFORM_SCHEMA,
    ENTITY_ID_FORMAT
)
from homeassistant.helpers.entity import generate_entity_id
import homeassistant.helpers.config_validation as cv
import homeassistant.util.color as color_util

from .beewilight  import BeewiSmartLight
import tenacity

_LOGGER = logging.getLogger(__name__)

DOMAIN = "beewi_light"

# Validation of the user's configuration
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_NAME): cv.string,
    vol.Required(CONF_ADDRESS): cv.string,
})


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the platform."""
    mac = config[CONF_ADDRESS]
    name = config[CONF_NAME]

    if discovery_info is not None:
        _LOGGER.debug("Adding autodetected %s", discovery_info["hostname"])
        name = DOMAIN
    _LOGGER.debug(f"Adding light {name} with mac:{mac}")
    add_entities([BeewiLight(name, mac)])

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the platform from config_entry."""
    _LOGGER.debug(
        f"async_setup_entry:setting up the config entry {config_entry.title} "
        f"with data:{config_entry.data}"
    )
    name = config_entry.data.get(CONF_NAME) or DOMAIN
    mac = config_entry.data.get(CONF_ADDRESS)
    entity = BeewiLight(name, mac)
    async_add_entities([entity])

class BeewiLight(LightEntity):
    def __init__(self, name, mac):
        """Initialize"""
        self._name = name
        self._address = mac
        self.entity_id = generate_entity_id(ENTITY_ID_FORMAT, self._name, [])
        self._light = BeewiSmartLight(self._address)
        self.is_valid = True
        self._rgbw = None
        self._brightness = None
        self._isOn = False
        self._isWhite = None
        self._available = False

    @property
    def name(self):
        """Return the display name of this light."""
        return self._name

    @property
    def color_mode(self):
        return COLOR_MODE_RGBW
    
    @property
    def supported_color_modes(self):
        return {COLOR_MODE_RGBW}

    @property
    def brightness(self):
        return self._brightness

    @property
    def rgbw_color(self):
        """Return the RBG color value."""
        return self._rgbw
        
    @property
    def available(self) -> bool:
        return self._available

    @property
    def is_on(self):
        return self._isOn
    
    @tenacity.retry(stop=(tenacity.stop_after_delay(10) | tenacity.stop_after_attempt(5)))
    def turn_on(self, **kwargs):
        try:
            brightness = kwargs.get(ATTR_BRIGHTNESS)
            rgbw =  kwargs.get(ATTR_RGBW_COLOR)
    
            if not self._isOn:
                self._light.turnOn()
                self._isOn = True
                
            if not brightness == None:
                self._light.setBrightness(brightness)

            if not rgbw == None:
                tone = rgbw[3]

                if (rgbw[0] == 255 and rgbw[1] == 255 and rgbw[2] == 255) or self._rgbw[3] != tone:
                    """ Consider that we want the White mode and eventually set the light tone"""
                    if not self._isWhite:
                        self._light.setWhite()
                        self._isWhite = True
                    
                    self._light.setWhiteWarm(tone)
                else:
                    """ Consider we want color we focus the RGB and don't care about warm"""
                    self._light.setColor(rgbw[0], rgbw[1], rgbw[2])
                    self._isWhite = False    
            
            self._available = True
        except:
            raise
        
    @tenacity.retry(stop=(tenacity.stop_after_delay(10) | tenacity.stop_after_attempt(5)))
    def turn_off(self, **kwargs):
        try:
            self._light.turnOff()
            self._isOn = False
            self._available = True
        except:
            raise

    def update(self):
        try:
            self.execute_update()
        except:
            raise
        
    def execute_update(self):
        try:
            self._light.getSettings()
            self._available = True
            self._isOn = self._light.isOn
            self._isWhite = self._light.isWhite
            self._brightness = self._light.brightness
            self._rgbw = (255, 255, 255,self._light.temperature) if self._isWhite else (self._light.red, self._light.green, self._light.blue, self._light.temperature)
        except:
            self._available = False