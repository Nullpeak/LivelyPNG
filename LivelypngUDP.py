#!/usr/bin/env python3
"""
Global Keyboard Listener → UDP Bridge for OBS Tilt Script

Run this OUTSIDE of OBS (e.g., in terminal/cmd).
It listens for keyboard input globally and sends state via UDP to the OBS script.
"""

import socket
import json
import threading
import time
import sys

# --- Choose your backend ---
# Option 1: pynput (cross-platform, needs: pip install pynput)
# Option 2: keyboard (Windows/Linux, needs: pip install keyboard)
# Option 3: evdev (Linux only, no pip needed usually)

USE_BACKEND = "keyboard"  # Change to "keyboard" or "evdev" if preferred

# UDP Config (must match the OBS script's listener)
UDP_HOST = "127.0.0.1"
UDP_PORT = 45271

# Keys to track
KEY_MAP = {
    'a': 'a',
    'd': 'd',
    'shift': 'shift',
    'shift_r': 'shift',  # right shift
    'ctrl': 'ctrl',
    'ctrl_r': 'ctrl',     # right ctrl
    'control': 'ctrl',
    'control_r': 'ctrl',
}

class UDPSender:
    def __init__(self, host, port):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.addr = (host, port)
        self._lock = threading.Lock()
        self._last_state = None

    def send(self, state_dict):
        """Send key state only if it changed."""
        with self._lock:
            # Normalize state for comparison
            current = (
                state_dict.get('a', False),
                state_dict.get('d', False),
                state_dict.get('shift', False),
                state_dict.get('ctrl', False),
            )
            if current == self._last_state:
                return  # No change, skip UDP spam
            self._last_state = current

        payload = json.dumps(state_dict).encode('utf-8')
        try:
            self.sock.sendto(payload, self.addr)
        except Exception as e:
            print(f"[UDP Error] {e}")

    def close(self):
        self.sock.close()


class KeyState:
    def __init__(self):
        self.state = {'a': False, 'd': False, 'shift': False, 'ctrl': False}
        self._lock = threading.Lock()

    def set(self, key, pressed):
        with self._lock:
            self.state[key] = pressed

    def get(self):
        with self._lock:
            return dict(self.state)


# ============================================================
# BACKEND: pynput
# ============================================================
def run_pynput(sender, keystate):
    try:
        from pynput import keyboard
    except ImportError:
        print("pynput not installed. Run: pip install pynput")
        sys.exit(1)

    def on_press(key):
        try:
            k = key.char.lower() if hasattr(key, 'char') and key.char else None
        except AttributeError:
            k = None

        if k == 'a':
            keystate.set('a', True)
        elif k == 'd':
            keystate.set('d', True)
        elif key == keyboard.Key.shift or key == keyboard.Key.shift_r:
            keystate.set('shift', True)
        elif key == keyboard.Key.ctrl or key == keyboard.Key.ctrl_r:
            keystate.set('ctrl', True)

        sender.send(keystate.get())

    def on_release(key):
        try:
            k = key.char.lower() if hasattr(key, 'char') and key.char else None
        except AttributeError:
            k = None

        if k == 'a':
            keystate.set('a', False)
        elif k == 'd':
            False
            keystate.set('d', False)
        elif key == keyboard.Key.shift or key == keyboard.Key.shift_r:
            keystate.set('shift', False)
        elif key == keyboard.Key.ctrl or key == keyboard.Key.ctrl_r:
            keystate.set('ctrl', False)

        sender.send(keystate.get())

        # Stop listener on Esc (optional, remove if you don't want this)
        # if key == keyboard.Key.esc:
        #     return False

    print("[pynput] Listening for keys... (A, D, Shift, Ctrl)")
    print("[pynput] Press Ctrl+C to stop.")

    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()


# ============================================================
# BACKEND: keyboard
# ============================================================
def run_keyboard(sender, keystate):
    try:
        import keyboard as kb
    except ImportError:
        print("keyboard not installed. Run: pip install keyboard")
        sys.exit(1)

    def make_handler(key_name, obs_key):
        def on_press():
            keystate.set(obs_key, True)
            sender.send(keystate.get())
        def on_release():
            keystate.set(obs_key, False)
            sender.send(keystate.get())
        return on_press, on_release

    handlers = [
        ('a', 'a'), ('d', 'd'),
        ('shift', 'shift'), ('right shift', 'shift'),
        ('ctrl', 'ctrl'), ('right ctrl', 'ctrl'),
    ]

    for kb_key, obs_key in handlers:
        on_p, on_r = make_handler(kb_key, obs_key)
        kb.on_press_key(kb_key, lambda e, p=on_p: p())
        kb.on_release_key(kb_key, lambda e, r=on_r: r())

    print("[keyboard] Listening for keys... (A, D, Shift, Ctrl)")
    print("[keyboard] Press Ctrl+C to stop.")
    kb.wait()


# ============================================================
# BACKEND: evdev (Linux only)
# ============================================================
def run_evdev(sender, keystate):
    try:
        import evdev
        from evdev import InputDevice, categorize, ecodes
    except ImportError:
        print("evdev not installed. Run: pip install evdev")
        sys.exit(1)

    # Find keyboard devices
    devices = [InputDevice(path) for path in evdev.list_devices()]
    keyboards = [d for d in devices if 'keyboard' in d.name.lower() or 'kbd' in d.name.lower()]

    if not keyboards:
        print("No keyboard devices found via evdev.")
        sys.exit(1)

    print(f"[evdev] Found keyboards: {[k.name for k in keyboards]}")

    KEY_A = ecodes.KEY_A
    KEY_D = ecodes.KEY_D
    KEY_LEFTSHIFT = ecodes.KEY_LEFTSHIFT
    KEY_RIGHTSHIFT = ecodes.KEY_RIGHTSHIFT
    KEY_LEFTCTRL = ecodes.KEY_LEFTCTRL
    KEY_RIGHTCTRL = ecodes.KEY_RIGHTCTRL

    def read_device(dev):
        for event in dev.read_loop():
            if event.type != ecodes.EV_KEY:
                continue
            key_event = categorize(event)
            code = key_event.scancode
            pressed = key_event.keystate in (key_event.key_down, key_event.key_hold)

            if code == KEY_A:
                keystate.set('a', pressed)
            elif code == KEY_D:
                keystate.set('d', pressed)
            elif code in (KEY_LEFTSHIFT, KEY_RIGHTSHIFT):
                keystate.set('shift', pressed)
            elif code in (KEY_LEFTCTRL, KEY_RIGHTCTRL):
                keystate.set('ctrl', pressed)
            else:
                continue

            sender.send(keystate.get())

    threads = []
    for kbd in keyboards:
        t = threading.Thread(target=read_device, args=(kbd,), daemon=True)
        t.start()
        threads.append(t)

    print("[evdev] Listening for keys... (A, D, Shift, Ctrl)")
    print("[evdev] Press Ctrl+C to stop.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass


# ============================================================
# MAIN
# ============================================================
def main():
    print("=" * 50)
    print("OBS Tilt Keyboard Bridge")
    print("=" * 50)
    print(f"UDP Target: {UDP_HOST}:{UDP_PORT}")
    print(f"Backend:  {USE_BACKEND}")
    print("-" * 50)

    sender = UDPSender(UDP_HOST, UDP_PORT)
    keystate = KeyState()

    try:
        if USE_BACKEND == "pynput":
            run_pynput(sender, keystate)
        elif USE_BACKEND == "keyboard":
            run_keyboard(sender, keystate)
        elif USE_BACKEND == "evdev":
            run_evdev(sender, keystate)
        else:
            print(f"Unknown backend: {USE_BACKEND}")
    except KeyboardInterrupt:
        print("\n[Shutdown] Closing...")
    finally:
        sender.close()


if __name__ == "__main__":
    main()