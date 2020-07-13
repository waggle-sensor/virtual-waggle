from waggle.plugin import Plugin
from time import sleep

plugin = Plugin()

while True:
    print('publishing')
    plugin.add_measurement({'id': 1, 'sub_id': 1, 'value': 12.34})
    plugin.publish_measurements()
    sleep(1)
