import tkinter as tk  # For the graphical interface
from tkinter.filedialog import *  # For the load/save dialog windows
from tkinter import messagebox  # For the window close event
import os  # For handling system processes
import socket  # For the SOCKET module for network connections
import threading  # For running background functions
from tkmacosx import Button  # To use mac-style buttons
import math as ma  # For the logarithm
from sys import exit  # To close the program
import time
import subprocess  # To prevent macOS from putting the app to sleep when minimized
import platform


from pathlib import Path  # To extract the file name from a file path

# For OSC
from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import BlockingOSCUDPServer

fader_length = 150  # Fader length
default_width = 5  # Label width
show = "NEW SHOW"  # Show name

# Colors
light_red = "#CD5C5C"
light_green = "#98FB98"
color_no_mod = "gray25"
color_mod = "DarkGoldenrod3"
color_mute = "gray50"
color_on = "DarkOrange2"
color_fondos = "gray40"

# Fonts
default_font = "Helvetica 12 bold"  # Default font
med_font = "Helvetica 12 bold"  # Medium-size font
small_font = "Helvetica 10 bold"  # Extra-small font

# Lists for the data
envios = []  # Create sends list
seq = []  # Create sequence
executor = []  # Create list for executors
listado_de_cues = []  # List of cues shown in the box

envio_actual = 0  # Selected send
cue_actual = 0  # Current cue
exec_actual = 0  # Current executor

autosend_global = False  # Indicates whether automatic send is enabled

temp_file_name = "temp_cues"
show_iniciado = 0  # To load the show once
caffeinate_proc = None  # Process to keep the app awake on macOS

# Desk network configuration
def_host = "192.168.0.128"  # Console default
# host ="172.18.3.10" # Test
# host ="192.168.137.1" # Test
# host = "127.0.0.1"  # Test
host = "172.18.3.10"  # Console default
port = 49280  # Port selected at startup
def_port = 49280  # Default port, must be 49280

# OSC network configuration
def_host_osc = "127.0.0.1"
host_osc = "127.0.0.1"
def_port_osc = 5005
port_osc = 5005


def show_inicial():
    """Load the show saved as a temporary file"""
    global show_iniciado

    try:
        fichero = open("backup.csv", "r")
        datos = fichero.read()
        fichero.close()
        monta_show(datos)
        print_cmd("Loaded last used values")
        show_iniciado = 1

    except Exception as e:
        print(e)
        print_cmd("No show could be loaded")
        show_iniciado = 1

    print_cmd("PERAMESA v3.0")


def show_name_update():
    """Update the label for the show name"""
    app.OpcionesNameShowCue.Show_entry.delete(0, 'end')
    app.OpcionesNameShowCue.Show_entry.insert(0, show)


def print_cmd(*cadena):
    """Check that the object has already been created and use its function"""
    if show_iniciado == 0:  # Here it only prints in the terminal
        print(*cadena)
    else:
        app.ventana_comando.print_cmd(*cadena)  # Here it prints in the command window


def borra_cmd():
    """Check that the object has already been created and use its function"""
    if show_iniciado == 0:
        pass
    else:
        app.ventana_comando.borra_cmd()


def evitar_app_nap():
    """Prevent macOS from pausing the app when minimized (App Nap)."""
    global caffeinate_proc

    if platform.system() != "Darwin":
        return

    if caffeinate_proc is not None and caffeinate_proc.poll() is None:
        # There is already an active caffeinate process
        return

    try:
        # Keeps the app "active" while this process is alive
        caffeinate_proc = subprocess.Popen(
            ["caffeinate", "-dimsu", "-w", str(os.getpid())]
        )
        print_cmd("App Nap disabled to keep listening and sending in the background")
    except FileNotFoundError:
        print_cmd(
            "'caffeinate' not found; if macOS pauses the app when minimized, disable App Nap manually"
        )


def clear_cue():
    """Clear all values of the current cue"""
    for j in range(0, 17):
        for i in range(0, 64):
            seq[0].cue_list[cue_actual].envio[j].canal[i].ch_value = 0
            seq[0].cue_list[cue_actual].envio[j].canal[i].ch_mute = "MUTE"
            seq[0].cue_list[cue_actual].envio[j].canal[i].ch_mod = False


def actualiza_executors():
    """Send all values of the current cue to the executors"""
    for i in range(0, 64):
        executor[i].carga_valores(
            seq[0].cue_list[cue_actual].envio[envio_actual].canal[i].ch_value,
            seq[0].cue_list[cue_actual].envio[envio_actual].canal[i].ch_mute,
            seq[0].cue_list[cue_actual].envio[envio_actual].canal[i].ch_mod)


def gotocue(cue_destino):
    """Jump to the indicated cue"""
    # Clear the command box
    global cue_actual
    cue_actual = cue_destino
    listado_de_cues[0].listado_upd()
    listado_de_cues[0].listado_cues.selection_set(cue_actual)
    actualiza_executors()
    print_cmd("Cue actual: ", cue_actual)
    print_cmd("Cue name: ", seq[0].cue_list[cue_actual].cue_name)
    app.OpcionesNameShowCue.Cue_entry.delete(0, 'end')
    app.OpcionesNameShowCue.Cue_entry.insert(0, seq[0].cue_list[cue_actual].cue_name)
    root.focus_set()  # Set focus on the main window

    # Check if auto send is enabled and send to the desk
    if autosend_global:
        app.OpcionExtraButtons.conectar_directo(0)
    else:
        pass


def crear_archivo(name):
    """Function to create a file"""
    fichero = open(name + ".csv", "w")  # Open temporary file in write mode

    # Write the title to the file
    fichero.write(show + "\n")

    # Write values to file
    for x in range(0, int(len(seq[0].cue_list))):  # Loop per line
        fichero.write(str(seq[0].cue_list[x].cue_name) + ";")  # Cue name
        for i in range(0, 17):
            for j in range(0, 64):  # Write channel values
                fichero.write(str(seq[0].cue_list[x].envio[i].canal[j].ch_value) + ";")
                fichero.write(str(seq[0].cue_list[x].envio[i].canal[j].ch_mute) + ";")
                fichero.write(str(seq[0].cue_list[x].envio[i].canal[j].ch_mod) + ";")
        fichero.write("\n")
    fichero.close()  # Close file

    print_cmd("Number of cues: " + str(len(seq[0].cue_list)))
    print_cmd("Saved file '" + str(name) + "'")  # Control


def autosave():
    """Save the show every so often"""
    crear_archivo(temp_file_name)
    root.after(60000 * 5, autosave)  # time in milliseconds


def on_closing():
    """Events when closing the program"""
    if messagebox.askokcancel("Quit", "Nene... Do you want to quit?"):
        crear_archivo("backup")  # Create temporary file
        root.destroy()
        exit()


def monta_show(datos):
    """Build the show"""
    global show
    global cue_actual

    i_cue = 0

    # Build the show with the data
    app.new_show()  # Clear the current show
    lineas = datos.splitlines()  # Split the data into lines
    show = lineas[0]  # Update show name
    show_name_update()  # Update show label

    linea = []  # Create a list to store the data

    for i in range(0, (len(lineas)) - 2):
        seq[0].cue_list.append(Cue())  # Create a new cue

    for i in range(1, len(lineas)):
        linea[:] = []  # Clear the list
        columna = 1  # Helper to count the column in the file

        linea = lineas[i].split(";")  # Split the current line into groups
        seq[0].cue_list[i_cue].cue_name = str(linea[0])

        #  Start loop to fill values in channels
        for j in range(0, 17):
            for k in range(0, 64):
                seq[0].cue_list[i_cue].envio[j].canal[k].ch_value = linea[columna]
                columna += 1
                seq[0].cue_list[i_cue].envio[j].canal[k].ch_mute = linea[columna]
                columna += 1
                # Convert text line to boolean values
                if linea[columna] == "True":
                    aux = True
                else:
                    aux = False

                seq[0].cue_list[i_cue].envio[j].canal[k].ch_mod = aux

                columna += 1
        i_cue += 1

    cue_actual = 0

    gotocue(cue_actual)
    borra_cmd()  # Clear the screen


def fader_rango(valor_original):
    """Convert 0-100 values to a logarithmic scale"""
    # old_value = float(x)
    # old_range = [0.0, 100.0]
    # new_range = [-32768.0, 1000.0]
    # percent = (old_value - old_range[0])/(old_range[1] - old_range[0])
    # resultado = ((new_range[1] - new_range[0]) * percent) + new_range[0]
    x = int(valor_original)

    resultado = ma.log(((x * 999) / 100) + 1, 1000) * 33768 - 32768  # Convert to logarithmic scale
    return int(resultado)


def osc_thread():
    """Start a thread for OSC"""
    if show_iniciado:
        # Open a parallel thread for listening
        hacer = threading.Thread(target=listen)
        hacer.daemon = True  # To end the thread when closing the application
        hacer.start()  # Start listening
    else:
        pass


def listen():
    """Listen"""
    dispatcher = Dispatcher()
    dispatcher.set_default_handler(default_handler)

    try:
        # Try to open the OSC server on host_osc:port_osc
        server = BlockingOSCUDPServer((host_osc, port_osc), dispatcher)
    except PermissionError as e:
        # Common permission/firewall/blocked-port error
        print_cmd(f"OSC ERROR: could not open {host_osc}:{port_osc}")
        print_cmd(f"OSC ERROR detail: {e}")
        return
    except OSError as e:
        # Other socket errors (invalid IP, port in use, etc.)
        print_cmd(f"OSC SOCKET ERROR at {host_osc}:{port_osc}: {e}")
        return

    try:
        print_cmd(f"OSC listening on {host_osc}:{port_osc}")
        server.serve_forever()  # Blocks forever
    except Exception as e:
        # In case the server crashes while listening
        print_cmd(f"OSC ERROR while listening: {e}")
        return

def default_handler(address, *args):
    """What the desk does with each OSC message"""
    print(f"Received: {address}: {args}")

    if address == "/go":
        borra_cmd()  # Clear the screen
        if args[0] == 0:
            if show_iniciado:
                app.OpcListButtons.prev_cue()
            else:
                pass
            print_cmd("OSC: GOBACK")
        else:
            if args[0] == 1:
                if show_iniciado:
                    app.OpcListButtons.next_cue()
                else:
                    pass
                print_cmd("OSC: GO")
            else:
                print_cmd("OSC: ** Invalid value for go ** ")
                pass

    else:
        if address == "/goto":
            borra_cmd()  # Clear the screen
            if show_iniciado:
                if int(args[0]) >= len(seq[0].cue_list):
                    print_cmd("CUE does not exist: ", args[0])
                else:
                    gotocue(args[0])

            print_cmd("OSC: GOTO CUE ", args[0])

        else:
            print_cmd("OSC: Received invalid message")


def send_values():
    """Send the values to the desk"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # sock.setblocking(0)
        sock.close()
    except:
        pass
    # Store the connection as a variable (to make it easier to use)
    try:
        # Open connection
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((host, port))
        sock.settimeout(5)
        print_cmd("Connected to " + str(host) + " on port " + str(port))
        print_cmd("Sending:")

        # Loop for the Master send
        for channel in range(0, 64):
            if seq[0].cue_list[cue_actual].envio[0].canal[channel].ch_mod:  # Check whether the value should be sent
                ch = channel
                thelevel = fader_rango(seq[0].cue_list[cue_actual].envio[0].canal[channel].ch_value)

                if seq[0].cue_list[cue_actual].envio[0].canal[channel].ch_mute == "ON":  # Turn on channel
                    string_fad_on = "set MIXER:Current/InCh/Fader/On {} 0 1\n".format(ch)
                    sock.sendall(string_fad_on.encode())
                else:
                    string_fad_off = "set MIXER:Current/InCh/Fader/On {} 0 0\n".format(ch)  # Mute channel
                    sock.sendall(string_fad_off.encode())


                # Send fader values
                string_level = "set MIXER:Current/InCh/Fader/Level {} 0 {}\n".format(ch, thelevel)  # Adjust channel
                sock.sendall(string_level.encode())
                print_cmd("MASTER Ch ", ch, seq[0].cue_list[cue_actual].envio[0].canal[channel].ch_mute, " at ",
                          thelevel)

            else:
                pass

        # Loop for the rest of the sends
        for send in range(1, 17):
            for channel in range(0, 64):
                if seq[0].cue_list[cue_actual].envio[send].canal[channel].ch_mod:  # Check whether it should be sent
                    ch = channel
                    thelevel = fader_rango(seq[0].cue_list[cue_actual].envio[send].canal[channel].ch_value)
                    thesend = send - 1

                    if seq[0].cue_list[cue_actual].envio[send].canal[channel].ch_mute == "ON":  # Turn on channel
                        string_fad_on = "set MIXER:Current/InCh/ToMix/On {} {} 1\n".format(ch, thesend)
                        sock.sendall(string_fad_on.encode())

                    else:
                        string_fad_off = "set MIXER:Current/InCh/ToMix/On {} {} 0\n".format(ch, thesend)  # Mute channel
                        sock.sendall(string_fad_off.encode())


                    # Send fader values
                    string_level = "set MIXER:Current/InCh/ToMix/Level {} {} {}\n".format(ch, thesend, thelevel)
                    sock.sendall(string_level.encode())
                    print_cmd("SEND ", send, "Ch ", ch, seq[0].cue_list[cue_actual].envio[send].canal[channel].ch_mute,
                              " at ", thelevel)


                else:
                    pass
        
        try:
            # Receive a message before closing the connection
            sock.recv(1500)
            for i in range(0,5):
                time.sleep(0.1)
        except:
            print_cmd("The console is not responding")
                


        # ALWAYS close the connection at the end of the script
        # sock.setblocking(0)
        sock.close()
        print_cmd("Connection closed")


    except ConnectionRefusedError as e:
        print(e)
        print_cmd("CONNECTION REFUSED")
        print_cmd("Could not establish a connection to the console")
        print_cmd("IP: " + str(host) + "   Port: " + str(port))

    except TimeoutError as e:
        print(e)
        print_cmd("CONNECTION TIMEOUT")
        print_cmd("Could not establish a connection to the console")
        print_cmd("IP: " + str(host) + "   Port: " + str(port))


class Channel:
    """Structure for channels storing value, mute, and modified state"""

    # Class constructor
    def __init__(self, ch_num, ch_value, ch_mute, ch_mod):
        self.ch_num = ch_num
        self.ch_value = ch_value
        self.ch_mute = ch_mute
        self.ch_mod = ch_mod

    def __str__(self):
        return '{} {} {} {}'.format(self.ch_num, self.ch_value, self.ch_mute, self.ch_mod)


class Send:
    """Structure for sends"""

    def __init__(self):
        canal = []
        self.canal = canal
        for i in range(0, 64):
            self.canal.append(Channel(i, 0, "MUTE", False))


class Cue:
    """Structure for each cue"""

    def __init__(self):
        cue_name = ''
        envio = []
        self.envio = envio
        self.cue_name = cue_name

        for i in range(0, 17):
            self.envio.append(Send())

    def mostrar_ch(self):
        print_cmd(self.envio[envio_actual].canal[exec_actual].ch_value)

    def rename(self, new_name):
        self.cue_name = new_name


class Seq:
    """Structure for the sequence"""

    def __init__(self):
        cue_list = []
        self.cue_list = cue_list

        self.cue_list.append(Cue())
        self.cue_list[0].rename("CUE 0")


class SendsButtons:
    """Create the send buttons"""

    def __init__(self, send_num, sends_frame):
        self.send_num = send_num
        self.send_name = ""
        self.sends_frame = sends_frame

        if self.send_num == 0:
            send_name = "MASTER"
        else:
            send_name = "SEND " + str(send_num)

        self.send_button = tk.Label(sends_frame,
                                  font=small_font,
                                  fg="WHITE",
                                  text=send_name,
                                  bg=self.send_color(send_num),
                                  #borderless=1,
                                  borderwidth=3,
                                  relief="raised",
                                  #overrelief='sunken',
                                  height=3,
                                  width=10,
                                  highlightbackground=color_fondos)
                                  #command=self.selec_send)

        self.send_button.grid(sticky="W", row=0, column=0 + send_num, padx=5, pady=5)
        self.send_button.bind('<Button-1>', lambda event: self.selec_send(event))

    def selec_send(self, event):
        """Select the send"""
        global envio_actual
        envios[envio_actual].send_button.config(bg=color_no_mod)
        # turn_off_send_button(self.send_num)
        envio_actual = self.send_num  # Update current send
        self.send_button.config(bg=color_mod)
        self.send_button.config(highlightbackground="WHITE")

        actualiza_executors()

        if envio_actual == 0:
            print_cmd("Master")
        else:
            print_cmd("Send " + str(envio_actual))

    @staticmethod
    def send_color(send_num):
        if send_num == envio_actual:
            color = color_mod
        else:
            color = color_no_mod
        return color


class Exec:
    """Create the executors, buttons, labels, and faders"""

    def __init__(self, exec_ch, exec_value, exec_mute, exec_mod, exec_x, exec_y, exec_frame):
        label = tk.Label()
        fader_label = tk.Label()
        mute = tk.Button()

        self.label = label
        self.mute = mute
        self.fader_label = fader_label
        self.exec_ch = exec_ch
        self.exec_value = exec_value
        self.exec_mute = exec_mute
        self.exec_mod = exec_mod

        self.exec_x = exec_x
        self.exec_y = exec_y
        self.exec_frame = exec_frame

        # ID label
        self.label = tk.Label(exec_frame,
                              font=default_font,
                              text="CH " + str(exec_ch + 1),
                              bg=color_fondos)
        self.label.grid(row=exec_y, column=exec_x)
        self.label.bind('<Double-Button-1>', lambda event: self.test(event))

        # Mute button
        self.mute = tk.Label(exec_frame,
                             font=default_font,
                             text=exec_mute,
                             bg=color_mute,
                             # highlightbackground=color_fondos,
                             fg="BLACK",
                             relief="ridge",
                             # borderless=1,
                             width=default_width)
        #                     command=self.toggle)  # Send the button number to toggle
        self.mute.grid(row=exec_y + 1, column=exec_x)
        self.mute.grid(sticky="nsew")
        self.mute.bind('<Button-1>', lambda event: self.toggle(event))

        # Fader
        self.fader = tk.Scale(exec_frame,
                              font=default_font,
                              bg=color_fondos,
                              bd=3,  # Inner border thickness
                              troughcolor="gray80",  # Background color
                              highlightcolor=color_fondos,
                              highlightbackground=color_fondos,
                              activebackground=color_mod,
                              showvalue=0,  # Do not show the value
                              from_=100,
                              to=0,
                              length=fader_length
                              )
        self.fader.config(command=self.actualiza_etiqueta_fader)
        self.fader.grid(row=exec_y + 2, column=exec_x)
        self.fader.set(self.exec_value)  # Initial value
        self.fader.bind("<ButtonRelease-1>", self.modifica_fader)

        # Label with the fader value. It also indicates if the channel is sent
        self.fader_label = tk.Label(exec_frame,
                                    font=default_font,
                                    text=self.actualiza_etiqueta_fader,
                                    bg=color_no_mod,  # Normal label color
                                    fg="BLACK",
                                    relief="ridge",
                                    width=default_width)
        self.fader_label.grid(row=exec_y + 3, column=exec_x)
        self.fader_label.bind('<Double-Button-1>',
                              lambda event: self.tog_enviar(event))  # Double click toggles sending

        # Blank space
        self.white = tk.Label(exec_frame,
                              text="",
                              bg=color_fondos)
        self.white.grid(row=exec_y + 4, column=exec_x)

    def actualiza_etiqueta_fader(self, event):
        """Update 0-100 values in dB"""
        # print(event)
        if self.fader.get() < 1:
            sdb = "- inf"  # "\u221E"
        else:
            db = int(fader_rango(self.fader.get()) * 0.01)
            if db > 0:
                sdb = ("+" + str(db))
            else:
                sdb = str(db)

        self.fader_label.config(text=sdb)

    def test(self, event):
        """Utility function to log the value of the pressed channel"""
        # print(event)
        print("Send: ", envio_actual, "Ch:", (self.exec_ch + 1), "At: ", self.exec_value, self.exec_mute, "Mod: ",
              self.exec_mod)
        print_cmd("TEST MESSAGE")

    def toggle(self, event):
        """Change the state of the MUTE button"""
        # print(event)
        self.fader_label.config(bg=color_mod)  # Update the value label (modified)
        self.exec_mod = True  # Update channel as modified
        seq[0].cue_list[cue_actual].envio[envio_actual].canal[self.exec_ch].ch_mod = True
        if self.exec_mute == "ON":
            self.exec_mute = "MUTE"
            self.mute.config(bg=color_mute)
            self.mute.config(highlightbackground="WHITE")
            self.mute.config(text="MUTE")
            seq[0].cue_list[cue_actual].envio[envio_actual].canal[self.exec_ch].ch_mute = "MUTE"
        else:
            self.exec_mute = "ON"
            self.mute.config(bg=color_on)
            self.mute.config(highlightbackground="WHITE")
            self.mute.config(text="ON")
            seq[0].cue_list[cue_actual].envio[envio_actual].canal[self.exec_ch].ch_mute = "ON"

    def modifica_fader(self, event):
        """Actions performed when modifying the fader"""
        # # print(event)
        self.exec_value = self.fader.get()  # Update executor variable
        print_cmd("Fader", (self.exec_ch + 1), "at", self.fader.get(), "%")  # Log the data
        # Update fader data
        seq[0].cue_list[cue_actual].envio[envio_actual].canal[self.exec_ch].ch_value = self.fader.get()
        # self.fader_label.config(text=self.fader.get())
        self.actualiza_etiqueta_fader(self)
        # Mark send as modified
        seq[0].cue_list[cue_actual].envio[envio_actual].canal[self.exec_ch].ch_mod = True
        self.exec_mod = True
        self.fader_label.config(bg=color_mod)

    def tog_enviar(self, event):
        """Toggle whether a channel is sent"""
        # print(event)
        if not self.exec_mod:
            self.exec_mod = True
            self.fader_label.config(bg=color_mod)
            print_cmd("Send values for the selected channel")
            seq[0].cue_list[cue_actual].envio[envio_actual].canal[self.exec_ch].ch_mod = True

        else:
            self.exec_mod = False
            self.fader_label.config(bg=color_no_mod)
            print_cmd("Do not send values for the selected channel")
            seq[0].cue_list[cue_actual].envio[envio_actual].canal[self.exec_ch].ch_mod = False

    def carga_valores(self, upd_value, upd_mute, upd_mod):
        self.exec_value = upd_value
        self.fader_label.config(text=self.actualiza_etiqueta_fader(self))  # Change label text

        # Update executor MUTE value
        self.exec_mute = upd_mute
        if self.exec_mute == "ON":
            self.mute.config(bg=color_on)
            self.mute.config(highlightbackground="WHITE")
            self.mute.config(text=self.exec_mute)

        else:
            self.mute.config(bg=color_mute)
            self.mute.config(highlightbackground="WHITE")
            self.mute.config(text=self.exec_mute)

        # Update fader modified property
        self.exec_mod = upd_mod
        if self.exec_mod:
            self.fader_label.config(bg=color_mod)
        else:
            self.fader_label.config(bg=color_no_mod)

        self.fader.set(upd_value)  # Load value into the executor


class OpcionesNameShowCue:
    """Structure for the show name options and the current cue"""

    def __init__(self, option_frame):
        self.option_frame = option_frame
        self.Show_label = tk.Label
        self.Show_entry = tk.Entry
        self.Cue_label = tk.Label
        self.Cue_entry = tk.Entry

        # COLUMN 1 #################################################################
        # Show label

        self.Show_label = tk.Label(self.option_frame,
                                   font=default_font,
                                   text="SHOW NAME:",
                                   bg=color_fondos,
                                   width=10)
        self.Show_label.grid(sticky="W", row=0, column=0, padx=8, pady=0)

        # Show name entry
        self.Show_entry = tk.Entry(self.option_frame,
                                   font=default_font,
                                   textvariable=show,
                                   bg=color_on,
                                   fg="BLACK",
                                   width=30)
        self.Show_entry.grid(sticky="W", row=0, column=1, padx=8, pady=0)
        self.Show_entry.insert(0, show)
        self.Show_entry.bind('<Return>', self.show_name)
        # self.Show_entry.bind('<Leave>', self.show_name)

        # Current cue label
        self.Cue_label = tk.Label(self.option_frame,
                                  font=default_font,
                                  text="CUE NAME:",
                                  fg="BLACK",
                                  bg=color_fondos,
                                  width=10)
        self.Cue_label.grid(sticky="W", row=1, column=0, padx=8, pady=0)

        # Cue name entry
        self.Cue_entry = tk.Entry(self.option_frame,
                                  font=default_font,
                                  textvariable=seq[0].cue_list[cue_actual].cue_name,
                                  bg=color_mod,
                                  fg="BLACK",
                                  width=30)
        self.Cue_entry.grid(sticky="W", row=1, column=1, padx=8, pady=0)
        self.Cue_entry.insert(0, seq[0].cue_list[cue_actual].cue_name)
        self.Cue_entry.bind('<Return>', self.cue_name)

    def show_name(self, event):
        """Update the show name after verifying it is a valid file name"""
        # print(event)
        global show

        safe_string = str()
        for c in self.Show_entry.get():
            if c.isalnum() or c in [' ', '.', '/']:
                safe_string = safe_string + c

        valid = safe_string == self.Show_entry.get()
        if not valid:
            print_cmd("Invalid name.")
        else:
            show = self.Show_entry.get()
            listado_de_cues[0].listado_cues.selection_set(cue_actual)

    def cue_name(self, event):
        """Update the cue name"""
        # print(event)
        seq[0].cue_list[cue_actual].cue_name = self.Cue_entry.get()
        listado_de_cues[0].listado_upd()
        listado_de_cues[0].listado_cues.selection_set(cue_actual)


class OpcConfigRed:
    """Structure for network selection options"""

    def __init__(self, option_frame):
        self.option_frame = option_frame
        global host
        global host_osc
        global port
        global port_osc

        # Network configuration label
        self.Label_desk = tk.Label(self.option_frame,
                                   font=default_font,
                                   text="NETWORK CONFIGURATION",
                                   fg="BLACK",
                                   bg=color_fondos,
                                   width=20)
        self.Label_desk.grid(row=2, column=0, padx=8, pady=0, columnspan=2, sticky='NSEW')

        # HOST label
        self.Label_host = tk.Label(self.option_frame,
                                   font=default_font,
                                   text="DESK HOST",
                                   fg="BLACK",
                                   bg=color_fondos,
                                   width=10)
        self.Label_host.grid(sticky="W", row=3, column=0, padx=8, pady=0)

        # HOST value entry
        self.Host_entry = tk.Entry(option_frame,
                                   font=default_font,
                                   textvariable=host,
                                   bg="#ccffff",
                                   fg="BLACK",
                                   width=30)
        self.Host_entry.grid(sticky="W", row=3, column=1, padx=8, pady=0)
        self.Host_entry.insert(0, host)
        self.Host_entry.config(state='disabled')
        self.Host_entry.bind('<Double-1>', self.host_enabled)
        self.Host_entry.bind('<Return>', self.host_number)
        # self.Host_entry.bind('<Leave>', self.host_number)

        # PORT label
        self.Label_port = tk.Label(self.option_frame,
                                   font=default_font,
                                   text="DESK PORT",
                                   fg="BLACK",
                                   bg=color_fondos,
                                   width=10)
        self.Label_port.grid(sticky="W", row=4, column=0, padx=8, pady=0)

        # PORT value entry
        self.Port_entry = tk.Entry(self.option_frame,
                                   font=default_font,
                                   textvariable=port,
                                   bg="#ccffff",
                                   fg="BLACK",
                                   width=30)
        self.Port_entry.grid(sticky="W", row=4, column=1, padx=8, pady=0)
        self.Port_entry.insert(0, port)
        self.Port_entry.config(state='disabled')
        self.Port_entry.bind('<Double-1>', self.port_enabled)
        self.Port_entry.bind('<Return>', self.port_number)
        # self.Port_entry.bind('<Leave>', self.port_number)

        # OSC HOST label
        self.Label_host_osc = tk.Label(self.option_frame,
                                       font=default_font,
                                       text="OSC HOST",
                                       fg="BLACK",
                                       bg=color_fondos,
                                       width=10)
        self.Label_host_osc.grid(sticky="W", row=5, column=0, padx=8, pady=0)

        # OSC HOST value entry
        self.host_osc = tk.StringVar(self.option_frame, host_osc)
        self.Host_osc_entry = tk.Entry(option_frame,
                                       font=default_font,
                                       textvariable=self.host_osc,
                                       bg="#ccffff",
                                       fg="BLACK",
                                       width=30)
        self.Host_osc_entry.grid(sticky="W", row=5, column=1, padx=8, pady=0)
        # self.Host_osc_entry.insert(0, self.host_osc)
        self.Host_osc_entry.config(state='disabled')
        self.Host_osc_entry.bind('<Double-1>', self.host_osc_enabled)
        self.Host_osc_entry.bind('<Return>', self.host_osc_number)
        # self.Host_osc_entry.bind('<Leave>', self.host_osc_number)

        # OSC PORT label
        self.Label_osc_port = tk.Label(self.option_frame,
                                       font=default_font,
                                       text="OSC PORT",
                                       fg="BLACK",
                                       bg=color_fondos,
                                       width=10)
        self.Label_osc_port.grid(sticky="W", row=6, column=0, padx=8, pady=0)

        # OSC PORT value entry
        self.port_osc = tk.StringVar(self.option_frame, port_osc)
        self.Port_osc_entry = tk.Entry(self.option_frame,
                                       font=default_font,
                                       textvariable=self.port_osc,
                                       bg="#ccffff",
                                       fg="BLACK",
                                       width=30)
        self.Port_osc_entry.grid(sticky="W", row=6, column=1, padx=8, pady=0)
        # self.Port_osc_entry.insert(0, self.port_osc)
        self.Port_osc_entry.config(state='disabled')
        self.Port_osc_entry.bind('<Double-1>', self.port_osc_enabled)
        self.Port_osc_entry.bind('<Return>', self.port_osc_number)
        # self.Port_osc_entry.bind('<Leave>', self.port_osc_number)

    def port_enabled(self, event):
        """Unlock the data entry"""
        # print(event)
        self.Port_entry.configure(state='normal')

    def port_number(self, event):
        """Update the PORT"""
        # print(event)

        global port
        if self.Port_entry.get() == "":
            port = def_port
        else:
            try:
                aux = self.Port_entry.get()
                port = int(aux)
            except Exception as e:
                print(e)
                port = def_port
                print_cmd("Invalid port, changed to default")
                print_cmd("Current port: " + str(port))

        # listado_de_cues[0].selection_set(cue_actual)

        self.Port_entry.delete(0, "end")  # Update text
        self.Port_entry.insert(0, port)
        self.Port_entry.configure(state='disabled')  # Lock label

        root.focus_set()

    def host_enabled(self, event):
        """Activate the host field"""
        # print(event)
        self.Host_entry.configure(state='normal')

    def host_number(self, event):
        """Update the HOST"""
        # print(event)
        global host
        if self.Host_entry.get() == "":
            host = def_host
        else:
            host = self.Host_entry.get()
        # lista_cues.selection_set(cue_actual)

        self.Host_entry.delete(0, "end")  # Update text
        self.Host_entry.insert(0, host)
        self.Host_entry.configure(state='disabled')  # Lock label

        root.focus_set()  # Restore focus

    def host_osc_enabled(self, event):
        """Unlock the data entry"""
        # print(event)
        self.Host_osc_entry.configure(state='normal')

    def host_osc_number(self, event):
        """Update the OSC HOST"""
        # print(event)
        global host_osc

        if self.Host_osc_entry.get() == "":
            host_osc = def_host_osc
        else:
            host_osc = self.Host_osc_entry.get()

        self.Host_osc_entry.delete(0, "end")  # Update text
        self.Host_osc_entry.insert(0, host_osc)
        self.Host_osc_entry.configure(state='disabled')  # Lock label

        root.focus_set()  # Restore focus

        # Retry starting the OSC server with the new configuration
        osc_thread()

    def port_osc_enabled(self, event):
        # print(event)
        self.Port_osc_entry.configure(state='normal')

    def port_osc_number(self, event):
        """Update the OSC PORT"""
        # print(event)
        global port_osc
        if self.Port_osc_entry.get() == "":
            port_osc = def_port_osc
        else:
            try:
                aux = self.Port_osc_entry.get()
                port_osc = int(aux)
            except Exception as e:
                print(e)
                port_osc = def_port_osc
                print_cmd("Invalid OSC port, changed to default")
                print_cmd("Current OSC port: " + str(port_osc))

        self.Port_osc_entry.delete(0, "end")  # Update text
        self.Port_osc_entry.insert(0, port_osc)
        self.Port_osc_entry.configure(state='disabled')  # Lock label

        root.focus_set()

        # Retry starting the OSC server with the new port
        osc_thread()

class OpcLlistaCues:
    """Display the list of cues on screen"""

    def __init__(self, option_frame):
        self.option_frame = option_frame

        # Scroll bar
        self.scrollbar = tk.Scrollbar(self.option_frame, orient="vertical")
        self.scrollbar.grid(sticky="NSEW", row=0, column=6, padx=0, pady=4, rowspan=8)

        self.listado_cues = tk.Listbox(self.option_frame,
                                       width=50,
                                       selectmode="SINGLE",
                                       activestyle="dotbox",
                                       yscrollcommand=self.scrollbar.set)

        self.listado_cues.grid(sticky="NSEW", row=0, column=2, padx=0, pady=4,
                               ipadx=5, ipady=5, rowspan=8, columnspan=2)

        self.listado_upd()
        self.listado_cues.selection_set(cue_actual)  # Default list selection
        self.listado_cues.bind('<ButtonRelease-1>', self.goto_lista)

        self.scrollbar.config(command=self.listado_cues.yview)

    def goto_lista(self, event):
        """Jump to the clicked cue"""
        # print(event)
        borra_cmd()  # Clear the screen
        gotocue(self.listado_cues.curselection()[0])  # Default list selection

    def listado_upd(self):
        """Update the items in the CUES list"""
        self.listado_cues.delete(0, "end")

        for x in range(0, len(seq[0].cue_list)):  # Create the list items
            #  listado_cues.insert("end", ("[ " + str(x) + " ]   " + label))
            self.listado_cues.insert("end", ("[ " + str(x) +
                                             " ]   " +
                                             seq[0].cue_list[x].cue_name))


class OpcListButtons:
    def __init__(self, option_frame):
        self.option_frame = option_frame
        self.prevcue_button = Button()
        self.nextcue_button = Button()
        self.moveup_button = Button()
        self.movedw_button = Button()
        self.newcue_button = Button()
        self.deletecue_button = Button()

        # Previous CUE button
        self.prevcue_button = Button(self.option_frame,
                                     font=med_font,
                                     fg="BLACK",
                                     text='<< PREV',
                                     bg=light_green,
                                     highlightbackground="WHITE",
                                     borderless=1,
                                     command=self.prev_cue)
        self.prevcue_button.grid(sticky="W", row=1, column=7, padx=8, pady=4)

        # Next CUE button
        self.nextcue_button = Button(self.option_frame,
                                     font=med_font,
                                     fg="BLACK",
                                     text='NEXT >>',
                                     bg=light_green,
                                     highlightbackground="WHITE",
                                     borderless=1,
                                     command=self.next_cue)
        self.nextcue_button.grid(sticky="W", row=2, column=7, padx=8, pady=4)

        # Move up button
        self.moveup_button = Button(self.option_frame,
                                    font=med_font,
                                    fg="BLACK",
                                    text='MOVE UP',
                                    bg="lavender",
                                    highlightbackground="WHITE",
                                    borderless=1,
                                    command=self.move_up)
        self.moveup_button.grid(sticky="W", row=3, column=7, padx=8, pady=4)

        # Move down button
        self.movedw_button = Button(self.option_frame,
                                    font=med_font,
                                    fg="BLACK",
                                    text='MOVE DW',
                                    bg="lavender",
                                    highlightbackground="WHITE",
                                    borderless=1,
                                    command=self.move_dw)
        self.movedw_button.grid(sticky="W", row=4, column=7, padx=8, pady=4)

        # New CUE button
        self.newcue_button = Button(self.option_frame,
                                    font=med_font,
                                    fg="BLACK",
                                    text='NEW',
                                    bg="lavender",
                                    highlightbackground="WHITE",
                                    borderless=1,
                                    command=self.new_cue)
        self.newcue_button.grid(sticky="W", row=5, column=7, padx=8, pady=4)

        # Delete CUE button
        self.deletecue_button = Button(option_frame,
                                       font=med_font,
                                       fg="BLACK",
                                       text='DELETE',
                                       bg=light_red,
                                       highlightbackground="WHITE",
                                       borderless=1)
        self.deletecue_button.grid(sticky="W", row=6, column=7, padx=8, pady=4)
        self.deletecue_button.bind('<Double-1>', self.delete_cue)

    @staticmethod
    def prev_cue():
        if not cue_actual:
            pass
        else:
            gotocue(cue_actual - 1)

    @staticmethod
    def next_cue():
        if cue_actual == (len(seq[0].cue_list) - 1):
            pass
        else:
            gotocue(cue_actual + 1)

    @staticmethod
    def move_up():
        """Move the current cue up"""

        global cue_actual

        if cue_actual != 0:
            seq[0].cue_list[cue_actual], seq[0].cue_list[cue_actual - 1] \
                = seq[0].cue_list[cue_actual - 1], seq[0].cue_list[cue_actual]
            cue_actual -= 1
            borra_cmd()  # Clear the screen
            gotocue(cue_actual)

        else:
            pass

    @staticmethod
    def move_dw():
        """Move the current cue down"""

        global cue_actual

        if cue_actual != len(seq[0].cue_list) - 1:
            seq[0].cue_list[cue_actual], seq[0].cue_list[cue_actual + 1] \
                = seq[0].cue_list[cue_actual + 1], seq[0].cue_list[cue_actual]
            cue_actual += 1
            borra_cmd()  # Clear the screen
            gotocue(cue_actual)

    @staticmethod
    def new_cue():
        """Create a new CUE"""
        global cue_actual
        seq[0].cue_list.append(Cue())
        cue_actual = ((len(seq[0].cue_list)) - 1)  # Move to the last CUE
        actualiza_executors()
        seq[0].cue_list[cue_actual].cue_name = ("CUE " + str(cue_actual))  # Add a generic cue name
        listado_de_cues[0].listado_upd()
        borra_cmd()  # Clear the screen
        gotocue(cue_actual)
        print_cmd("Created CUE", cue_actual)

    @staticmethod
    def delete_cue(event):
        """Delete the selected CUE"""
        # print(event)
        global cue_actual

        if len(seq[0].cue_list) != 1:
            del seq[0].cue_list[cue_actual]  # Delete the entire element from the sequence
            if cue_actual != 0:
                cue_actual -= 1
            else:
                pass

        else:  # CUE 0 cannot be deleted, it is only reset
            clear_cue()

        borra_cmd()  # Clear the screen
        print_cmd("CUE deleted")
        gotocue(cue_actual)  # Update the desk


class OpcionExtraButtons:
    def __init__(self, option_frame):
        self.option_frame = option_frame

        # Autosend
        self.autosend = tk.IntVar()
        self.a_send = tk.Checkbutton(self.option_frame,
                                     font=default_font,
                                     text="AUTOSEND",
                                     variable=self.autosend,
                                     onvalue=True,
                                     fg="BLACK",
                                     bg=color_fondos,
                                     offvalue=0)
        self.a_send.grid(sticky="W", row=0, column=8, padx=8, pady=4)
        self.a_send.bind('<Button-1>', self.check_color)

        # Button that sends values
        self.send_button = tk.Label(self.option_frame,
                                  font=med_font,
                                  text='SEND TO DESK',
                                  #command=self.conectar,
                                  bg=light_red,
                                  #borderless=1,
                                  highlightbackground="WHITE")
        self.send_button.grid(sticky="W", row=1, column=8, padx=8, pady=4)
        self.send_button.bind('<Button-1>', lambda event: self.conectar_directo(event))

        # SELECT ALL button
        self.selectall_button = Button(self.option_frame,
                                       font=med_font,
                                       fg="BLACK",
                                       text='SELECT',
                                       bg=color_mod,
                                       borderless=1,
                                       highlightbackground="WHITE",
                                       command=self.select_all)
        self.selectall_button.grid(sticky="W", row=2, column=8, padx=8, pady=4)

        # UNSELECT ALL button
        self.selectall_button = Button(self.option_frame,
                                       font=med_font,
                                       fg="BLACK",
                                       text='UNSELECT',
                                       bg=color_no_mod,
                                       borderless=1,
                                       highlightbackground="WHITE",
                                       command=self.unselect_all)
        self.selectall_button.grid(sticky="W", row=3, column=8, padx=8, pady=4)

        # CLEAR CUE button
        self.clearcue_button = Button(self.option_frame,
                                      font=med_font,
                                      fg="BLACK",
                                      text='CLEAR',
                                      bg="lavender",
                                      borderless=1,
                                      highlightbackground="WHITE",
                                      command=self.clear_cue_upd)
        self.clearcue_button.grid(sticky="W", row=4, column=8, padx=8, pady=4)

        # ON ALL button
        self.on_all_button = Button(self.option_frame,
                                    font=med_font,
                                    #                           width = 8,
                                    fg="BLACK",
                                    text='ON ALL',
                                    command=self.on_all,
                                    bg=color_on,
                                    borderless=1,
                                    highlightbackground="WHITE")
        self.on_all_button.grid(sticky="W", row=5, column=8, padx=8, pady=4)

        # MUTE ALL button
        self.mute_all_button = Button(self.option_frame,
                                      font=med_font,
                                      #                           width = 8,
                                      fg="BLACK",
                                      text='MUTE ALL',
                                      command=self.mute_all,
                                      bg=color_mute,
                                      borderless=1,
                                      highlightbackground="WHITE")
        self.mute_all_button.grid(sticky="W", row=6, column=8, padx=8, pady=4)

    def check_color(self, event):
        """Change the check color to show whether it is enabled"""
        # print(event)

        global autosend_global
        if (self.autosend.get()) == True:
            self.a_send.config(fg="BLACK")
            autosend_global = False
            print_cmd("*** Autosend DISABLED ***")
        else:
            self.a_send.config(fg="RED")
            print_cmd("*** Autosend ENABLED ***")
            autosend_global = True

    def conectar_directo(self, event):
        """Try to connect without a parallel thread"""
        send_values()

    def conectar(self, event):
        """Attempt to connect and send values to the desk using a parallel thread
        so the UI is not blocked while connecting"""
        self.send_button["state"] = "disabled"  # Change button state
        self.send_button.config(bg="grey",
                                highlightbackground="WHITE")

        # Open parallel thread
        self.task = threading.Thread(target=send_values)
        self.task.daemon = True  # End thread when closing the main application
        self.task.start()
        # Check periodically whether the thread has finished
        self.schedule_check(self.task)  # Check if the connection succeeded

    def schedule_check(self, task):
        """Schedule the execution of `check_if_done()` within one second."""
        root.after(1000, self.check_if_done, task)

    def check_if_done(self, task):
        """Check if the thread has finished and perform some actions"""
        # If the thread has finished, restore the button and show a message.
        if not task.is_alive():
            print_cmd("Connection finished")
            # Restore the button.
            self.send_button["state"] = "normal"
            self.send_button.config(bg=light_red,
                                    highlightbackground="WHITE")
        else:
            # Otherwise, check again soon.
            self.schedule_check(task)

    @staticmethod
    def select_all():
        """Mark all channels in the send to be sent"""
        for i in range(0, 64):
            seq[0].cue_list[cue_actual].envio[envio_actual].canal[
                i].ch_mod = True  # fader_label[i].config(bg=color_mod)
        actualiza_executors()
        print_cmd("All channels marked to send")

    @staticmethod
    def unselect_all():
        """Unmark all channels in the send"""
        for i in range(0, 64):
            seq[0].cue_list[cue_actual].envio[envio_actual].canal[i].ch_mod = False
        actualiza_executors()
        print_cmd("All channels unmarked for sending")

    @staticmethod
    def clear_cue_upd():
        """Set all values to 0 and update the executors"""
        clear_cue()
        actualiza_executors()

    @staticmethod
    def on_all():
        """Unmute all channels in the send"""
        for i in range(0, 64):
            seq[0].cue_list[cue_actual].envio[envio_actual].canal[i].ch_mute = "ON"
        actualiza_executors()
        print_cmd("All channels unmuted")

    @staticmethod
    def mute_all():
        """Mute all channels in the send"""
        for i in range(0, 64):
            seq[0].cue_list[cue_actual].envio[envio_actual].canal[i].ch_mute = "MUTE"
        actualiza_executors()
        print_cmd("All channels muted")


class OpcionesVentanaCmd:
    """Window to display commands"""

    def __init__(self, option_frame):

        self.option_frame = option_frame
        self.cmd = tk.Text(self.option_frame,
                           state='disabled',
                           width=40,
                           height=4,
                           font=med_font,
                           highlightbackground="WHITE",
                           fg="GREEN",
                           bg="BLACK")
        self.cmd.grid(sticky="nsew", row=0, column=9, padx=0, pady=4,
                      ipadx=5, ipady=5, rowspan=6, columnspan=2)

    def print_cmd(self, *input_string):
        """Print to the console and the Text widget"""
        if show_iniciado == 0:
            print(*input_string)
        else:
            print("CMD: ", *input_string)

            self.cmd.configure(state='normal')
            for argv in range(0, len(input_string)):
                s = str(*input_string[argv:argv + 1]) + " "
                self.cmd.insert("end", s)
            self.cmd.insert("end", "\n")
            self.cmd.yview(tk.END)
            self.cmd.configure(state='disabled')

    def borra_cmd(self):
        """Clear the screen"""
        self.cmd.configure(state='normal')
        self.cmd.delete(1.0, "end")
        self.cmd.configure(state='disabled')


class Mesa:
    """Main block of the program"""

    def __init__(self, root):
        super().__init__()
        """Initialize the desk"""
        # Create main window
        root.title("Peramesa v3.0")
        root.minsize(width=1330, height=820)  # Minimum main size
        root.configure(bg=color_fondos)

        # Try to set the icon
        icon_dir = Path(__file__).resolve().parent
        icon_set = False

        try:
            if platform.system() == "Darwin":
                icon_path = icon_dir / "pera.icns"
                root.wm_iconbitmap(default=str(icon_path))
                icon_set = True
            elif platform.system() == "Windows":
                icon_path = icon_dir / "peramesa_multi.ico"
                root.wm_iconbitmap(default=str(icon_path))
                icon_set = True
        except Exception as e:
            print(e)

        if not icon_set:
            try:
                img = tk.Image("photo", file=str(icon_dir / "peramesa.png"))
                root.iconphoto(True, img)  # you may also want to try this.
                root.tk.call('wm', 'iconphoto', root._w, img)
            except Exception as e:
                print(e)
                pass

        root.protocol("WM_DELETE_WINDOW", on_closing)  # When closing the program

        # Create the different frames
        self.inicializa()
        self.crear_ejecutores()
        self.crear_envios()
        self.crear_opciones()

        # Create the menu bar
        self.mainmenu = tk.Menu(root, tearoff=0, bg=color_fondos, fg="white")
        root.configure(menu=self.mainmenu)

        self.file_menu = tk.Menu(root, tearoff=0, bg=color_fondos, fg="white")
        self.mainmenu.add_cascade(label="File", menu=self.file_menu)
        self.file_menu.add_command(label="New show", command=self.new_show)
        self.file_menu.add_command(label="Load show", command=self.load_show)
        self.file_menu.add_command(label="Save show", command=self.save_show)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Help", command=self.help_window)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Exit", command=on_closing)

        self.file_menu.config(bg=color_fondos, activebackground="BLACK")

        # Autosave
        autosave()

    # File functions

    @staticmethod
    def new_show():
        """Create a new file"""
        global cue_actual
        global show

        crear_archivo(temp_file_name)  # Create backup
        cue_actual = 0  # Move to the first CUE and clear it
        clear_cue()

        if len(seq[0].cue_list) != 1:  # Check there is more than one element
            for x in range(1, len(seq[0].cue_list)):  # Delete all cues except 0
                del seq[0].cue_list[1]
        else:
            pass

        show = "NEW SHOW"
        show_name_update()
        borra_cmd()  # Clear the screen
        gotocue(cue_actual)  # Update faders

    @staticmethod
    def load_show():
        """Function to load a show"""
        try:
            files = [('CSV', '*.csv'),
                     ('Text Document', '*.txt')]
            ruta = askopenfilename(filetypes=files, defaultextension=files)
            fichero = open(ruta, 'r')
            datos = fichero.read()
            fichero.close()
            if datos == '':
                print_cmd("Invalid file")
            else:
                monta_show(datos)

        except AttributeError as e:
            print(e)
            print_cmd("Canceled before loading")

    @staticmethod
    def save_show():
        """Function to save the show"""
        global show

        try:
            files = [('CSV', '*.csv'),
                     ('Text Document', '*.txt')]
            ruta = asksaveasfilename(filetypes=files, defaultextension=files)
            ruta_completa = Path(ruta)

            # Update show name
            show = str(Path(ruta).stem)  # Retrieve the name
            show_name_update()

            ruta_sin_extension = str(ruta_completa.with_suffix(''))
            crear_archivo(ruta_sin_extension)

        except Exception as e:
            print(e)
            print_cmd("Canceled before saving")

    @staticmethod
    def help_window():
        """Create help window"""
        help_w = tk.Toplevel(root)  # Create window
        help_w.geometry('800x800')
        help_w.resizable(width=0, height=0)
        help_w.title("Help Peramesa v3.0")

        help_file_map = {
            "English": Path(__file__).with_name("help_text_en.txt"),
            "Spanish": Path(__file__).with_name("help_text.txt"),
        }

        control_frame = tk.Frame(help_w)
        control_frame.pack(fill=tk.X, padx=10, pady=5)

        tk.Label(control_frame, text="Language:").pack(side=tk.LEFT)

        selected_language = tk.StringVar(value="English")

        def load_help_text(*_):
            help_path = help_file_map.get(selected_language.get())
            if help_path is None:
                return

            long_text = help_path.read_text(encoding="utf-8")
            help_text.configure(state=tk.NORMAL)
            help_text.delete("1.0", tk.END)
            help_text.insert(tk.END, long_text)
            help_text.configure(state=tk.NORMAL)

        tk.OptionMenu(control_frame,
                      selected_language,
                      "English",
                      "Spanish",
                      command=load_help_text).pack(side=tk.LEFT, padx=5)

        h_scroll = tk.Scrollbar(help_w)  # Create scrollbar
        h_scroll.pack(side=tk.RIGHT,
                      fill=tk.Y)  # Place scroll on the right
        help_text = tk.Text(help_w,
                            wrap=tk.NONE,
                            yscrollcommand=h_scroll.set)  # Text widget
        help_text.pack(fill=tk.BOTH,
                       expand=tk.YES,
                       side=tk.LEFT)

        load_help_text()
        h_scroll.config(command=help_text.yview)
        tk.mainloop()

    # Create the program blocks

    @staticmethod
    def inicializa():
        """Initialize desk values"""
        seq.append(Seq())

    @staticmethod
    def crear_ejecutores():
        """Create the frame with the executors"""
        # Frame with executors
        exec_frame = tk.Frame(root)
        exec_frame.configure(bg=color_fondos)
        exec_frame.grid(row=1, column=0, padx=5, pady=5)

        # Loop to create the executors
        for i in range(0, 64):
            # Grid positions
            if i < 32:
                posicion_x = i
                posicion_y = 6
            else:
                posicion_y = 1
                posicion_x = i - 32

            # Create the executors
            executor.append(Exec(i,
                                 seq[0].cue_list[0].envio[envio_actual].canal[i].ch_value,
                                 seq[0].cue_list[0].envio[envio_actual].canal[i].ch_mute,
                                 False, posicion_x, posicion_y, exec_frame))

    @staticmethod
    def crear_envios():
        """Section for the send buttons"""
        sends_frame = tk.Frame(root)
        sends_frame.configure(bg=color_fondos)
        sends_frame.grid(sticky="W", row=0, column=0, padx=5, pady=5)

        for i in range(0, 17):  # For the 16 sends and the Master
            envios.append(SendsButtons(i, sends_frame))

    def crear_opciones(self):
        option_frame = tk.Frame(root)  # Create the frame for options
        option_frame.config(bg=color_fondos)  # Frame background color
        option_frame.grid(sticky="W", row=2, column=0, padx=5, pady=5)

        self.OpcionesNameShowCue = OpcionesNameShowCue(option_frame)  # Buttons to change show and cue names
        self.OpcConfigRed = OpcConfigRed(option_frame)  # Buttons to change the send network
        listado_de_cues.append(OpcLlistaCues(option_frame))  # Create the list of CUES

        self.OpcListButtons = OpcListButtons(option_frame)  # Create buttons to move through the list
        self.OpcionExtraButtons = OpcionExtraButtons(option_frame)  # Create buttons with extra functions
        self.ventana_comando = OpcionesVentanaCmd(option_frame)  # Create command window


if __name__ == '__main__':
    root = tk.Tk()
    app = Mesa(root)

    evitar_app_nap()

    # Try to load the last used show
    if show_iniciado == 0:
        show_inicial()

    osc_thread()
    root.mainloop()
