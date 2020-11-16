import waggle.plugin as plugin
from random import random
from time import sleep

plugin.init()

while True:
    value = 25.0 + 5*random()
    print('publishing', value)
    plugin.publish('env.temperature', value)
    sleep(1)
