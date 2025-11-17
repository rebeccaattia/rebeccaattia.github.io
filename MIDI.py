code = '''# loads a simple MIDI driver
import time
from BLE_CEEO import Yell

NoteOn = 0x90
NoteOff = 0x80
StopNotes = 123
SetInstroment = 0xC0
Reset = 0xFF
off = 0
pppp = 8
ppp = 20
pp= 31
p = 42
mp = 53
mf = 64
f = 80
ff = 96
fff = 112
ffff = 127
    
class Instrument:
    def __init__(self, name = 'Fred'):
        self.midi = Yell(name, verbose = True, type = 'midi')
    
    def connect_up(self):
        self.midi.connect_up()
        
    def disconnect(self):
        self.midi.disconnect()
    
    def play(self, cmd, notes, vel = f, channel = 0):
        channel = 0x0F & channel
        timestamp_ms = time.ticks_ms()
        tsM = (timestamp_ms >> 7 & 0b111111) | 0x80
        tsL =  0x80 | (timestamp_ms & 0b1111111)
        c =  cmd | channel 
        for n in notes:
            payload = [tsM,tsL,c,n,vel]
            self.midi.send(bytes(payload))'''
