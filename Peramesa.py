import tkinter as tk  # Para la interfaz gráfica
from tkinter.filedialog import *  # Para los cuadros de dialogo de cargar y grabar
from tkinter import messagebox  # Para el evento cerrar ventana
import socket  # Para el modulo SOCKET de conexion red
import threading  # Para realizar funciones en segundo plano
from tkmacosx import Button  # Para utiliza botonis tipo mac
import math as ma  # Para el logaritmo
from sys import exit  # Para cerrar el programa
import time


from pathlib import Path  # Para extrar el nombre de archivo de una ruta de archivo

# Para el OSC
from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import BlockingOSCUDPServer

fader_length = 150  # Longitud de los faders
default_width = 5  # Anchura de las etiquetas
show = "NEW SHOW"  # Nombre del show

# Colores
light_red = "#CD5C5C"
light_green = "#98FB98"
color_no_mod = "gray25"
color_mod = "DarkGoldenrod3"
color_mute = "gray50"
color_on = "DarkOrange2"
color_fondos = "gray40"

# Fuentes
default_font = "Helvetica 12 bold"  # Fuente por defecto
med_font = "Helvetica 12 bold"  # Fuente tamaño medio
small_font = "Helvetica 10 bold"  # Fuente chiquitica

# Listas para los datos
envios = []  # Crea lista de envios
seq = []  # Crea secuencia
executor = []  # Crea lista para ejecutores
listado_de_cues = []  # Listado de cues que se muestra en el box

envio_actual = 0  # Envio seleccionado
cue_actual = 0  # Cue actual
exec_actual = 0  # Ejecutor actual

autosend_global = False  # Indica si está activado el envio automático

temp_file_name = "temp_cues"
show_iniciado = 0  # Para cargar el show una vez

# Configuracion red mesa de sonido
def_host = "192.168.0.128"  # Original de la mesa
# host ="172.18.3.10" # De prueba
# host ="192.168.137.1" # De prueba
# host = "127.0.0.1"  # De prueba
host = "172.18.3.10"  # Original de la mesa
port = 49280  # Puerto seleccionado al iniciar
def_port = 49280  # Puerto por defecto, debe ser 49280

# Configuracion red OSC
def_host_osc = "127.0.0.1"
host_osc = "127.0.0.1"
def_port_osc = 5005
port_osc = 5005


def show_inicial():
    """Monta el show grabado como temporal"""
    global show_iniciado

    try:
        fichero = open("backup.csv", "r")
        datos = fichero.read()
        fichero.close()
        monta_show(datos)
        print_cmd("Cargados ultimos valores utilizados")
        show_iniciado = 1

    except Exception as e:
        print(e)
        print_cmd("No se ha podido cargar ningun show")
        show_iniciado = 1

    print_cmd("PERAMESA v3.0")


def show_name_update():
    """ Actualiza la etiqueta para el nombre del show """
    app.OpcionesNameShowCue.Show_entry.delete(0, 'end')
    app.OpcionesNameShowCue.Show_entry.insert(0, show)


def print_cmd(*cadena):
    """ Comprueba que se ha creado ya el objeto y utiliza su función """
    if show_iniciado == 0:  # Aqui solo imprimime en la terminal
        print(*cadena)
    else:
        app.ventana_comando.print_cmd(*cadena)  # Aqui imprime en la ventan de comandos


def borra_cmd():
    """ Comprueba que se ha creado ya el objeto y utiliza su función """
    if show_iniciado == 0:
        pass
    else:
        app.ventana_comando.borra_cmd()


def clear_cue():
    """ Limpia todos los valores de la cue actual """
    for j in range(0, 17):
        for i in range(0, 64):
            seq[0].cue_list[cue_actual].envio[j].canal[i].ch_value = 0
            seq[0].cue_list[cue_actual].envio[j].canal[i].ch_mute = "MUTE"
            seq[0].cue_list[cue_actual].envio[j].canal[i].ch_mod = False


def actualiza_executors():
    """ Envia todos los valores de la cue actual a los ejecutores """
    for i in range(0, 64):
        executor[i].carga_valores(
            seq[0].cue_list[cue_actual].envio[envio_actual].canal[i].ch_value,
            seq[0].cue_list[cue_actual].envio[envio_actual].canal[i].ch_mute,
            seq[0].cue_list[cue_actual].envio[envio_actual].canal[i].ch_mod)


def gotocue(cue_destino):
    """ Salta a la cue indicada """
    # Limpia cuadro de comandos
    global cue_actual
    cue_actual = cue_destino
    listado_de_cues[0].listado_upd()
    listado_de_cues[0].listado_cues.selection_set(cue_actual)
    actualiza_executors()
    print_cmd("Cue actual: ", cue_actual)
    print_cmd("Cue name: ", seq[0].cue_list[cue_actual].cue_name)
    app.OpcionesNameShowCue.Cue_entry.delete(0, 'end')
    app.OpcionesNameShowCue.Cue_entry.insert(0, seq[0].cue_list[cue_actual].cue_name)
    root.focus_set()  # Selecciona focus en la ventana principal

    # Comprueba si esta activado auto send y envía a la mesa
    if autosend_global:
        app.OpcionExtraButtons.conectar_directo(0)
    else:
        pass


def crear_archivo(name):
    """ Función para crear archivo"""
    fichero = open(name + ".csv", "w")  # Abrir fichero temporal modo escritura

    # imprime a archivo el título
    fichero.write(show + "\n")

    # imprime valores a archivo
    for x in range(0, int(len(seq[0].cue_list))):  # loop por línea
        fichero.write(str(seq[0].cue_list[x].cue_name) + ";")  # Nombre CUE
        for i in range(0, 17):
            for j in range(0, 64):  # imprime valores del canal
                fichero.write(str(seq[0].cue_list[x].envio[i].canal[j].ch_value) + ";")
                fichero.write(str(seq[0].cue_list[x].envio[i].canal[j].ch_mute) + ";")
                fichero.write(str(seq[0].cue_list[x].envio[i].canal[j].ch_mod) + ";")
        fichero.write("\n")
    fichero.close()  # Cerrar fichero

    print_cmd("Numero de cues: " + str(len(seq[0].cue_list)))
    print_cmd("Guardado archivo '" + str(name) + "'")  # Control #


def autosave():
    """ Graba el show cada cierto tiempo """
    crear_archivo(temp_file_name)
    root.after(60000 * 5, autosave)  # tiempo en milisegundos


def on_closing():
    """ Eventos al cerrar el programa """
    if messagebox.askokcancel("Quit", "Nene... Do you want to quit?"):
        crear_archivo("backup")  # Crea archivo temporal
        root.destroy()
        exit()


def monta_show(datos):
    """ Monta el show"""
    global show
    global cue_actual

    i_cue = 0

    # Montamos el show con los datos
    app.new_show()  # Borra el show actual
    lineas = datos.splitlines()  # Partimos los datos en lineas
    show = lineas[0]  # Actualiza nombre del show
    show_name_update()  # Actualiza etiqueta show

    linea = []  # Creamos una lista para guardar los datos

    for i in range(0, (len(lineas)) - 2):
        seq[0].cue_list.append(Cue())  # Crea una nueva cue

    for i in range(1, len(lineas)):
        linea[:] = []  # Borra la lista
        columna = 1  # Auxiliar para contar la columna del archivo

        linea = lineas[i].split(";")  # Corta la linea actual en grupos
        seq[0].cue_list[i_cue].cue_name = str(linea[0])

        #  Comenzamos loop para rellenar valores en canales
        for j in range(0, 17):
            for k in range(0, 64):
                seq[0].cue_list[i_cue].envio[j].canal[k].ch_value = linea[columna]
                columna += 1
                seq[0].cue_list[i_cue].envio[j].canal[k].ch_mute = linea[columna]
                columna += 1
                # Pasamos linea de texto a valores booleanos
                if linea[columna] == "True":
                    aux = True
                else:
                    aux = False

                seq[0].cue_list[i_cue].envio[j].canal[k].ch_mod = aux

                columna += 1
        i_cue += 1

    cue_actual = 0

    gotocue(cue_actual)
    borra_cmd()  # Limpia la pantalla


def fader_rango(valor_original):
    """ Convierte los valores 0-100 a escala logaritmica"""
    # old_value = float(x)
    # old_range = [0.0, 100.0]
    # new_range = [-32768.0, 1000.0]
    # percent = (old_value - old_range[0])/(old_range[1] - old_range[0])
    # resultado = ((new_range[1] - new_range[0]) * percent) + new_range[0]
    x = int(valor_original)

    resultado = ma.log(((x * 999) / 100) + 1, 1000) * 33768 - 32768  # Convierte a escala logaritmica
    return int(resultado)


def osc_thread():
    """ Comienza hilo para el OSC """
    if show_iniciado:
        # Abrimos hilo paralelo para la escucha
        hacer = threading.Thread(target=listen)
        hacer.daemon = True  # Para finalizar el hilo al cerrar la aplicación
        hacer.start()  # Comienza a escuchar
    else:
        pass


def listen():
    """ Escucha """
    dispatcher = Dispatcher()
    dispatcher.set_default_handler(default_handler)

    try:
        # Intentar abrir el servidor OSC en host_osc:port_osc
        server = BlockingOSCUDPServer((host_osc, port_osc), dispatcher)
    except PermissionError as e:
        # Error típico de permisos / firewall / puerto prohibido
        print_cmd(f"OSC ERROR: no se ha podido abrir {host_osc}:{port_osc}")
        print_cmd(f"OSC ERROR detalle: {e}")
        return
    except OSError as e:
        # Otros errores de socket (IP no válida, puerto en uso, etc.)
        print_cmd(f"OSC ERROR de socket en {host_osc}:{port_osc}: {e}")
        return

    try:
        print_cmd(f"OSC escuchando en {host_osc}:{port_osc}")
        server.serve_forever()  # Blocks forever
    except Exception as e:
        # Por si el servidor peta mientras está escuchando
        print_cmd(f"OSC ERROR durante la escucha: {e}")
        return

def default_handler(address, *args):
    """ Lo que hace la mesa con cada  mensaje OSC """
    print(f"Recibido: {address}: {args}")

    if address == "/go":
        borra_cmd()  # Limpia la pantalla
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
                print_cmd("OSC: ** Valor no valido para go ** ")
                pass

    else:
        if address == "/goto":
            borra_cmd()  # Limpia la pantalla
            if show_iniciado:
                if int(args[0]) >= len(seq[0].cue_list):
                    print_cmd("No existe la CUE: ", args[0])
                else:
                    gotocue(args[0])

            print_cmd("OSC: GOTO CUE ", args[0])

        else:
            print_cmd("OSC: Recibido mensaje no valido")


def send_values():
    """ Envia los valores a la mesa """
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # sock.setblocking(0)
        sock.close()
    except:
        pass
    # La conexion como una variable (Para facilitar su uso)
    try:
        # Abrimos conexión
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((host, port))
        sock.settimeout(5)
        print_cmd("Conectado a " + str(host) + " en el puerto " + str(port))
        print_cmd("Enviando:")

        # Loop para el Master
        for channel in range(0, 64):
            if seq[0].cue_list[cue_actual].envio[0].canal[channel].ch_mod:  # Comprueba si hay que enviar el valor
                ch = channel
                thelevel = fader_rango(seq[0].cue_list[cue_actual].envio[0].canal[channel].ch_value)

                if seq[0].cue_list[cue_actual].envio[0].canal[channel].ch_mute == "ON":  # Enciende canal
                    string_fad_on = "set MIXER:Current/InCh/Fader/On {} 0 1\n".format(ch)
                    sock.sendall(string_fad_on.encode())
                else:
                    string_fad_off = "set MIXER:Current/InCh/Fader/On {} 0 0\n".format(ch)  # Mutea canal
                    sock.sendall(string_fad_off.encode())


                # Envia valores fader
                string_level = "set MIXER:Current/InCh/Fader/Level {} 0 {}\n".format(ch, thelevel)  # Ajusta canal
                sock.sendall(string_level.encode())
                print_cmd("MASTER Ch ", ch, seq[0].cue_list[cue_actual].envio[0].canal[channel].ch_mute, " at ",
                          thelevel)

            else:
                pass

        # Loop para el resto de los envios
        for send in range(1, 17):
            for channel in range(0, 64):
                if seq[0].cue_list[cue_actual].envio[send].canal[channel].ch_mod:  # Comprueba si hay que enviar
                    ch = channel
                    thelevel = fader_rango(seq[0].cue_list[cue_actual].envio[send].canal[channel].ch_value)
                    thesend = send - 1

                    if seq[0].cue_list[cue_actual].envio[send].canal[channel].ch_mute == "ON":  # Enciende canal
                        string_fad_on = "set MIXER:Current/InCh/ToMix/On {} {} 1\n".format(ch, thesend)
                        sock.sendall(string_fad_on.encode())

                    else:
                        string_fad_off = "set MIXER:Current/InCh/ToMix/On {} {} 0\n".format(ch, thesend)  # Mutea canal
                        sock.sendall(string_fad_off.encode())


                    # Envia valores fader
                    string_level = "set MIXER:Current/InCh/ToMix/Level {} {} {}\n".format(ch, thesend, thelevel)
                    sock.sendall(string_level.encode())
                    print_cmd("SEND ", send, "Ch ", ch, seq[0].cue_list[cue_actual].envio[send].canal[channel].ch_mute,
                              " at ", thelevel)


                else:
                    pass
        
        try:
            # Recibe un mensaje antes de cerrar la conexion
            sock.recv(1500)
            for i in range(0,5):
                time.sleep(0.1)
        except:
            print_cmd("La mesa no responde")
                


        # Cerrar SIEMPRE la conexion al final del Script
        # sock.setblocking(0)
        sock.close()
        print_cmd("Conexión cerrada")


    except ConnectionRefusedError as e:
        print(e)
        print_cmd("CONEXION DENEGADA")
        print_cmd("No se ha podido establecer conexión con la mesa")
        print_cmd("IP: " + str(host) + "   Puerto: " + str(port))

    except TimeoutError as e:
        print(e)
        print_cmd("TIEMPO PARA CONEXIÓN AGOTADO")
        print_cmd("No se ha podido establecer conexión con la mesa")
        print_cmd("IP: " + str(host) + "   Puerto: " + str(port))


class Channel:
    """ Estructura para los canales donde se guarda valor, mute y modificado """

    # Constructor de clase
    def __init__(self, ch_num, ch_value, ch_mute, ch_mod):
        self.ch_num = ch_num
        self.ch_value = ch_value
        self.ch_mute = ch_mute
        self.ch_mod = ch_mod

    def __str__(self):
        return '{} {} {} {}'.format(self.ch_num, self.ch_value, self.ch_mute, self.ch_mod)


class Send:
    """ Estructura para envios """

    def __init__(self):
        canal = []
        self.canal = canal
        for i in range(0, 64):
            self.canal.append(Channel(i, 0, "MUTE", False))


class Cue:
    """ Estructura para cada cue"""

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
    """ Estructura para la secuencia"""

    def __init__(self):
        cue_list = []
        self.cue_list = cue_list

        self.cue_list.append(Cue())
        self.cue_list[0].rename("CUE 0")


class SendsButtons:
    """ Crea los botones de envios """

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
        """ Selecciona el envío """
        global envio_actual
        envios[envio_actual].send_button.config(bg=color_no_mod)
        # apaga_boton_envio(self.send_num)
        envio_actual = self.send_num  # Actualiza envio actual
        self.send_button.config(bg=color_mod)
        self.send_button.config(highlightbackground="WHITE")

        actualiza_executors()

        if envio_actual == 0:
            print_cmd("Master")
        else:
            print_cmd("Envio " + str(envio_actual))

    @staticmethod
    def send_color(send_num):
        if send_num == envio_actual:
            color = color_mod
        else:
            color = color_no_mod
        return color


class Exec:
    """ Crea los ejecutores, botones, etiquetas y faders"""

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

        # Etiqueta ID
        self.label = tk.Label(exec_frame,
                              font=default_font,
                              text="CH " + str(exec_ch + 1),
                              bg=color_fondos)
        self.label.grid(row=exec_y, column=exec_x)
        self.label.bind('<Double-Button-1>', lambda event: self.test(event))

        # Botón Mute
        self.mute = tk.Label(exec_frame,
                             font=default_font,
                             text=exec_mute,
                             bg=color_mute,
                             # highlightbackground=color_fondos,
                             fg="BLACK",
                             relief="ridge",
                             # borderless=1,
                             width=default_width)
        #                     command=self.toggle)  # Envía a toggle el numero del boton
        self.mute.grid(row=exec_y + 1, column=exec_x)
        self.mute.grid(sticky="nsew")
        self.mute.bind('<Button-1>', lambda event: self.toggle(event))

        # Fader
        self.fader = tk.Scale(exec_frame,
                              font=default_font,
                              bg=color_fondos,
                              bd=3,  # Grosor borde interior
                              troughcolor="gray80",  # Color del fondo
                              highlightcolor=color_fondos,
                              highlightbackground=color_fondos,
                              activebackground=color_mod,
                              showvalue=0,  # No muestra el valor
                              from_=100,
                              to=0,
                              length=fader_length
                              )
        self.fader.config(command=self.actualiza_etiqueta_fader)
        self.fader.grid(row=exec_y + 2, column=exec_x)
        self.fader.set(self.exec_value)  # Valor inicial
        self.fader.bind("<ButtonRelease-1>", self.modifica_fader)

        # Etiqueta con valor del fader. También indica si el canal se envía
        self.fader_label = tk.Label(exec_frame,
                                    font=default_font,
                                    text=self.actualiza_etiqueta_fader,
                                    bg=color_no_mod,  # Color normal de etiquetas
                                    fg="BLACK",
                                    relief="ridge",
                                    width=default_width)
        self.fader_label.grid(row=exec_y + 3, column=exec_x)
        self.fader_label.bind('<Double-Button-1>',
                              lambda event: self.tog_enviar(event))  # Al hacer doble clik elimina envío

        # Espacio en blanco
        self.white = tk.Label(exec_frame,
                              text="",
                              bg=color_fondos)
        self.white.grid(row=exec_y + 4, column=exec_x)

    def actualiza_etiqueta_fader(self, event):
        """ Actualiza los valores 0 a 100 en dB """
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
        """ Función para probar cosas varias, indica el valor del canal que se pulsa """
        # print(event)
        print("Send: ", envio_actual, "Ch:", (self.exec_ch + 1), "At: ", self.exec_value, self.exec_mute, "Mod: ",
              self.exec_mod)
        print_cmd("OJETE")

    def toggle(self, event):
        """Cambia el estado del botón MUTE"""
        # print(event)
        self.fader_label.config(bg=color_mod)  # Actualiza la etiqueta de valores (modificado)
        self.exec_mod = True  # Actualiza canal a modificado
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
        """ Lo que hace al modificar el fader """
        # # print(event)
        self.exec_value = self.fader.get()  # Actualiza variable del ejecutor
        print_cmd("Fader", (self.exec_ch + 1), "at", self.fader.get(), "%")  # Imprime los datos
        # Actualiza datos del fader
        seq[0].cue_list[cue_actual].envio[envio_actual].canal[self.exec_ch].ch_value = self.fader.get()
        # self.fader_label.config(text=self.fader.get())
        self.actualiza_etiqueta_fader(self)
        # Modifica enviado
        seq[0].cue_list[cue_actual].envio[envio_actual].canal[self.exec_ch].ch_mod = True
        self.exec_mod = True
        self.fader_label.config(bg=color_mod)

    def tog_enviar(self, event):
        """ Función para modificar si envía o no un canal """
        # print(event)
        if not self.exec_mod:
            self.exec_mod = True
            self.fader_label.config(bg=color_mod)
            print_cmd("Enviar valores del canal seleccionado")
            seq[0].cue_list[cue_actual].envio[envio_actual].canal[self.exec_ch].ch_mod = True

        else:
            self.exec_mod = False
            self.fader_label.config(bg=color_no_mod)
            print_cmd("No enviar valores del canal seleccionado")
            seq[0].cue_list[cue_actual].envio[envio_actual].canal[self.exec_ch].ch_mod = False

    def carga_valores(self, upd_value, upd_mute, upd_mod):
        self.exec_value = upd_value
        self.fader_label.config(text=self.actualiza_etiqueta_fader(self))  # Cambia nombre etiqueta

        # Actualiza valor MUTE del ejecutor
        self.exec_mute = upd_mute
        if self.exec_mute == "ON":
            self.mute.config(bg=color_on)
            self.mute.config(highlightbackground="WHITE")
            self.mute.config(text=self.exec_mute)

        else:
            self.mute.config(bg=color_mute)
            self.mute.config(highlightbackground="WHITE")
            self.mute.config(text=self.exec_mute)

        # Actualiza propiedad modificada del fader
        self.exec_mod = upd_mod
        if self.exec_mod:
            self.fader_label.config(bg=color_mod)
        else:
            self.fader_label.config(bg=color_no_mod)

        self.fader.set(upd_value)  # Carga valor en el ejecutor


class OpcionesNameShowCue:
    """ Estructura para las opciones del nombre del show y de la CUE actual"""

    def __init__(self, option_frame):
        self.option_frame = option_frame
        self.Show_label = tk.Label
        self.Show_entry = tk.Entry
        self.Cue_label = tk.Label
        self.Cue_entry = tk.Entry

        # COLUMNA 1 #################################################################
        # Etiqueta show

        self.Show_label = tk.Label(self.option_frame,
                                   font=default_font,
                                   text="SHOW NAME:",
                                   bg=color_fondos,
                                   width=10)
        self.Show_label.grid(sticky="W", row=0, column=0, padx=8, pady=0)

        # Entrada nombre show
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

        # Etiqueta cue actual
        self.Cue_label = tk.Label(self.option_frame,
                                  font=default_font,
                                  text="CUE NAME:",
                                  fg="BLACK",
                                  bg=color_fondos,
                                  width=10)
        self.Cue_label.grid(sticky="W", row=1, column=0, padx=8, pady=0)

        # Entrada nombre cue
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
        """ Actualiza el nombre del show comprobando antes si es válido como
        nombre de archivo """
        # print(event)
        global show

        safe_string = str()
        for c in self.Show_entry.get():
            if c.isalnum() or c in [' ', '.', '/']:
                safe_string = safe_string + c

        valid = safe_string == self.Show_entry.get()
        if not valid:
            print_cmd("Nombre no valido.")
        else:
            show = self.Show_entry.get()
            listado_de_cues[0].listado_cues.selection_set(cue_actual)

    def cue_name(self, event):
        """ Actualiza el nombre de la CUE """
        # print(event)
        seq[0].cue_list[cue_actual].cue_name = self.Cue_entry.get()
        listado_de_cues[0].listado_upd()
        listado_de_cues[0].listado_cues.selection_set(cue_actual)


class OpcConfigRed:
    """ Estructura para las opciones de selección de red """

    def __init__(self, option_frame):
        self.option_frame = option_frame
        global host
        global host_osc
        global port
        global port_osc

        # Etiqueta Configuracion Red
        self.Label_desk = tk.Label(self.option_frame,
                                   font=default_font,
                                   text="NETWORK CONFIGURATION",
                                   fg="BLACK",
                                   bg=color_fondos,
                                   width=20)
        self.Label_desk.grid(row=2, column=0, padx=8, pady=0, columnspan=2, sticky='NSEW')

        # Etiqueta HOST
        self.Label_host = tk.Label(self.option_frame,
                                   font=default_font,
                                   text="DESK HOST",
                                   fg="BLACK",
                                   bg=color_fondos,
                                   width=10)
        self.Label_host.grid(sticky="W", row=3, column=0, padx=8, pady=0)

        # Entrada valor HOST
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

        # Etiqueta PORT
        self.Label_port = tk.Label(self.option_frame,
                                   font=default_font,
                                   text="DESK PORT",
                                   fg="BLACK",
                                   bg=color_fondos,
                                   width=10)
        self.Label_port.grid(sticky="W", row=4, column=0, padx=8, pady=0)

        # Entrada valor PORT
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

        # Etiqueta HOST OSC
        self.Label_host_osc = tk.Label(self.option_frame,
                                       font=default_font,
                                       text="OSC HOST",
                                       fg="BLACK",
                                       bg=color_fondos,
                                       width=10)
        self.Label_host_osc.grid(sticky="W", row=5, column=0, padx=8, pady=0)

        # Entrada valor HOST OSC
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

        # Etiqueta PORT OSC
        self.Label_osc_port = tk.Label(self.option_frame,
                                       font=default_font,
                                       text="OSC PORT",
                                       fg="BLACK",
                                       bg=color_fondos,
                                       width=10)
        self.Label_osc_port.grid(sticky="W", row=6, column=0, padx=8, pady=0)

        # Entrada valor PORT OSC
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
        """ Desbloquea la entrada de datos """
        # print(event)
        self.Port_entry.configure(state='normal')

    def port_number(self, event):
        """ Actualiza el PUERTO """
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
                print_cmd("Host no valido, cambiado a por defecto")
                print_cmd("Host actual: " + str(port))

        # listado_de_cues[0].selection_set(cue_actual)

        self.Port_entry.delete(0, "end")  # Actualiza texto
        self.Port_entry.insert(0, port)
        self.Port_entry.configure(state='disabled')  # Bloquea etiqueta

        root.focus_set()

    def host_enabled(self, event):
        """ Activar el host """
        # print(event)
        self.Host_entry.configure(state='normal')

    def host_number(self, event):
        """ Actualiza el HOST """
        # print(event)
        global host
        if self.Host_entry.get() == "":
            host = def_host
        else:
            host = self.Host_entry.get()
        # lista_cues.selection_set(cue_actual)

        self.Host_entry.delete(0, "end")  # Actualiza texto
        self.Host_entry.insert(0, host)
        self.Host_entry.configure(state='disabled')  # Bloquea etiqueta

        root.focus_set()  # Devuelve focus

    def host_osc_enabled(self, event):
        """ Desbloquea la entrada de datos """
        # print(event)
        self.Host_osc_entry.configure(state='normal')

    def host_osc_number(self, event):
        """ Actualiza el HOST OSC"""
        # print(event)
        global host_osc

        if self.Host_osc_entry.get() == "":
            host_osc = def_host_osc
        else:
            host_osc = self.Host_osc_entry.get()

        self.Host_osc_entry.delete(0, "end")  # Actualiza texto
        self.Host_osc_entry.insert(0, host_osc)
        self.Host_osc_entry.configure(state='disabled')  # Bloquea etiqueta

        root.focus_set()  # Devuelve focus

        # Reintenta iniciar el servidor OSC con la nueva configuración
        osc_thread()

    def port_osc_enabled(self, event):
        # print(event)
        self.Port_osc_entry.configure(state='normal')

    def port_osc_number(self, event):
        """ Actualiza el PUERTO OSC"""
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
                print_cmd("OSC Port no valido, cambiado a por defecto")
                print_cmd("OSC Port actual: " + str(port_osc))

        self.Port_osc_entry.delete(0, "end")  # Actualiza texto
        self.Port_osc_entry.insert(0, port_osc)
        self.Port_osc_entry.configure(state='disabled')  # Bloquea etiqueta

        root.focus_set()

        # Reintenta iniciar el servidor OSC con el nuevo puerto
        osc_thread()

class OpcLlistaCues:
    """Muestra por pantalla la lista de Cues"""

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
        self.listado_cues.selection_set(cue_actual)  # Selección de la lista por defecto
        self.listado_cues.bind('<ButtonRelease-1>', self.goto_lista)

        self.scrollbar.config(command=self.listado_cues.yview)

    def goto_lista(self, event):
        """ Salta a la cue pulsada """
        # print(event)
        borra_cmd()  # Limpia la pantalla
        gotocue(self.listado_cues.curselection()[0])  # Selección de la lista por defecto

    def listado_upd(self):
        """ Actualiza los elementos de la lista de CUES """
        self.listado_cues.delete(0, "end")

        for x in range(0, len(seq[0].cue_list)):  # Crea los elementos de la lista
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

        # Boton previos CUE
        self.prevcue_button = Button(self.option_frame,
                                     font=med_font,
                                     fg="BLACK",
                                     text='<< PREV',
                                     bg=light_green,
                                     highlightbackground="WHITE",
                                     borderless=1,
                                     command=self.prev_cue)
        self.prevcue_button.grid(sticky="W", row=1, column=7, padx=8, pady=4)

        # Boton next CUE
        self.nextcue_button = Button(self.option_frame,
                                     font=med_font,
                                     fg="BLACK",
                                     text='NEXT >>',
                                     bg=light_green,
                                     highlightbackground="WHITE",
                                     borderless=1,
                                     command=self.next_cue)
        self.nextcue_button.grid(sticky="W", row=2, column=7, padx=8, pady=4)

        # Boton move up
        self.moveup_button = Button(self.option_frame,
                                    font=med_font,
                                    fg="BLACK",
                                    text='MOVE UP',
                                    bg="lavender",
                                    highlightbackground="WHITE",
                                    borderless=1,
                                    command=self.move_up)
        self.moveup_button.grid(sticky="W", row=3, column=7, padx=8, pady=4)

        # Boton move down
        self.movedw_button = Button(self.option_frame,
                                    font=med_font,
                                    fg="BLACK",
                                    text='MOVE DW',
                                    bg="lavender",
                                    highlightbackground="WHITE",
                                    borderless=1,
                                    command=self.move_dw)
        self.movedw_button.grid(sticky="W", row=4, column=7, padx=8, pady=4)

        # Boton nueva CUE
        self.newcue_button = Button(self.option_frame,
                                    font=med_font,
                                    fg="BLACK",
                                    text='NEW',
                                    bg="lavender",
                                    highlightbackground="WHITE",
                                    borderless=1,
                                    command=self.new_cue)
        self.newcue_button.grid(sticky="W", row=5, column=7, padx=8, pady=4)

        # Boton borrar CUE
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
        """ Desplaza hacia arriba la CUE actual """

        global cue_actual

        if cue_actual != 0:
            seq[0].cue_list[cue_actual], seq[0].cue_list[cue_actual - 1] \
                = seq[0].cue_list[cue_actual - 1], seq[0].cue_list[cue_actual]
            cue_actual -= 1
            borra_cmd()  # Limpia la pantalla
            gotocue(cue_actual)

        else:
            pass

    @staticmethod
    def move_dw():
        """ Desplaza hacia abajo la CUE actual """

        global cue_actual

        if cue_actual != len(seq[0].cue_list) - 1:
            seq[0].cue_list[cue_actual], seq[0].cue_list[cue_actual + 1] \
                = seq[0].cue_list[cue_actual + 1], seq[0].cue_list[cue_actual]
            cue_actual += 1
            borra_cmd()  # Limpia la pantalla
            gotocue(cue_actual)

    @staticmethod
    def new_cue():
        """ Crea una nueva CUE """
        global cue_actual
        seq[0].cue_list.append(Cue())
        cue_actual = ((len(seq[0].cue_list)) - 1)  # Nos vamos a la última CUE
        actualiza_executors()
        seq[0].cue_list[cue_actual].cue_name = ("CUE " + str(cue_actual))  # Añade un nombre genérico  de cue
        listado_de_cues[0].listado_upd()
        borra_cmd()  # Limpia la pantalla
        gotocue(cue_actual)
        print_cmd("Creada CUE", cue_actual)

    @staticmethod
    def delete_cue(event):
        """ Borra la CUE seleccionada """
        # print(event)
        global cue_actual

        if len(seq[0].cue_list) != 1:
            del seq[0].cue_list[cue_actual]  # Borra el elemento completo de la secuencia
            if cue_actual != 0:
                cue_actual -= 1
            else:
                pass

        else:  # La CUE 0 no se puede borrar, solo se inicializa
            clear_cue()

        borra_cmd()  # Limpia la pantalla
        print_cmd("CUE eliminada")
        gotocue(cue_actual)  # Actualiza la mesa


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

        # Boton que envía valores
        self.send_button = tk.Label(self.option_frame,
                                  font=med_font,
                                  text='SEND TO DESK',
                                  #command=self.conectar,
                                  bg=light_red,
                                  #borderless=1,
                                  highlightbackground="WHITE")
        self.send_button.grid(sticky="W", row=1, column=8, padx=8, pady=4)
        self.send_button.bind('<Button-1>', lambda event: self.conectar_directo(event))

        # Boton SELECT ALL
        self.selectall_button = Button(self.option_frame,
                                       font=med_font,
                                       fg="BLACK",
                                       text='SELECT',
                                       bg=color_mod,
                                       borderless=1,
                                       highlightbackground="WHITE",
                                       command=self.select_all)
        self.selectall_button.grid(sticky="W", row=2, column=8, padx=8, pady=4)

        # Boton UNSELECT ALL
        self.selectall_button = Button(self.option_frame,
                                       font=med_font,
                                       fg="BLACK",
                                       text='UNSELECT',
                                       bg=color_no_mod,
                                       borderless=1,
                                       highlightbackground="WHITE",
                                       command=self.unselect_all)
        self.selectall_button.grid(sticky="W", row=3, column=8, padx=8, pady=4)

        # Boton limpiar CUE
        self.clearcue_button = Button(self.option_frame,
                                      font=med_font,
                                      fg="BLACK",
                                      text='CLEAR',
                                      bg="lavender",
                                      borderless=1,
                                      highlightbackground="WHITE",
                                      command=self.clear_cue_upd)
        self.clearcue_button.grid(sticky="W", row=4, column=8, padx=8, pady=4)

        # Boton ON ALL
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

        # Boton MUTE ALL
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
        """ Cambia el color del check para que sea visible que está activado"""
        # print(event)

        global autosend_global
        if (self.autosend.get()) == True:
            self.a_send.config(fg="BLACK")
            autosend_global = False
            print_cmd("*** Envío automático DESACTIVADO ***")
        else:
            self.a_send.config(fg="RED")
            print_cmd("*** Envío automático ACTIVADO ***")
            autosend_global = True

    def conectar_directo(self, event):
        """ Trata de conectar sin hilo paralelo """
        send_values()

    def conectar(self, event):
        """ Trata de conectar y enviar valores a la mesa, comienza un hilo paralelo
        para que no se bloquee la mesa mientras trata de conectar """
        self.send_button["state"] = "disabled"  # Cambiamos estado del botón
        self.send_button.config(bg="grey",
                                highlightbackground="WHITE")

        # Abrimos hilo en paralelo
        self.task = threading.Thread(target=send_values)
        self.task.daemon = True  # Para finalizar el hilo al cerrar la aplicación principal
        self.task.start()
        #  Chequamos periodicamente si el hilo ha finalizado
        self.schedule_check(self.task)  # Comprobar que ha conseguido la conexión

    def schedule_check(self, task):
        """ Programar la ejecución de la función `check_if_done()` dentro de un segundo.  """
        root.after(1000, self.check_if_done, task)

    def check_if_done(self, task):
        """ Comprueba si el hilo ha finalizado y realiza algunas acciones """
        # Si el hilo ha finalizado, restaruar el botón y mostrar un mensaje.
        if not task.is_alive():
            print_cmd("Conexión finalizada")
            # Restablecer el botón.
            self.send_button["state"] = "normal"
            self.send_button.config(bg=light_red,
                                    highlightbackground="WHITE")
        else:
            # Si no, volver a chequear en unos momentos.
            self.schedule_check(task)

    @staticmethod
    def select_all():
        """ Marca para enviar todos los canales del envio """
        for i in range(0, 64):
            seq[0].cue_list[cue_actual].envio[envio_actual].canal[
                i].ch_mod = True  # fader_label[i].config(bg=color_mod)
        actualiza_executors()
        print_cmd("Todos los canales marcados para enviar")

    @staticmethod
    def unselect_all():
        """ Desmarca para enviar todos los canales del envio """
        for i in range(0, 64):
            seq[0].cue_list[cue_actual].envio[envio_actual].canal[i].ch_mod = False
        actualiza_executors()
        print_cmd("Desmarcados todos los canales para enviar")

    @staticmethod
    def clear_cue_upd():
        """ Pone todos los valores a 0 y actualiza los ejecutores """
        clear_cue()
        actualiza_executors()

    @staticmethod
    def on_all():
        """ Desmutea todos los canales del envio  """
        for i in range(0, 64):
            seq[0].cue_list[cue_actual].envio[envio_actual].canal[i].ch_mute = "ON"
        actualiza_executors()
        print_cmd("Todos los canales desmuteados")

    @staticmethod
    def mute_all():
        """ Mutea todos los canales del envio  """
        for i in range(0, 64):
            seq[0].cue_list[cue_actual].envio[envio_actual].canal[i].ch_mute = "MUTE"
        actualiza_executors()
        print_cmd("Todos los canales muteados")


class OpcionesVentanaCmd:
    """ Ventana para mostrar comandos """

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
        """ Imprime en consola y en la pantalla Text """
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
        """ Borra la pantalla """
        self.cmd.configure(state='normal')
        self.cmd.delete(1.0, "end")
        self.cmd.configure(state='disabled')


class Mesa:
    """ Bloque principal del programa"""

    def __init__(self, root):
        super().__init__()
        """ Inicializa la mesa """
        # Creamos ventana principal
        root.title("Peramesa v3.0")
        root.minsize(width=1330, height=820)  # Tamaño minimo principal
        root.configure(bg=color_fondos)

        # Intenta poner icono
        try:
            root.wm_iconbitmap(default=r'pera.icns')
        except Exception as e:
            print(e)
            try:
                img = tk.Image("photo", file="peramesa.png")
                root.iconphoto(True, img)  # you may also want to try this.
                root.tk.call('wm', 'iconphoto', root._w, img)
            except Exception as e:
                print(e)
                pass

        root.protocol("WM_DELETE_WINDOW", on_closing)  # Al cerrar el programa

        # Creamos los distintos frames
        self.inicializa()
        self.crear_ejecutores()
        self.crear_envios()
        self.crear_opciones()

        # Cramos barra de menus
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

    # Funciones para ficheros

    @staticmethod
    def new_show():
        """ Crea un nuevo archivo """
        global cue_actual
        global show

        crear_archivo(temp_file_name)  # Crea backup
        cue_actual = 0  # Nos situamos en la primera CUE y la borramos
        clear_cue()

        if len(seq[0].cue_list) != 1:  # Comprueba que hay más de un elemento
            for x in range(1, len(seq[0].cue_list)):  # Borra todas las cues menos la 0
                del seq[0].cue_list[1]
        else:
            pass

        show = "NEW SHOW"
        show_name_update()
        borra_cmd()  # Limpia la pantalla
        gotocue(cue_actual)  # Actualiza faders

    @staticmethod
    def load_show():
        """ Función para cargar show """
        try:
            files = [('CSV', '*.csv'),
                     ('Text Document', '*.txt')]
            ruta = askopenfilename(filetypes=files, defaultextension=files)
            fichero = open(ruta, 'r')
            datos = fichero.read()
            fichero.close()
            if datos == '':
                print_cmd("Archivo no valido")
            else:
                monta_show(datos)

        except AttributeError as e:
            print(e)
            print_cmd("Cancelado antes de cargar")

    @staticmethod
    def save_show():
        """ Función para grabar el show """
        global show

        try:
            files = [('CSV', '*.csv'),
                     ('Text Document', '*.txt')]
            ruta = asksaveasfilename(filetypes=files, defaultextension=files)
            ruta_completa = Path(ruta)

            # actualiza nombre del show
            show = str(Path(ruta).stem)  # Recupera el nombre
            show_name_update()

            ruta_sin_extension = str(ruta_completa.with_suffix(''))
            crear_archivo(ruta_sin_extension)

        except Exception as e:
            print(e)
            print_cmd("Cancelado antes de guardar")

    @staticmethod
    def help_window():
        """ Crea ventana de ayuda """
        help_w = tk.Toplevel(root)  # Crea ventana
        help_w.geometry('800x800')
        help_w.resizable(width=0, height=0)
        help_w.title("Help Peramesa v3.0")

        h_scroll = tk.Scrollbar(help_w)  # Crea scrollbar
        h_scroll.pack(side=tk.RIGHT,
                      fill=tk.Y)  # Situa el scroll a la derecha
        help_text = tk.Text(help_w,
                            wrap=tk.NONE,
                            yscrollcommand=h_scroll.set)  # text windget
        help_text.pack(fill=tk.BOTH,
                       expand=tk.YES,
                       side=tk.LEFT)

        help_file = Path(__file__).with_name("help_text.txt")
        long_text = help_file.read_text(encoding="utf-8")
        help_text.insert(tk.END, long_text)
        h_scroll.config(command=help_text.yview)
        tk.mainloop()

    # Crear bloques del programa

    @staticmethod
    def inicializa():
        """ Inicializamos valores de mesa  """
        seq.append(Seq())

    @staticmethod
    def crear_ejecutores():
        """ Crea el frame con los ejecutores"""
        # Frame con los ejecutores
        exec_frame = tk.Frame(root)
        exec_frame.configure(bg=color_fondos)
        exec_frame.grid(row=1, column=0, padx=5, pady=5)

        # Bucle para crear los ejecutores
        for i in range(0, 64):
            # Posiciones de "grid"
            if i < 32:
                posicion_x = i
                posicion_y = 6
            else:
                posicion_y = 1
                posicion_x = i - 32

            # Creamos los ejecutores
            executor.append(Exec(i,
                                 seq[0].cue_list[0].envio[envio_actual].canal[i].ch_value,
                                 seq[0].cue_list[0].envio[envio_actual].canal[i].ch_mute,
                                 False, posicion_x, posicion_y, exec_frame))

    @staticmethod
    def crear_envios():
        """ Apartado para los botones de envio """
        sends_frame = tk.Frame(root)
        sends_frame.configure(bg=color_fondos)
        sends_frame.grid(sticky="W", row=0, column=0, padx=5, pady=5)

        for i in range(0, 17):  # Para los 16 envios y el Master
            envios.append(SendsButtons(i, sends_frame))

    def crear_opciones(self):
        option_frame = tk.Frame(root)  # Creamos el frame para las opciones
        option_frame.config(bg=color_fondos)  # Color de fondo del frame
        option_frame.grid(sticky="W", row=2, column=0, padx=5, pady=5)

        self.OpcionesNameShowCue = OpcionesNameShowCue(option_frame)  # Botones para cambiar nobre show y CUE
        self.OpcConfigRed = OpcConfigRed(option_frame)  # Botones para cambiar la red de evíos
        listado_de_cues.append(OpcLlistaCues(option_frame))  # Crea la lista de CUES

        self.OpcListButtons = OpcListButtons(option_frame)  # Crea botones para moverse por la lista
        self.OpcionExtraButtons = OpcionExtraButtons(option_frame)  # Crea botones con algunas funciones extra
        self.ventana_comando = OpcionesVentanaCmd(option_frame)  # Crea ventana comandos


if __name__ == '__main__':
    root = tk.Tk()
    app = Mesa(root)

    # Intenta cargar el ultimo show utilizado
    if show_iniciado == 0:
        show_inicial()

    osc_thread()
    root.mainloop()
