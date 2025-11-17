from js
import time, asyncio
import channel as _ch

myChannel = _ch.CEEO_Channel(
    "hackathon",
    "@chrisrogers",
    "talking-on-a-channel",
    divName="all_things_channels",
    suffix="_test",
    default_topic="/LEGO"
)