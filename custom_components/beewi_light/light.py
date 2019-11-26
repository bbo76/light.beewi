"""Platform for light integration."""
import logging
import time
import voluptuous as vol

from homeassistant.const import CONF_ADDRESS, CONF_DEVICES, CONF_NAME
from homeassistant.components.light import (
    ATTR_BRIGHTNESS, ATTR_HS_COLOR, ATTR_WHITE_VALUE, SUPPORT_BRIGHTNESS,
    SUPPORT_COLOR, SUPPORT_WHITE_VALUE, Light, PLATFORM_SCHEMA)
import homeassistant.helpers.config_validation as cv
import homeassistant.util.color as color_util

from bluepy import btle

_LOGGER = logging.getLogger(__name__)
SUPPORT_BEEWI_LED = (SUPPORT_BRIGHTNESS | SUPPORT_COLOR | SUPPORT_WHITE_VALUE)

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
    add_entities(lights,True)



class BeewiLight(Light):
    def __init__(self,device):
        """Initialize"""
        self._name = device[CONF_NAME]
        self._address = device[CONF_ADDRESS]
        self.is_valid = True
        self._white = 0
        self._brightness = 0
        self._rgb = (0, 0, 0)
        self._state = False
        self._connection = None

    @property
    def name(self):
        """Return the display name of this light."""
        return self._name

    @property
    def brightness(self):
        """Return the brightness of the light.
        This method is optional. Removing it indicates to Home Assistant
        that brightness is not supported for this light.
        """
        return self._brightness

    @property
    def rgb_color(self):
        """Return the RBG color value."""
        return self._rgb

    @property
    def white_value(self):
        """Return the white property."""
        return self._white

    @property
    def supported_features(self):
        """Flag supported features."""
        return SUPPORT_BEEWI_LED

    @property
    def should_poll(self):
        """Feel free to poll."""
        return True

    @property
    def is_on(self):
        """Return true if light is on."""
        return self._state
        
    @property
    def assumed_state(self):
        """We can report the actual state."""
        return False
    
    def turn_on(self, **kwargs):
        _LOGGER.debug("turn_on()")
        """Instruct the light to turn on.
        You can skip the brightness part if your light does not support
        brightness control.
        """
        #rgb = kwargs.get(ATTR_RGB_COLOR)
        hs_color = kwargs.get(ATTR_HS_COLOR)
        white = kwargs.get(ATTR_WHITE_VALUE)
        brightness = kwargs.get(ATTR_BRIGHTNESS)
        
        _LOGGER.warning("hs Value")
        _LOGGER.warning(hs_color)
        _LOGGER.warning("white Value")
        _LOGGER.warning(white)
        _LOGGER.warning("brightness Value")
        _LOGGER.warning(brightness)

        if not self._state:
            command = "55" + "1001" + "0d0a"
            self.write_command(command)
            _LOGGER.debug("Ampoule allumée avec succès")
        
        if white is not None:
            #self._hs_color = (0, 0)
            self._white = white
            whiteten = round((white / 2.55 ) / 10)
            if whiteten < 2:
                whiteten = 2

            command = "55" + "110" + str(hex(whiteten)[2:]) + "0d0a"
            self.write_command(command)

        if hs_color is not None:
            self._brightness = 255
            self._hs_color = hs_color
            rgb = color_util.color_hsv_to_RGB(hs_color[0], hs_color[1], self._brightness / 255 * 100)
            _LOGGER.warning("RGB Value")
            _LOGGER.debug(rgb)
            _LOGGER.debug(str(hex(rgb[0])[2:]).rjust(2,'0'))
            _LOGGER.debug(str(hex(rgb[1])[2:]).rjust(2,'0'))
            _LOGGER.debug(str(hex(rgb[2])[2:]).rjust(2,'0'))
            command = "55" + "13" + str(hex(rgb[0])[2:]).rjust(2,'0') + str(hex(rgb[1])[2:]).rjust(2,'0') + str(hex(rgb[2])[2:]).rjust(2,'0') + "0d0a"
            self.write_command(command)

        if brightness is not None:
            self._rgb = (255, 255, 255)
            self._brightness = brightness
            brightnessten = round((brightness / 2.55 ) / 10)

            if brightnessten < 2:
                brightnessten = 2

            command = "55" + "120" + str(hex(brightnessten)[2:]) + "0d0a"
            self.write_command(command)
        
        self._state = True
                   
    def write_command(self, command):
        _LOGGER.debug("write_command()")
        if not self.test_connection():
            try:
                self.connect()
            except Exception as e:
                _LOGGER.error(e)
                return

        _LOGGER.debug("Tentative de connexion à l'adresse " + self._address)
        #device = btle.Peripheral(self._address, btle.ADDR_TYPE_PUBLIC, 0)
        _LOGGER.warning("Envoi de la trame: " + command)
        self._connection.writeCharacteristic(0x0021,bytes.fromhex(command))
        

    def get_settings(self):
        _LOGGER.debug("get_settings()")
        settings = []

        if not self.test_connection():
            try:
                self.connect()
            except Exception as e:
                _LOGGER.error(e)
                return
  
        settings = self._connection.readCharacteristic(0x0024)
        _LOGGER.debug("Settings: " + str(settings))
        
        return settings
    
    def turn_off(self, **kwargs):
        _LOGGER.debug("turn_off()")
        """Instruct the light to turn off."""
        command = "55" + "1000" + "0d0a"
        self.write_command(command)
        self._state = False
        _LOGGER.debug("Ampoule éteinte avec succès")

    def update(self):
        _LOGGER.debug("Update()")
        try:
            settings = self.get_settings()
            bulbIsOn = (settings[0] % 2) == 1
            bulbIsWhite = (settings[1] & 15) > 0
            brightness = (settings[1] & 240) >> 4

            if brightness < 2 :
                brightness = 2

            tone = (settings[1] & 15) - 2

            if tone < 2 :
                tone = 2

            self._state = bulbIsOn
            self._brightness = (brightness * 2.55) * 10
            self._white = (tone * 2.55) * 10
            rgb = (settings[2], settings[3], settings[4])
            _LOGGER.debug(rgb)
            hsv = color_util.color_RGB_to_hsv(*rgb)
            self._hs_color = hsv[:2]
        except Exception:
            self._state = False
        
    def test_connection(self):
        """
        Test if the connection is still alive
        
        :return: True if connected
        """
        if not self.is_connected():
            return False

        # send test message, read bulb name
        try:
            self._connection.readCharacteristic(0x0024)
        except btle.BTLEException:
            self.disconnect()
            return False
        except BrokenPipeError:
            # bluepy-helper died
            self._connection = None
            return False

        return True
    
    def is_connected(self):
        """
        :return: True if connected
        """
        return self._connection is not None  # and self.test_connection()
    
    def connect(self, bluetooth_adapter_nr=0):
        """
        Connect to device
        
        :param bluetooth_adapter_nr: bluetooth adapter name as shown by
            "hciconfig" command. Default : 0 for (hci0)
        
        :return: True if connection succeed, False otherwise
        """
        _LOGGER.debug("Connecting...")

        try:
            connection = btle.Peripheral(self._address, btle.ADDR_TYPE_PUBLIC,
                                         bluetooth_adapter_nr)
            self._connection = connection.withDelegate(self)
            #self._subscribe_to_recv_characteristic()
        except RuntimeError as e:
            _LOGGER.error('Connection failed : {}'.format(e))
            return False

        return True

    def disconnect(self):
        """
        Disconnect from device
        """
        _LOGGER.debug("Disconnecting...")

        try:
            self._connection.disconnect()
        except btle.BTLEException:
            pass

        self._connection = None
