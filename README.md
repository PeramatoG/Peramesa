# Peramesa

Peramesa is a Tk-based cue control tool for Yamaha digital mixers that speak the TF-style remote control protocol (default TCP port 49280). It lets you store, edit and send fader levels and mute states for multiple channels and sends, organized in cues, and trigger them manually or via OSC.

> NOTE: This project is currently focused on the original author's workflow and mixer setup.
> Use it at your own risk and always test with your own console before a show.

---

## Features

- Cue-based structure:
  - Sequence → Cues → Sends (Master + 16 sends) → 64 channels.
- Per-channel controls:
  - Fader value (0–100)
  - Mute state (ON / MUTE)
  - “Modified” flag to decide what gets actually sent to the mixer.
- TCP connection to the mixer:
  - Sends commands to update channel faders and send levels/mutes.
- OSC control (default host `127.0.0.1`, port `5005`):
  - `/go 0` – go to the previous cue
  - `/go 1` – go to the next cue
  - `/goto <n>` – jump to cue `<n>`
- CSV-based show files (save/load) with automatic backup:
  - Loads `backup.csv` on startup when available.
  - Autosaves to `temp_cues.csv` every 5 minutes to preserve the current show.
- macOS-specific safeguard to keep the app awake via `caffeinate` while minimized.

---

## Requirements

- Python **3.10+** (tested with CPython 3.10/3.11).
- Dependencies installed via `requirements.txt`:
  - `python-osc`
  - `tkmacosx` (only needed on macOS; standard Tk buttons are used elsewhere)

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
.\.venv\Scripts\activate
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

- **Host**: IP address of your digital mixer. The app falls back to the default value if the field is left empty (default `192.168.0.128`).
- **Port**: TCP port used by the mixer’s remote control protocol. Empty or invalid values revert to the default (`49280`).

These values can be edited directly in the GUI by double-clicking the field labels. Peramesa is tuned for Yamaha mixers that follow this protocol and is not intended as a generic control surface for other brands.

### OSC

Peramesa can listen for OSC messages to control cues.

- **OSC Host**: usually `127.0.0.1` for local control, or the IP of the machine running Peramesa. Leaving the field blank restores the default value.
- **OSC Port**: defaults to `5005`. Invalid or empty entries fall back to that value.

After changing OSC host or port in the GUI (double-click to unlock, press Enter to apply), Peramesa restarts the OSC server with the new values. If the port is blocked or not allowed by the system, an error is shown in the command/log window.

---

## Notes

- File management options are available from the **File** menu: **New show**, **Load show**, **Save show**, **Help**, **About**, and **Exit**.

---

## License

This project is licensed under the MIT License – see the [`LICENSE`](LICENSE) file for details.
