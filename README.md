# 🎬 LivelyPNG — Animated PNG Vtuber for OBS

Give your PNG vtuber smooth, physics-y movement — tilts, drops, bounces — all driven by keypresses, directly inside OBS.

> ⚙️ **Everything is configurable from the OBS Scripts panel. No code editing needed.**

---

## ✨ What it does

| Action | Effect |
|---|---|
| Hold **A** | Tilt left |
| Hold **D** | Tilt right |
| Hold **A + D** | Stays centered |
| Hold **Shift** | Small downward drop |
| Hold **Ctrl** | Big downward drop |
| Release any key | Smooth return to neutral |

All transitions use a **custom cubic Bézier easing curve**, giving that satisfying springy feel. Tilt angle, drop distance, animation duration and curve shape are all adjustable from OBS.

---

## 📦 Files

```
LivelyPNG/
├── Livelypng.py          # ✅ Standalone — hotkeys registered inside OBS
├── Livelypngbridge.py    # 🌐 UDP mode — OBS-side listener
└── LivelypngUDP.py       # ⌨️  Run outside OBS — sends key state over UDP
```

---

## 🚀 Setup

### Option A — Standalone (simplest)

> Use this if you only want hotkeys bound inside OBS.

1. In OBS: **Tools → Scripts → ➕** → select `Livelypng.py`
2. Set your source name (default: `vtuber`) and adjust settings
3. Go to **Settings → Hotkeys** → assign keys to:
   - `Smooth Tilt Left (A)`
   - `Smooth Tilt Right (D)`
   - `Smooth Drop (Shift)`
   - `Smooth Drop Heavy (Ctrl)`
4. Done ✅

---

### Option B — UDP Bridge (recommended for gaming/streaming)

> Use this if you want **global** keypress detection while OBS is in the background — ideal when you're playing a game and still want the avatar to react.

**Step 1 — Load the OBS listener script**

1. **Tools → Scripts → ➕** → select `Livelypngbridge.py`
2. Configure source name, animation settings, and UDP port (default: `45271`)

**Step 2 — Run the keyboard bridge outside OBS**

```bash
pip install keyboard   # or: pip install pynput
python LivelypngUDP.py
```

> Inside `LivelypngUDP.py`, change `USE_BACKEND` to `"pynput"`, `"keyboard"`, or `"evdev"` depending on your OS and preference.

| Backend | OS | Install |
|---|---|---|
| `keyboard` | Windows / Linux | `pip install keyboard` |
| `pynput` | Windows / macOS / Linux | `pip install pynput` |
| `evdev` | Linux only | `pip install evdev` |

**Step 3 — Press A, D, Shift, Ctrl — watch your avatar move!**

---

## ⚙️ Configuration (inside OBS — no code needed)

All settings live in **Tools → Scripts → [your script]**:

| Setting | Description |
|---|---|
| **Source name** | The name of your PNG source in OBS |
| **Tilt angle (°)** | How far left/right it rotates (0–45°) |
| **Animation duration (ms)** | How long each transition takes |
| **Drop with Shift (px)** | Pixels to drop on Shift |
| **Drop with Ctrl (px)** | Pixels to drop on Ctrl |
| **Bézier X1/Y1/X2/Y2** | Shape of the easing curve |
| **UDP Host / Port** | *(Bridge only)* Where to receive key events |

---

## 🎬 Preview



https://github.com/user-attachments/assets/5093bccd-83f3-439a-9aad-f82bd0934343



---

## 💡 Tips

- Your PNG source must be named exactly as written in the **Source name** field (case-sensitive).
- The script auto-detects the source's base position and rotation on load — if you move the source, reload the script.
- The Bézier curve defaults (`X1=0.34, Y1=0.12, X2=0.09, Y2=0.98`) give a snappy-then-settle feel. Try `0.25, 0.1, 0.25, 1.0` for a smoother ease-out.
- For the UDP bridge, make sure the port in `LivelypngUDP.py` matches the one set in the OBS script panel.

---

## 📄 License

MIT — do whatever you want, credit appreciated 💙
