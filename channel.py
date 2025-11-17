from pyscript import document, window, WebSocket
import asyncio
import json
from time import sleep
import inspect, sys


def iscoroutinefunction(obj):
    is_mp = "micropython" in sys.version.lower()
    if is_mp:
        if "<closure <generator>" in repr(obj):
            return True
        return inspect.isgeneratorfunction(obj)
    return inspect.iscoroutinefunction(obj)



# ======================================================
#       CHANNEL CLASS WITH F-STRING HTML TEMPLATE
# ======================================================

class CEEO_Channel:

    def __init__(
        self,
        channel,
        user,
        project,
        divName='all_things_channels',
        suffix='_test',
        default_topic="/LEGO"
    ):
        self.channel = channel
        self.user = user
        self.project = project
        self.suffix = suffix
        self.value = 0
        self.callback = None
        self.is_connected = False

        # ---------------------------
        # Inject clean HTML template
        # ---------------------------
        ChannelHTML = f"""
<style>

.channel-container {{
    background: none !important;
    border: none !important;
    width: 100%;
}}

.channel-grid {{
    display: grid;
    grid-template-columns: 1fr;
    gap: 8px;
}}

.channel-row {{
    display: flex;
    align-items: center;
    gap: 8px;
}}

.channel-label {{
    font-size: 14px;
    color: #333;
}}

.channel-input {{
    padding: 4px 6px;
    font-size: 14px;
    border: 1px solid #ccc;
    border-radius: 4px;
    flex: 1;
}}

.small-btn {{
    padding: 4px 14px;
    font-size: 14px;
    border-radius: 6px;
    border: 1px solid #aaa;
    background: #f7f7f7;
    cursor: pointer;
}}

.dimmed {{
    opacity: 0.2 !important;
    pointer-events: none !important;
}}

#live{suffix} {{
    width: 14px;
    height: 14px;
    border-radius: 50%;
    background: red;
}}

/* HIDDEN MESSAGE LOG */
.message-log {{
    display: none !important;
}}

.log-entry {{
    padding: 0;
    margin: 0;
}}

.log-highlight {{
    background: #f1d15a;
    color: #000;
    font-weight: bold;
    padding: 0 4px;
    border-radius: 3px;
}}

</style>

<div class="channel-container">
    <div class="channel-grid">
        <div style="display:flex; flex-direction:column; gap:6px;">

            <div class="channel-row">
                <div id="live{suffix}"></div>
                <button id="channel_connect{suffix}" class="small-btn">Connect</button>
                <input id="topic{suffix}" class="channel-input" value="{default_topic}">
                <span class="channel-label">Received:</span>
                <label id="channelValue{suffix}" class="channel-label">0</label>
            </div>

            <div class="channel-row">
                <button id="send{suffix}" class="small-btn">Send Message</button>
                <input id="payload{suffix}" class="channel-input" value="send this">
            </div>
            <br>

            <div class="channel-row">
                <span class="channel-label">Start program when I receive:</span>
                <input id="trigger{suffix}" class="channel-input" value="My turn message">
            </div>

            <div class="channel-row">
                <span class="channel-label">After program finishes, send:</span>
                <input id="posttrigger{suffix}" class="channel-input" value="Next turn message">
            </div>

            <div id="log{suffix}" class="message-log"></div>

        </div>
    </div>
</div>
        """

        # Inject into DOM
        root = document.getElementById(divName)
        root.innerHTML = ChannelHTML

        # Hook up DOM references
        self.topic = document.getElementById(f"topic{suffix}")
        self.valueLabel = document.getElementById(f"channelValue{suffix}")
        self.payload = document.getElementById(f"payload{suffix}")
        self.trigger_box = document.getElementById(f"trigger{suffix}")
        self.posttrigger_box = document.getElementById(f"posttrigger{suffix}")
        self.connect_btn = document.getElementById(f"channel_connect{suffix}")
        self.send_btn_el = document.getElementById(f"send{suffix}")
        self.liveIndicator = document.getElementById(f"live{suffix}")
        self.log_div = document.getElementById(f"log{suffix}")

        # Bind events
        self.connect_btn.onclick = self.connect_disconnect
        self.send_btn_el.onclick = self._send_btn

        # Create post-trigger JS callback
        self._register_posttrigger_callback()

        # Start disconnected
        self._apply_disconnected_ui()



    # ======================================================
    #        POST-TRIGGER SEND (JS CALLS PYTHON)
    # ======================================================

    def _register_posttrigger_callback(self):
        def js_post():
            if not self.is_connected:
                return
            msg = self.posttrigger_box.value.strip()
            loop = asyncio.get_event_loop()
            loop.create_task(self.post(self.topic.value, msg))

        window.channel_posttrigger = js_post



    # ======================================================
    #                    UI DIMMING
    # ======================================================

    def _apply_connected_ui(self):
        for el in [
            self.send_btn_el, self.payload,
            self.trigger_box, self.posttrigger_box
        ]:
            el.classList.remove("dimmed")

    def _apply_disconnected_ui(self):
        for el in [
            self.send_btn_el, self.payload,
            self.trigger_box, self.posttrigger_box
        ]:
            el.classList.add("dimmed")



    # ======================================================
    #             CONNECT & DISCONNECT LOGIC
    # ======================================================

    def connect_disconnect(self, event):
        if not self.is_connected:
            self._setupSocket()
            self.connect_btn.innerText = "Disconnect"
        else:
            self.close()
            self.connect_btn.innerText = "Connect"

    def _setupSocket(self):
        self.url = (
            f"wss://{self.user}.pyscriptapps.com/"
            f"{self.project}/api/channels/{self.channel}"
        )
        self._openSocket()

    def _openSocket(self):

        def onopen(evt):
            self.is_connected = True
            self.liveIndicator.style.backgroundColor = "green"
            self._apply_connected_ui()

        def onclose(evt):
            self.is_connected = False
            self.liveIndicator.style.backgroundbackgroundColor = "red"
            self._apply_disconnected_ui()

        self.socket = WebSocket(
            url=self.url,
            onopen=onopen,
            onclose=onclose,
            onmessage=self.onmessage
        )

    def close(self):
        try:
            self.socket.close()
        except:
            pass
        self.is_connected = False
        self.liveIndicator.style.backgroundColor = "red"
        self._apply_disconnected_ui()



    # ======================================================
    #                       SEND
    # ======================================================

    async def post(self, topic, value):
        if not self.is_connected:
            return
        try:
            payload = {"topic": topic, "value": value}
            self.socket.send(json.dumps(payload))
        except Exception as e:
            window.console.log("POST ERROR:", e)

    async def _send_btn(self, event):
        if not self.is_connected:
            return
        await self.post(self.topic.value, self.payload.value)



    # ======================================================
    #              RECEIVE / TRIGGER LOGIC
    # ======================================================

    async def onmessage(self, event):
        try:
            msg = json.loads(event.data)
            if msg.get("type") == "welcome":
                return
            if msg.get("type") == "data":
                payload = json.loads(msg["payload"])
                await self._on_data(payload)
        except Exception:
            window.console.log("RECEIVE ERROR:", event.data)

    async def _on_data(self, payload):
        value = payload.get("value", "")

        # Update UI
        self.value = value
        self.valueLabel.innerText = value

        # Log only latest (still functional but invisible)
        self._log_latest(value)

        # Trigger check
        trigger = self.trigger_box.value.strip()
        if str(value).strip() == trigger:
            self._log_trigger(value)
            try:
                window.triggerChannelMessage(str(value))
            except:
                pass

        # Optional callback
        if self.callback:
            if iscoroutinefunction(self.callback):
                await self.callback(payload)
            else:
                self.callback(payload)



    # ======================================================
    #   COLLAPSED ONE-LINE LOG WITH TRIGGER HIGHLIGHTING
    # ======================================================

    def _log_latest(self, value):
        if not self.log_div:
            return
        self.log_div.innerHTML = ""
        entry = document.createElement("div")
        entry.classList.add("log-entry")
        entry.innerText = str(value)
        self.log_div.appendChild(entry)

    def _log_trigger(self, value):
        if not self.log_div:
            return
        self.log_div.innerHTML = ""
        entry = document.createElement("div")
        entry.classList.add("log-entry", "log-highlight")
        entry.innerText = str(value)
        self.log_div.appendChild(entry)
