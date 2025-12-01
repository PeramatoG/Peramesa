from setuptools import setup

APP = ["Peramesa.py"]
DATA_FILES = ["help_text.txt", "help_text_en.txt"]

OPTIONS = {
    "argv_emulation": False,
    "includes": [
        "tkinter",
        "tkinter.filedialog",
        "tkinter.messagebox",
    ],
    "packages": [
        "pythonosc",
        "tkmacosx",
    ],
    "iconfile": "pera.icns",
    "plist": {
        "CFBundleName": "Peramesa",
        "CFBundleDisplayName": "Peramesa",
        "CFBundleIdentifier": "com.luismaperamato.peramesa",
        "CFBundleShortVersionString": "3.0.0",
        "CFBundleVersion": "3.0.0",
        "NSHighResolutionCapable": True,
    },
}

setup(
    app=APP,
    name="Peramesa",
    data_files=DATA_FILES,
    options={"py2app": OPTIONS},
    setup_requires=["py2app"],
)
