"""
Author: Liam Collod
Last Modified: 10/01/2020

Python 2.7 only
Katana script, tested on 3.6v4
"""

from .textureMonitor.script import TextureMonitorUI, VERSION

# Register the TAB in the Katana UI
PluginRegistry = [
    ('KatanaPanel', 2.0, 'Textures Monitor v{}'.format(VERSION), TextureMonitorUI)
]

