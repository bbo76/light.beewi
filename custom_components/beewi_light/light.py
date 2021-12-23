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
    PLATFORM_SCHEMA
)
import homeassistant.helpers.config_validation as cv
import homeassistant.util.color as color_util

from bulbeewipy  import BeewiSmartLight
_LOGGER = logging.getLogger(__name__)

# Validation of the user's configuration
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_NAME): cv.string,
    vol.Required(CONF_ADDRESS): cv.string,
})


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the platform."""
    lights = []
    device = {}
    device[CONF_NAME] = config[CONF_NAME]
    device[CONF_ADDRESS] = config[CONF_ADDRESS]
    light = BeewiLight(device)
    lights.append(light)
    add_entities(lights)

class BeewiLight(LightEntity):
    def __init__(self,device):
        """Initialize"""
        self._name = device[CONF_NAME]
        self._address = device[CONF_ADDRESS]
        self._light = BeewiSmartLight(self._address)
        self.is_valid = True
        self._rgb = None
        self._brightness = None
        self._isOn = None
        self._isWhite = None

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
    def is_on(self):
        return self._isOn
    
    def turn_on(self, **kwargs):
        try:
            brightness = kwargs.get(ATTR_BRIGHTNESS)
            rgbw =  kwargs.get(ATTR_RGBW_COLOR)
            _LOGGER.debug("Brightness for turn_on : {}".format(brightness))
            _LOGGER.debug("RGBW for turn_on : {}".format(rgbw))
    
            if not self._isOn:
                self._light.turnOn()
                self._isOn = True
                
            if not brightness == None:
                self._light.setBrightness(brightness)

            if not rgbw == None:
                if rgbw[0] == 255 and rgbw[1] == 255 and rgbw[2] == 255:
                    """ Consider that we want the White mode and eventually set the light tone"""
                    tone = rgbw[3]

                    if not self._isWhite:
                        self._light.setWhite()
                        self._isWhite = True
                    
                    self._light.setWhiteWarm(tone)
                else:
                    """ Consider we want color we focus the RGB and don't care about warm"""
                    self._light.setColor(rgbw[0], rgbw[1], rgbw[2])
                    self._isWhite = False       
        except Exception as e:
            _LOGGER.error(e)
        
    def turn_off(self, **kwargs):
        try:
            self._light.turnOff()
            self._isOn = False
        except Exception as e:
            _LOGGER.error(e)

    def update(self):
        try:
            _LOGGER.debug("Trying get states")
            self._light.getSettings()
            self._isOn = self._light.isOn
            self._isWhite = self._light.isWhite
            self._brightness = self._light.brightness
            self._rgbw = (255, 255, 255,self._light.temperature) if self._isWhite else (self._light.red, self._light.green, self._light.blue, self._light.temperature)
        except:
            _LOGGER.debug("set state to None we cannot get state (power off ?)")
            self._isOn = None