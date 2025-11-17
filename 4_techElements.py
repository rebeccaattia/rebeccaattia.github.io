from pyscript import document, window, when
import channel as _ch
import asyncio

# -------------------------
# CHANNEL SETUP
# -------------------------
mytopic = '/LEGO'
myChannel = _ch.CEEO_Channel(
    "hackathon", "@chrisrogers", "talking-on-a-channel",
    divName='all_things_channels', suffix='_test', default_topic=mytopic
)
document.getElementById('topic_test').innerHTML = mytopic


class Channel:
    """
    You can use this function to read or write to the channel.
        channel.send('some text') will send a string (or number) on topic '/LEGO'
        channel.msg has the latest message on the '/LEGO' channel
    """
    def __init__(self):
        self.msg = None
        self.value = -1
        myChannel.callback = self._receive 

    def _receive(self, message):
        thetopic = document.getElementById('topic_test').value
        topic, msg = myChannel.check(thetopic, message)
        if msg:  
            self.msg = msg
            try:
                number = float(msg)
                self.value = int(number) if number % 1.0 == 0 else number
            except:
                self.value = -1

            # Notify JavaScript side
            try:
                window.channel.msg = msg
            except Exception as e:
                window.console.log(f"Failed to update JS channel.msg: {e}")

    async def _sendIt(self, msg):
        thetopic = document.getElementById('topic_test').value
        return await myChannel.post(thetopic, msg)
        
    def send(self, msg):
        loop = asyncio.get_event_loop()
        success = loop.create_task(self._sendIt(msg))


channel = Channel()


# -------------------------
# TECH ELEMENTS
# -------------------------
import code
import Hub 
class Element:
    """You can use this function to read or write to a tech element.
        element.update_rate(1000) will update all sensor readings every 1 sec
        element.value has the latest sensor reading selected by the dropdown menu
    """
    def __init__(self, divName = 'all_things_hub', suffix = '_repl', hub = 2): # hub0 = spike, hub1 = Old TE, hub2 = TE
        self._hub = Hub.Hub_PS(divName, suffix, hub)  
        self.value = -1
        self.hubType = False
        self._hub.final_callback = self._new_data
        self._hub.info_callback = self._information

    async def _information(self, info):
        self.info = info
        try:
            self.hubType = info['GroupID']
            window.console.log(self.hubType)
            if self.hubType == 512:  # Single Motor
                def run(speed = None, port = 1, direction = 2):
                    if speed != None:
                        self.set_speed(speed, port)
                    fmt, ID, val = self._hub.hubInfo.commands.get('motor_run')
                    val['values']['port'] = port
                    val['values']['direction'] = direction & 0x03
                    self._send(fmt, ID, val) 
                
                def myspeed(speed_value = 100, port = 1): 
                    fmt, ID, val = self._hub.hubInfo.commands.get('motor_speed')
                    val['values']['port'] = port
                    val['values']['speed'] = speed_value  
                    self._send(fmt, ID, val) 
                
                def stop(port = 1):  
                    fmt, ID, val = self._hub.hubInfo.commands.get('motor_stop')
                    val['values']['port'] = port
                    self.set_speed(0, port)
                
                self.run = run
                self.stop = stop
                self.set_speed = myspeed  
                
            if self.hubType == 513:  # Double Motor
                def run(speed = None, port = 1, direction = 2):
                    if speed != None:
                        self.set_speed(speed, port)
                    fmt, ID, val = self._hub.hubInfo.commands.get('motor_run')
                    val['values']['port'] = port
                    val['values']['direction'] = direction & 0x03
                    self._send(fmt, ID, val) 
                
                def myspeed(speed_value = 100, port = 1): 
                    fmt, ID, val = self._hub.hubInfo.commands.get('motor_speed')
                    val['values']['port'] = port
                    val['values']['speed'] = speed_value  
                    self._send(fmt, ID, val) 
                
                def stop(port = 3):  
                    fmt, ID, val = self._hub.hubInfo.commands.get('motor_stop')
                    cmds = []
                    if port == 3:
                        val['values']['port'] = 1
                        cmds.append((fmt, ID, {'values':{'port':1}})) 
                        val['values']['port'] = 2
                        cmds.append((fmt, ID, {'values':{'port':2}})) 
                        self._sendMult(cmds) 
                        window.console.log('stopped')
                    else:
                        val['values']['port'] = port
                        self._send(fmt, ID, val) 
                    
                def runL(speed = 100):
                    if speed != None:
                        self.set_speed(speed, 1)
                    self.run(None, 1,2)

                def runR(speed = 100):
                    if speed != None:
                        self.set_speed(-speed, 2)
                    self.run(None, 2,2)

                def runB(speed_value = 100):
                    cmds = []
                    if speed_value != None:
                        cmds = []
                        fmt, ID, val = self._hub.hubInfo.commands.get('motor_speed')
                        cmds.append((fmt, ID, {'values':{'port':1,'speed':-speed_value}})) 
                        window.console.log('current val: ',cmds)
                        cmds.append((fmt, ID, {'values':{'port':2,'speed':speed_value}})) 
                        window.console.log('current val: ',cmds)

                        '''fmt, ID, val = self._hub.hubInfo.commands.get('motor_speed')
                        val['values']['port'] = 1
                        val['values']['speed'] = speed_value  
                        cmds.append((fmt, ID, val)) 
                        window.console.log('current val: ',cmds)
                        val2 = val.copy()
                        val2['values']['port'] = 2
                        cmds.append((fmt, ID, val2)) 
                        window.console.log('current val: ',cmds)'''
                    fmt, ID, val = self._hub.hubInfo.commands.get('motor_run')
                    val['values']['port'] = 1
                    val['values']['direction'] = 1
                    cmds.append((fmt, ID, {'values':{'port':1,'direction':1}})) 
                    val['values']['port'] = 2
                    val['values']['direction'] = 2
                    cmds.append((fmt, ID, {'values':{'port':2,'direction':1}})) 
                    self._sendMult(cmds) 

                self.run = run
                self.stop = stop
                self.set_speed = myspeed  
                self.run_left = runL
                self.run_right = runR
                self.run_both = runB
        except Exception as e:
            window.console.log('Error in _information: ',e)

    async def _sendIt(self, fmt, ID, val):
        try:
            await self._hub.send(fmt, ID, val) 
            window.console.log('sent: ',fmt, ID, val)
            return True
        except asyncio.CancelledError:
            print("Task was cancelled due to timeout.")
            raise
        return  False
        
    async def _sendItMult(self, cmds):
        try:
            for (fmt, ID, val) in cmds:
                await self._hub.send(fmt, ID, val) 
                window.console.log('sent: ',fmt, ID, val)
            return True
        except asyncio.CancelledError:
            print("Task was cancelled due to timeout.")
            raise
        return  False
        
    def _send(self, fmt, ID, val):
        loop = asyncio.get_event_loop()
        window.console.log('I think I sent: ',fmt, ID, val)
        try:
            task = asyncio.wait_for(self._sendIt(fmt, ID, val), timeout=6)
            loop.create_task(task)
            return True
        except asyncio.TimeoutError:
            print("A timeout occurred in the sync function!")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
        return False

    def _sendMult(self,cmds):
        loop = asyncio.get_event_loop()
        window.console.log('I think I sent: ',cmds)
        try:
            task = asyncio.wait_for(self._sendItMult(cmds), timeout=6)
            loop.create_task(task)
            return True
        except asyncio.TimeoutError:
            print("A timeout occurred in the sync function!")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
        return False

    async def _new_data(self, reply):
        try:
            self.value = self._hub.value
            reply = self._hub.reply
            if 'Motor_1' in reply.keys():
                self.position = reply['Motor_1']['position']
                #window.console.log(self.position)
                self.angle = reply['Motor_1']['angle']
                self.speed = reply['Motor_1']['speed']
                self.battery = reply['hub info']['Battery']
                
            if 'Motor_2' in reply.keys():
                self.position2 = reply['Motor_2']['position']
                self.angle2 = reply['Motor_2']['angle']
                self.speed2 = reply['Motor_2']['speed']
                self.battery2 = reply['hub info']['Battery']
                
            if 'Color' in reply.keys(): #'color', 'reflection', 'red', 'green', 'blue', 'hue', 'saturation', 'value'
                self.color = reply['Color']['color']
                self.reflection = reply['Color']['reflection']
                self.rgb = (reply['Color']['red'], reply['Color']['green'], reply['Color']['blue'])
                self.hsv = (reply['Color']['hue'], reply['Color']['stauration'], reply['Color']['value'])
                self.battery = reply['hub info']['Battery']
                
            if 'Joystick' in reply.keys():  #'leftStep', 'rightStep','leftAngle','rightAngle'
                self.leftStep = reply['Joystick']['leftStep']
                self.rightStep = reply['Joystick']['rightStep']
                self.leftAngle = reply['Joystick']['leftAngle']
                self.rightAngle = reply['Joystick']['rightAngle']
                self.battery = reply['hub info']['Battery']
        except:
            pass

    async def update_rate(self,rate = 20):
        await self._hub.feed_rate(rate)  #millisec - 20 is the fastest

motor = Element('hub1', '_1', 2)
await motor.update_rate(20)
sensor = Element('hub2', '_2', 2)
await sensor.update_rate(20)
document.getElementById('title_2').innerText = ''
_e1 = document.getElementById('var_1')
_e1.value = 'motor'
_e2 = document.getElementById('var_2')
_e2.value = 'sensor'

@when('change','#var_1')
def rename():
    _e1.value = _e1.value.replace(' ','_')
    exec(f"{_e1.value} = motor ")
@when('change','#var_2')
def rename2():
    _e2.value = _e2.value.replace(' ','_')
    exec(f"{_e2.value} = sensor ")

    

# -------------------------
# INTERACTIVE SESSION
# -------------------------
code.interact()
