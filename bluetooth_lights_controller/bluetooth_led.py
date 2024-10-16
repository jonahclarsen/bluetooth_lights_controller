from enum import IntEnum
from colour import Color
from bleak import BleakClient
from .shades_of_white import values as SHADES_OF_WHITE

UUID_CONTROL_CHARACTERISTIC = '00010203-0405-0607-0809-0a0b0c0d2b11'


def color2rgb(color):
    """ Converts a color-convertible into 3-tuple of 0-255 valued ints. """
    col = Color(color)
    rgb = col.red, col.green, col.blue
    rgb = [round(x * 255) for x in rgb]
    return tuple(rgb)


class LedCommand(IntEnum):
    """ A control command packet's type. """
    POWER = 0x01
    BRIGHTNESS = 0x04
    COLOR = 0x05


class LedMode(IntEnum):
    """
    The mode in which a color change happens in.

    Currently only manual is supported.
    """
    MANUAL = 0x02 # 0x02 for H6001, 0x0d for H6005
    MANUAL_H6005 = 0x0d
    MICROPHONE = 0x06
    SCENES = 0x05


class BluetoothLED:
    def __init__(self, mac, timeout=5):
        self.mac = mac
        services = {  # '0000180a-0000-1000-8000-00805f9b34fb',
            '00010203-0405-0607-0809-0a0b0c0d1910'}  # , '00010203-0405-0607-0809-0a0b0c0d1912'}
        # These are the only three services these lights use. Excluding the unused two seems to make
        # changing all the lights take ~4.1s instead of ~5.1s.
        # This is the best optimization I could find after hours of effort 2024-04-03 :(
        # A lot of the time is spent on discovering services, so I hoped to cache that object.
        # But this seems impossible with Bleak, since the services.obj object is stored
        # as an objective-c object which can't be pickled. Maybe it can be done with a C++ library
        # like SimpleBLE, but honestly I am not optimistic
        self._bt = BleakClient(mac, timeout=timeout)#, services=services)

    async def init_and_connect(self):
        try:
            await self._bt.connect()
        except Exception as e:
            print("Uhh!!", e)
            return False
        # We could print this, but it's a bit annoying:
        # print(self._bt.is_connected)

    def __del__(self):
        self._cleanup()

    # There seem to be some issues revolving around disconnecting from BLE objects using Bleak.
    # https://github.com/hbldh/bleak/issues/133
    # https://stackoverflow.com/questions/39599252/windows-ble-uwp-disconnect
    # Though, removing the resources for the connection should do the trick.
    def _cleanup(self):
        self._bt = None

    async def disconnect(self):
        if self._bt is not None:
            await self._bt.disconnect()
            self._bt = None

    def set_state(self, onoff):
        """ Controls the power state of the LED. """
        return self._send(LedCommand.POWER, [0x1 if onoff else 0x0])

    async def set_brightness(self, value):
        """
        Sets the LED's brightness.

        `value` must be a value between 0.0 and 1.0
        """
        if not 0 <= float(value) <= 1:
            raise ValueError(f'Brightness out of range: {value}')
        value = round(value * 0xFF)
        return await self._send(LedCommand.BRIGHTNESS, [value])

    async def set_color(self, color, is_h6005 = False):
        """
        Sets the LED's color.

        `color` must be a color-convertible (see the `colour` library),
        e.g. 'red', '#ff0000', etc.
        """

        mode = LedMode.MANUAL

        if is_h6005:
            mode = LedMode.MANUAL_H6005

        return await self._send(LedCommand.COLOR, [mode, *color2rgb(color)])

    async def set_color_white(self, value, is_h6005 = False):
        """
        Sets the LED's color in white-mode.

        `value` must be a value between -1.0 and 1.0
        White mode seems to enable a different set of LEDs within the bulb.
        This method uses the hardcoded RGB values of whites, directly taken from
        the mechanism used in Govee's app.
        """
        if not -1 <= value <= 1:
            raise ValueError(f'White value out of range: {value}')
        value = (value + 1) / 2  # in [0.0, 1.0]
        index = round(value * (len(SHADES_OF_WHITE) - 1))
        white = Color(SHADES_OF_WHITE[index])

        mode = LedMode.MANUAL

        if is_h6005:
            mode = LedMode.MANUAL_H6005

        # Set the color to white (although ignored) and the boolean flag to True
        return await self._send(LedCommand.COLOR, [mode, 0xff, 0xff, 0xff, 0x01, *color2rgb(white)])

    async def _send(self, cmd, payload):
        """ Sends a command and handles paylaod padding. """
        if not isinstance(cmd, int):
            raise ValueError('Invalid command')
        if not isinstance(payload, bytes) and not (
                isinstance(payload, list) and all(isinstance(x, int) for x in payload)):
            raise ValueError('Invalid payload')
        if len(payload) > 17:
            raise ValueError('Payload too long')

        cmd = cmd & 0xFF
        payload = bytes(payload)

        frame = bytes([0x33, cmd]) + bytes(payload)
        # pad frame data to 19 bytes (plus checksum)
        frame += bytes([0] * (19 - len(frame)))

        # The checksum is calculated by XORing all data bytes
        checksum = 0
        for b in frame:
            checksum ^= b

        frame += bytes([checksum & 0xFF])

        # return frame

        async def main():
            await self._bt.write_gatt_char(UUID_CONTROL_CHARACTERISTIC, frame)

        await main()

        # self._dev.char_write(UUID_CONTROL_CHARACTERISTIC, frame)
        # Implement Bleak's BLE functionality here. This replaces the original implementation's use of pyGATT, which is not
        # supported on most Windows Bluetooth interfaces or devices.
