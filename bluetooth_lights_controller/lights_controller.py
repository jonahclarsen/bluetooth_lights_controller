import asyncio
from .bluetooth_led import BluetoothLED

timeout = 5.0  # Seems to work well

async def set_state_of_light(mac_address, state, is_h6005 = False):
    print("Setting the states of the lights is really buggy, I don't recommend it! Prefer to set the brightness to 0.")

    led = BluetoothLED(mac_address, timeout=timeout)
    boolt = await led.init_and_connect()
    if boolt is False:
        return
    await led.set_state(state)
    await led.disconnect()

async def set_color_of_light(mac_address, color, brightness, is_h6005 = False):
    led = BluetoothLED(mac_address, timeout=timeout)

    boolt = await led.init_and_connect()

    if boolt is False:
        return
    # await led.set_state(True)  # If your lights are ever turned off (i.e. via the app), uncomment this

    await led.set_color(color, is_h6005)
    await led.set_brightness(brightness)
    await asyncio.sleep(.05)
    await led.disconnect()


async def set_color_of_light_white(mac_address, color, brightness, is_h6005 = False):
    led = BluetoothLED(mac_address, timeout=timeout)
    boolt = await led.init_and_connect()
    if boolt is False:
        print("Failed to connect!")
        return
    # await led.set_state(True)  # If your lights are ever turned off (i.e. via the app), uncomment this

    await led.set_color_white(color, is_h6005)
    await led.set_brightness(brightness)
    await asyncio.sleep(.05)  # I found 0.009 worked and 0.001 didn't (but then later .001 worked...?; note I was
    # using 0.01 until MacOS 14 when it no longer worked, I had to switch to .05 like in the other func)
    await led.disconnect()

from pprint import pprint
async def set_color_of_all_lights(lights, color, brightness):
    # Optimization: first, get the services of one of the LEDs:
    # led1 = BluetoothLED(lights["bedroom-1"], None, timeout=timeout)
    # boolt = await led1.init_and_connect()
    # services = led1._bt.services
    # To find out what services this devices uses so we can filter by them when connectingZ:
    # # pprint(services._BleakGATTServiceCollection__services)
    # # pprint(services._BleakGATTServiceCollection__services[12].uuid)
    # # pprint(services._BleakGATTServiceCollection__services[15].uuid)
    # # pprint(services._BleakGATTServiceCollection__services[23].uuid)
    # await led1.disconnect()

    i = 0
    tasks = []
    for light_name, mac_address in lights.items():
        try:
            is_h6005 = False
            if "h6005" in light_name or "H6005" in light_name:
                is_h6005 = True

            tasks += [asyncio.create_task(set_color_of_light(mac_address, color, brightness, is_h6005))]
            i += 1
        except Exception as e:
            print("Exception in lights_controller:", e)

    for task in tasks:
        await task


async def set_state_of_all_lights(lights, state):
    i = 0
    tasks = []
    for light_name, mac_address in lights.items():
        try:
            is_h6005 = False
            if "h6005" in light_name or "H6005" in light_name:
                is_h6005 = True

            tasks += [asyncio.create_task(set_state_of_light(mac_address, state, is_h6005))]
            i += 1
        except Exception as e:
            print("Exception in lights_controller:", e)

    for task in tasks:
        await task


async def set_color_of_all_lights_white(lights, color, brightness):
    i = 0
    tasks = []
    for light_name, mac_address in lights.items():
        try:
            is_h6005 = False
            if "h6005" in light_name or "H6005" in light_name:
                is_h6005 = True

            tasks += [asyncio.create_task(set_color_of_light_white(mac_address, color, brightness, is_h6005))]
            i += 1
        except Exception as e:
            print("Exception!", e)

    for task in tasks:
        await task
