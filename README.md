# Peramesa

Peramesa is a cue-based control tool for digital audio mixers.  
It allows you to store, edit and send fader levels and mute states for multiple channels and sends, organized in cues, and trigger them manually or via OSC.

> NOTE: This project is currently focused on the original author's workflow and mixer setup.  
> Use it at your own risk and always test with your own console before a show.

---

## Features

- Cue-based structure:
  - Sequence → Cues → Sends (Master + 16 sends) → 64 channels.
- Per-channel:
  - Fader value (0–100)
  - Mute state (ON / MUTE)
  - “Modified” flag to decide what gets actually sent to the mixer.
- TCP connection to the mixer:
  - Sends commands to update channel faders and send levels/mutes.
- OSC control:
  - Receives OSC messages (e.g. from QLab) to:
    - `/go` – go to next/previous cue
    - `/goto` – jump to a specific cue
- CSV-based show files (save/load).
- Auto-backup support (`backup.csv`, `temp_cues.csv`).

---

## Requirements

- Python **3.14** (tested with 3.14 on macOS and Windows).
- Dependencies (installed via `requirements.txt`), including for example:
  - `python-osc`
  - `tkmacosx` (for macOS UI look; falls back to standard Tk buttons on Windows)

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/PeramatoG/Peramesa.git
cd Peramesa
```

### 2. Create and activate a virtual environment

**On macOS:**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

**On Windows (CMD):**

```bat
python -m venv .venv
.\.venv\Scriptsctivate
```

### 3. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 4. Run Peramesa

```bash
python Peramesa.py
```

---

## Configuration

### Mixer connection

- **Host**: IP address of your digital mixer.  
- **Port**: TCP port used by the mixer’s remote control protocol.

These values can be edited directly in the GUI.

### OSC

Peramesa can listen for OSC messages to control cues.  

- **OSC Host**: usually `127.0.0.1` for local control, or the IP of the machine running Peramesa.
- **OSC Port**: default may vary; you can set any free UDP port (e.g. `9000`).

After changing OSC host or port in the GUI, Peramesa will try to restart the OSC server with the new values.  
If the port is blocked or not allowed by the system, an error will be shown in the command/log window.

---

## Notes

- This project was originally written in Spanish; some in-app texts and comments may still be in Spanish.
- The goal for future versions is to:
  - Improve documentation,
  - Separate help text into external files,
  - And optionally support both Spanish and English in the application.

---

## License

This project is licensed under the MIT License – see the [`LICENSE`](LICENSE) file for details.
