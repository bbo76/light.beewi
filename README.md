# Beewi Light (BLE) platform for Home Assistant

![Bulb](https://github.com/bbo76/light.beewi/blob/master/BeewiBulb.jpg)

This custom components let you control Beewi bulbs by BLE protocol.
You can switch ON/OFF the light or changing state:
 - Intensity
 - Warm
 - Color

# Configuration
Add the following to your `configuration.yaml` file.

```yaml
light:
  - platform: beewi_light
    name: Ampoule salon
    address: "XX:XX:XX:XX:XX:XX"
  ```

