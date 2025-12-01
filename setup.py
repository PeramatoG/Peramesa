"""
setup.py para construir Peramesa en macOS con py2app.

Uso:
    python setup.py py2app
"""

from setuptools import setup

APP = ["Peramesa.py"]

DATA_FILES = [
    "pera.icns",
    "peramesa.png",
    "help_text.txt",
    "help_text_en.txt",
]

OPTIONS = {
    # Icono de la app
    "iconfile": "pera.icns",

    # Comportamiento estándar de apps Mac al abrir archivos desde Finder
    "argv_emulation": True,

    # Nos aseguramos de que Tkinter y sus submódulos se incluyan
    "includes": [
        "tkinter",
        "tkinter.ttk",
        "tkinter.filedialog",
        "tkinter.messagebox",
    ],

    # Pedimos explícitamente los frameworks de Tcl/Tk para evitar el error de init.tcl
    # (ruta típica cuando usas el Python oficial de python.org)
    "frameworks": [
        "/Library/Frameworks/Tcl.framework",
        "/Library/Frameworks/Tk.framework",
    ],

    # Un poco de metadatos de bundle (no obligatorio, pero viene bien)
    "plist": {
        "CFBundleName": "Peramesa",
        "CFBundleDisplayName": "Peramesa",
        "CFBundleIdentifier": "com.luismaperamato.peramesa",
        "CFBundleShortVersionString": "3.0.0",
        "CFBundleVersion": "3.0.0",
    },
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={"py2app": OPTIONS},
    setup_requires=["py2app"],
)
