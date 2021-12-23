# Beewi Light (BLE) platform for Home Assistant
[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=for-the-badge)](https://github.com/hacs/integration)

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
