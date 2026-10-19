"""
Bo7 Zombies Simple Tool
Escribe los comandos en la consola del juego por vos.

Uso:
  1. Abrí el juego y quedate en el menú de Zombies.
  2. Corré:  pythonw "Bo7 Zombies Simple Tool.pyw"
     (si el juego corre como Administrador, este script también tiene que correr como Administrador)
  3. Hacé clic en el mapa. El programa pasa al juego y escribe:
        xstartprivateparty
        xstartlobby_patched
        ui_mapname <mapa>
        xpartygo
No necesita instalar nada (solo Python 3 para Windows).
"""
import ctypes
import sys
import json
import os
import threading
import time
import tkinter as tk
from ctypes import wintypes
from tkinter import ttk, messagebox

# ---------------------------------------------------------------- config
MAPAS = [
    ("Ashes of the Damned", "zm_sat_firefly"),
    ("Astra Malorum",       "zm_sat_ruby"),
    ("Paradox Junction",    "zm_sat_mantis"),
    ("Totenreich",          "zm_sat_locust"),
    ("Kowakujō",            "zm_sat_hornet"),
    ("Rex Infernus",        "zm_sat_scarab"),
    ("Dead Ops Arcade 4",   "zm_sat_ztron4"),
]

TITULO_VENTANA = "Black Ops 7"   # parte del título de la ventana del juego
SCAN_CONSOLA = 0x29              # tecla física arriba de Tab ( | ° ¬ en teclado latino)

CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "launcher_config.json")
DEFAULTS = {
    "espera_consola": 0.4,     # seg. tras abrir la consola
    "espera_comando": 1.5,     # seg. entre comandos
    "espera_lobby": 4.0,       # seg. tras xstartlobby_patched (cargar el lobby)
    "espera_tecla": 0.02,      # seg. entre letras
    "espera_esc": 5.0,         # seg. presionando ESC al salir de la partida
}

# ---------------------------------------------------------------- Win32 / SendInput
user32 = ctypes.WinDLL("user32", use_last_error=True)

INPUT_KEYBOARD = 1
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_UNICODE = 0x0004
KEYEVENTF_SCANCODE = 0x0008
SCAN_ENTER = 0x1C
ULONG_PTR = ctypes.c_size_t


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [("wVk", wintypes.WORD), ("wScan", wintypes.WORD),
                ("dwFlags", wintypes.DWORD), ("time", wintypes.DWORD),
                ("dwExtraInfo", ULONG_PTR)]


class MOUSEINPUT(ctypes.Structure):
    _fields_ = [("dx", wintypes.LONG), ("dy", wintypes.LONG),
                ("mouseData", wintypes.DWORD), ("dwFlags", wintypes.DWORD),
                ("time", wintypes.DWORD), ("dwExtraInfo", ULONG_PTR)]


class _INPUTunion(ctypes.Union):
    _fields_ = [("ki", KEYBDINPUT), ("mi", MOUSEINPUT)]


class INPUT(ctypes.Structure):
    _fields_ = [("type", wintypes.DWORD), ("u", _INPUTunion)]


def _send(scan=0, flags=0):
    inp = INPUT(type=INPUT_KEYBOARD)
    inp.u.ki = KEYBDINPUT(0, scan, flags, 0, 0)
    user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))


def tecla_vk(vk, espera=0.03):
    scan = user32.MapVirtualKeyW(vk, 0)
    for flags in (0, KEYEVENTF_KEYUP):
        inp = INPUT(type=INPUT_KEYBOARD)
        inp.u.ki = KEYBDINPUT(vk, scan, flags, 0, 0)
        user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))
        time.sleep(espera)


def tecla_char(ch, espera=0.03):
    code = ord(ch)
    _send(code, KEYEVENTF_UNICODE)
    time.sleep(espera)
    _send(code, KEYEVENTF_UNICODE | KEYEVENTF_KEYUP)
    time.sleep(espera)


# ---- Modo "directo": manda mensajes de teclado a la ventana del juego
WM_KEYDOWN, WM_KEYUP, WM_CHAR = 0x0100, 0x0101, 0x0102
ventana_juego = [None]
user32.PostMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]


def _post_tecla(vk, scan, espera=0.03):
    h = ventana_juego[0]
    lp_down = 1 | (scan << 16)
    lp_up = lp_down | (1 << 30) | (1 << 31)
    user32.PostMessageW(h, WM_KEYDOWN, vk, lp_down)
    time.sleep(espera)
    user32.PostMessageW(h, WM_KEYUP, vk, lp_up)
    time.sleep(espera)


def _post_texto(texto, espera):
    for ch in texto:
        user32.PostMessageW(ventana_juego[0], WM_CHAR, ord(ch), 1)
        time.sleep(espera)


# Formas de abrir la consola
METODOS_CONSOLA = {
    "Tecla arriba de Tab (directo)": lambda: _post_tecla(0xDC, SCAN_CONSOLA),
    "Tecla arriba de Tab (scan)":    lambda: tecla_scan(SCAN_CONSOLA),
    "Tecla arriba de Tab (VK_OEM_5)": lambda: tecla_vk(0xDC),
    "~ (VK_OEM_3)":                  lambda: tecla_vk(0xC0),
    "~ (carácter)":                  lambda: tecla_char("~"),
}
METODO_DEFAULT = "Tecla arriba de Tab (VK_OEM_5)"
metodo_consola = [METODO_DEFAULT]


def modo_directo():
    return "(directo)" in metodo_consola[0]


def abrir_consola():
    METODOS_CONSOLA[metodo_consola[0]]()


def enter():
    if modo_directo():
        _post_tecla(0x0D, SCAN_ENTER)
    else:
        tecla_scan(SCAN_ENTER)


def tecla_scan(scan, espera=0.03):
    _send(scan, KEYEVENTF_SCANCODE)
    time.sleep(espera)
    _send(scan, KEYEVENTF_SCANCODE | KEYEVENTF_KEYUP)
    time.sleep(espera)


def escribir(texto, espera):
    if modo_directo():
        _post_texto(texto, espera)
        return
    for ch in texto:
        code = ord(ch)
        _send(code, KEYEVENTF_UNICODE)
        _send(code, KEYEVENTF_UNICODE | KEYEVENTF_KEYUP)
        time.sleep(espera)


kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)


def _normalizar(s):
    return "".join(c for c in s.lower() if c.isalnum())


def _exe_de_ventana(hwnd):
    pid = wintypes.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    h = kernel32.OpenProcess(0x1000, False, pid.value)  # PROCESS_QUERY_LIMITED_INFORMATION
    if not h:
        return ""
    try:
        buf = ctypes.create_unicode_buffer(1024)
        size = wintypes.DWORD(1024)
        if kernel32.QueryFullProcessImageNameW(h, 0, buf, ctypes.byref(size)):
            return os.path.basename(buf.value).lower()
    finally:
        kernel32.CloseHandle(h)
    return ""


def listar_ventanas():
    ventanas = []
    EnumProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

    def cb(hwnd, _):
        if user32.IsWindowVisible(hwnd):
            n = user32.GetWindowTextLengthW(hwnd)
            buf = ctypes.create_unicode_buffer(n + 1)
            user32.GetWindowTextW(hwnd, buf, n + 1)
            ventanas.append((hwnd, buf.value))
        return True

    proc = EnumProc(cb)
    user32.EnumWindows(proc, 0)
    return ventanas


def buscar_ventana(_fragmento=None):
    ventanas = listar_ventanas()
    # 1) por nombre del ejecutable
    for hwnd, _t in ventanas:
        exe = _exe_de_ventana(hwnd)
        if exe.startswith("cod") and exe.endswith(".exe") and "launcher" not in exe:
            return hwnd
    # 2) por título, ignorando símbolos (®, :, espacios raros)
    for hwnd, titulo in ventanas:
        t = _normalizar(titulo)
        if "blackops7" in t or ("callofduty" in t and "battle" not in t):
            return hwnd
    return None


def enfocar(hwnd):
    ventana_juego[0] = hwnd
    user32.ShowWindow(hwnd, 9)          # SW_RESTORE
    _send(0x38)                          # Alt (truco para que Windows permita el foco)
    _send(0x38, KEYEVENTF_KEYUP)
    user32.SetForegroundWindow(hwnd)
    time.sleep(0.6)
    return user32.GetForegroundWindow() == hwnd


# ---------------------------------------------------------------- lógica
def cargar_config():
    cfg = dict(DEFAULTS)
    try:
        with open(CONFIG_PATH, encoding="utf-8") as f:
            cfg.update(json.load(f))
    except Exception:
        pass
    return cfg


def guardar_config(cfg):
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)
    except Exception:
        pass


def comando(cmd, cfg):
    abrir_consola()
    time.sleep(cfg["espera_consola"])
    escribir(cmd, cfg["espera_tecla"])
    time.sleep(0.1)
    enter()
    time.sleep(0.2)
    abrir_consola()                          # cerrar consola


# ---------------------------------------------------------------- textos (idiomas)
TEXTOS = {
    "es": {
        "titulo": "Bo7 Zombies Simple Tool",
        "tab_mapas": "  Mapas  ",
        "tab_camos": "  Camuflajes  ",
        "tab_ajustes": "  Ajustes  ",
        "elige_modo": "1. Elegí el modo de juego:",
        "salir": "Salir de la partida (disconnect + ESC)",
        "spam_esc": "Presionando ESC...",
        "salida_hecha": "Listo, saliste de la partida.",
        "esperar_esc": "ESC al salir",
        "zombie_cheat": "Empezar con +100.000 esencia, +25.000 chatarra y chatarra rara, y puertas abiertas",
        "elige_mapa": "2. Elegí el mapa (estando en el menú de Zombies):",
        "elige_camo": "Estando en el menú de Zombies, elegí un camuflaje:",
        "loadout": "Clase",
        "arma": "Arma",
        "principal": "Principal",
        "secundaria": "Secundaria",
        "camo_mp": "Maestría Multijugador",
        "camo_zm": "Maestría Zombies",
        "camo_wz": "Maestría Warzone",
        "tab_ww": "  Armas maravilla  ",
        "elige_ww": "Estando en el menú de Zombies, elegí un arma maravilla:",
        "arma_hecha": "Arma puesta: {}",
        "reset_arma": "Reiniciar arma (desbugear)",
        "reset_hecho": "Arma reiniciada a la de por defecto.",
        "sec_ranked_mp": "Ranked Multijugador",
        "sec_ranked_wz": "Ranked Warzone",
        "sec_cdl": "Equipos CDL",
        "sec_eventos": "Eventos",
        "sec_incentivos": "Incentivos",
        "sec_maestria_mp": "Maestría Multijugador",
        "sec_maestria_zm": "Maestría Zombies",
        "sec_ranked": "Ranked",
        "sec_especiales": "Especiales",
        "tiempos": " Tiempos (segundos) ",
        "entre_cmd": "Entre comandos",
        "esperar_lobby": "Esperar lobby",
        "abrir_consola": "Abrir consola",
        "tecla_consola": " Tecla de consola ",
        "probar": "Probar consola",
        "idioma": " Idioma ",
        "listo": "Listo.",
        "no_ventana": "No encuentro la ventana del juego.",
        "no_foco": "No pude pasar al juego. Hacé clic en el juego y probá de nuevo.",
        "escribiendo": "Escribiendo: {}",
        "hecho_mapa": "Listo: {}",
        "hecho_camo": "Camuflaje aplicado: {}",
        "probando": "Probando consola con: {}",
        "se_abrio": "¿Se abrió la consola? Si no, probá otro método.",
        "err_tiempos": "Los tiempos tienen que ser números.",
        "reliquia_titulo_zm_rb_rh_mod": "Mister Peeks Mayhem",
        "reliquia_txt_zm_rb_rh_mod": "En el juego se abrió el menú de reliquias.\n\n"
                        "1. Seleccioná a Mister Peeks (el osito dorado de la derecha).\n"
                        "2. Dale CONFIRMAR en el juego.\n"
                        "3. Volvé acá y presioná Continuar.",
        "reliquia_titulo_zm_rb_r_mod_survival": "Sobrevivencia Maldito",
        "reliquia_txt_zm_rb_r_mod_survival": "En el juego se abrió el menú de reliquias.\n\n"
                        "1. Elegí las reliquias que quieras.\n"
                        "2. Dale CONFIRMAR en el juego.\n"
                        "3. Volvé acá y presioná Continuar.",
        "reliquia_titulo_zm_rb_r_mod": "Modo Maldito",
        "reliquia_txt_zm_rb_r_mod": "En el juego se abrió el menú de reliquias.\n\n"
                        "1. Elegí las reliquias que quieras.\n"
                        "2. Dale CONFIRMAR en el juego.\n"
                        "3. Volvé acá y presioná Continuar.",
        "continuar": "Continuar",
        "cancelar": "Cancelar",
        "esperando_reliquia": "Esperando que elijas las reliquias...",
        "cancelado": "Cancelado.",
    },
    "en": {
        "titulo": "Bo7 Zombies Simple Tool",
        "tab_mapas": "  Maps  ",
        "tab_camos": "  Camos  ",
        "tab_ajustes": "  Settings  ",
        "elige_modo": "1. Pick a game mode:",
        "salir": "Leave match (disconnect + ESC)",
        "spam_esc": "Pressing ESC...",
        "salida_hecha": "Done, you left the match.",
        "esperar_esc": "ESC on leave",
        "zombie_cheat": "Start with +100,000 essence, +25,000 salvage & rare salvage, all doors open",
        "elige_mapa": "2. Pick a map (while in the Zombies menu):",
        "elige_camo": "While in the Zombies menu, pick a camo:",
        "loadout": "Loadout",
        "arma": "Weapon",
        "principal": "Primary",
        "secundaria": "Secondary",
        "camo_mp": "Multiplayer Mastery",
        "camo_zm": "Zombies Mastery",
        "camo_wz": "Warzone Mastery",
        "tab_ww": "  Wonder Weapons  ",
        "elige_ww": "While in the Zombies menu, pick a wonder weapon:",
        "arma_hecha": "Weapon set: {}",
        "reset_arma": "Reset weapon (unbug)",
        "reset_hecho": "Weapon reset to default.",
        "sec_ranked_mp": "Ranked Multiplayer",
        "sec_ranked_wz": "Ranked Warzone",
        "sec_cdl": "CDL Teams",
        "sec_eventos": "Events",
        "sec_incentivos": "Incentives",
        "sec_maestria_mp": "Multiplayer Mastery",
        "sec_maestria_zm": "Zombies Mastery",
        "sec_ranked": "Ranked",
        "sec_especiales": "Specials",
        "tiempos": " Timings (seconds) ",
        "entre_cmd": "Between commands",
        "esperar_lobby": "Lobby wait",
        "abrir_consola": "Open console",
        "tecla_consola": " Console key ",
        "probar": "Test console",
        "idioma": " Language ",
        "listo": "Ready.",
        "no_ventana": "Can't find the game window.",
        "no_foco": "Couldn't switch to the game. Click the game and try again.",
        "escribiendo": "Typing: {}",
        "hecho_mapa": "Done: {}",
        "hecho_camo": "Camo applied: {}",
        "probando": "Testing console with: {}",
        "se_abrio": "Did the console open? If not, try another method.",
        "err_tiempos": "Timings must be numbers.",
        "reliquia_titulo_zm_rb_rh_mod": "Mister Peeks Mayhem",
        "reliquia_txt_zm_rb_rh_mod": "The relic menu is now open in the game.\n\n"
                        "1. Select Mister Peeks (the golden teddy bear on the right).\n"
                        "2. Press CONFIRM in the game.\n"
                        "3. Come back here and press Continue.",
        "reliquia_titulo_zm_rb_r_mod_survival": "Cursed Survival",
        "reliquia_txt_zm_rb_r_mod_survival": "The relic menu is now open in the game.\n\n"
                        "1. Pick the relics you want.\n"
                        "2. Press CONFIRM in the game.\n"
                        "3. Come back here and press Continue.",
        "reliquia_titulo_zm_rb_r_mod": "Cursed",
        "reliquia_txt_zm_rb_r_mod": "The relic menu is now open in the game.\n\n"
                        "1. Pick the relics you want.\n"
                        "2. Press CONFIRM in the game.\n"
                        "3. Come back here and press Continue.",
        "continuar": "Continue",
        "cancelar": "Cancel",
        "esperando_reliquia": "Waiting for you to pick relics...",
        "cancelado": "Cancelled.",
    },
}

# En Zombies hay una sola clase con una sola arma -> loadout 0, weaponSetups 0.
# Para Multijugador poné esto en True: aparece el selector de clase (0, 1, 2...)
# y de arma (0 = principal, 1 = secundaria), y el archivo es "sat_mp_loadouts_private".
MOSTRAR_SELECTOR_CLASE = False

CAMOS = {
    "camo_mp": [("Gold", 72158), ("Diamond", 72161), ("Dark Spine", 72164), ("Dark Matter", 72167)],
    "camo_zm": [("Mystic Gold", 72160), ("Opal", 72163), ("Afterlife", 72166), ("Nebula", 72169)],
    "camo_wz": [("Gold Tiger", 72159), ("King's Ransom", 72162), ("Catalyst", 72165), ("Abyss", 72168)],
}


# Armas maravilla de BO7 (índices de atu-atlas.github.io/BO7/#zombies)
ARMAS_MARAVILLA = [
    ("Ray Gun",                 121970),
    ("Ray Gun Mark II",         121969),
    ("Necrofluid Gauntlet",     101506),
    ("Little Green Menace-1",   101174),
    ("Blundergat",              102433),
    ("Jotunn Star",             121037),
    ("Nekomancer",              126903),
    ("Thrustodyne M23 (DOA4)",  98083),
    ("Wunderwaffe DG-2 (DOA4)", 100641),
]
# Warden's Blight (sat_ww_scarab_zm) no tiene índice conocido todavía.


# Modos de juego: (id, nombre en inglés, nombre en español)
MODOS = [
    ("zm_rb",              "Standard Round-Based Zombies", "Zombies por rondas - Estándar"),
    ("zm_rb_r_mod",        "Cursed",                       "Modo Maldito"),
    ("zm_guided",          "Directed Mode",                "Modo guiado"),
    ("zm_rb_rh_mod",       "Mister Peeks Mayhem",          "Mister Peeks Mayhem"),
    ("zm_rb_echo",         "Rogue Run",                    "Operación Rogue"),
    ("zm_training_course", "Zombies Training Course",      "Curso de entrenamiento de zombies"),
    ("zm_rb_survival",       "Survival",                   "Sobrevivencia"),
    ("zm_rb_r_mod_survival", "Cursed Survival",            "Sobrevivencia Maldito"),
]

# Modos de sobrevivencia: usan otros mapas (una zona de cada mapa)
MODOS_SURVIVAL = {"zm_rb_survival", "zm_rb_r_mod_survival"}

# Mapas de sobrevivencia: (nombre en inglés, nombre en español, id del mapa, zona/poi)
MAPAS_SURVIVAL = [
    ("Ashes - Farm",            "Ashes - Granja",         "zm_sat_firefly", "zone_farm"),
    ("Ashes - Exit 115",        "Ashes - Salida 115",     "zm_sat_firefly", "zone_exit115"),
    ("Ashes - Cosmodrome",      "Ashes - Cosmódromo",     "zm_sat_firefly", "zone_launchpad"),
    ("Ashes - Ashwood",         "Ashes - Ashwood",        "zm_sat_firefly", "ashwood"),
    ("Astra Malorum - Mars",    "Astra Malorum - Marte",  "zm_sat_ruby",    "zone_temple"),
    ("Paradox Junction - Nuked","Paradox Junction - Nuked","zm_sat_mantis", "future"),
    ("Totenreich - Lighthouse", "Totenreich - Faro",      "zm_sat_locust",  "zone_lighthouse"),
    ("Kowakujō - Castle",       "Kowakujō - Castillo",    "zm_sat_hornet",  "castle"),
]

# Inductor de velocidad (rampage inducer): en todos los modos menos estos y Dead Ops Arcade
RAMPAGE_CMD = "set enable_rampage_inducer 1"
RAMPAGE_EXCLUIR_MODOS = {"zm_guided", "zm_rb_echo"}
RAMPAGE_EXCLUIR_MAPAS = {"zm_sat_ztron4"}



# Camos extra por juego: {juego: [(seccion, [(nombre, index), ...]), ...]}
CAMOS_JUEGOS = {
    'BO6': [
        ('ranked_mp', [('T1 #1', 90125), ('T2 #1', 90127), ('T2 #2', 90128), ('T2 #3', 90129), ('T2 #4', 90130), ('T2 #5', 90131), ('T2 #6', 90132), ('T5 #1', 101785), ('T5 #2', 101787), ('T5 #3', 101782), ('T5 #4', 101783), ('T5 #5', 101784), ('T5 #6', 101786), ('T6 #1', 119434), ('T6 #2', 119430), ('T6 #3', 119435), ('T6 #4', 119432), ('T6 #5', 119433), ('T6 #6', 119431)]),
        ('ranked_wz', [('T1 #1', 90126), ('T2 #3', 90135), ('T2 #4', 90136), ('T2 #5', 90137), ('T2 #6', 90138), ('T2 #7', 90139), ('T2 #8', 90140), ('T2 #9', 93392), ('T3 #1', 96347), ('T4 #1', 97618), ('T5 #1', 99729), ('T6 #1', 99728)]),
        ('cdl', [('Breach', 85052), ('Cloud9', 85051), ('Falcons', 85043), ('FaZe', 85054), ('Guerrillas', 85050), ('Heretics', 85048), ('CDL (lau)', 85042), ('OpTic', 85045), ('Ravens', 85053), ('ROKKR', 85047), ('Surge', 85046), ('Thieves', 85049), ('Ultra', 85044)]),
        ('eventos', [('ev420', 99702), ('ev420blk', 99701), ('evbacklog', 120024), ('evbacklogblk', 120026), ('evghost', 120023), ('evghostblk', 120027), ('evgummy', 120025), ('evs45', 107613), ('evs45blk', 107612), ('evs55jab', 116364)]),
        ('incentivos', [('incentive_01', 81434), ('incentive_02', 99388), ('incentive_sat', 101184)]),
    ],
    'MW2': [
        ('maestria_mp', [('Gold', 12244), ('Platinum', 12256), ('Polyatomic', 12247), ('Orion', 12237)]),
    ],
    'MW3': [
        ('maestria_mp', [('Gilded', 36833), ('Forged', 36834), ('Priceless', 36835), ('Interstellar', 32513)]),
        ('maestria_zm', [('Maestría 1', 45992), ('Maestría 2', 45993), ('Maestría 3', 45994), ('Maestría 4', 39591)]),
        ('ranked', [('Ranked A', 45883), ('Ranked B', 45884), ('Ranked C', 45885), ('Ranked D', 45886), ('Ranked E', 45887), ('Ranked F', 45888), ('Ranked G', 45889), ('Ranked H', 45890), ('Ranked I', 45891), ('Ranked J', 45892), ('Ranked K', 45893), ('Ranked L', 45894), ('Ranked M', 52045), ('Ranked N', 52150), ('Ranked O', 52151), ('Ranked P', 52152), ('Ranked Q', 52153), ('Ranked R', 52154), ('Ranked S', 52155), ('Ranked T', 52156), ('Ranked U', 52157)]),
        ('especiales', [('Special 01A', 53555), ('Special A', 44179), ('Special G', 47672), ('Special H', 50228), ('Special I', 51713), ('Special J', 52142), ('Special K', 52143), ('Special L', 52144), ('Special M', 52145), ('Special O', 52147), ('Special P', 52148), ('Special Q', 52149), ('Special R', 52291), ('Special S', 52292), ('Special T', 52293), ('Special V', 52295), ('Special W', 53551), ('Special X', 53552), ('Special Y', 53553), ('Special Z', 53554)]),
    ],
}


# Íconos de los camuflajes (PNG 64x64 en base64)
CAMO_IMG = {
    'Gold': "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",
    'Diamond': "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",
    'Dark Spine': "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",
    'Dark Matter': "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",
    'Mystic Gold': "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",
    'Opal': "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",
    'Afterlife': "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",
    'Nebula': "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",
    'Gold Tiger': "iVBORw0KGgoAAAANSUhEUgAAAEAAAABACAIAAAAlC+aJAAAjyUlEQVR42jW6WZOe15EmlpnnnHf53m+tvQpAYScIcCclimqJGrWk1rSXtqZ7esIOO2Lsccy1w46wfeF7X9u+GDvsuXB3eJuInmlPj3txSxS1EBRJcQFBgNiBAlBVqPXb3/Usmb5A+x+cPE/mk/nkk3j7l//tJIdEh+Ek/5/+j6vDUQnBf++bJ/7ghy/8z//yxuOtEbP//R9/45/8o7enc4/aLK2u+Xpez+e9pdXPP/v6v//n/68HjRKU8H/9n/3RO7/zWlOWSonurJd5/V/9N//j/t6+iRUA+CAmMv/Jv//9v//7P6rrMs76CCQIGEXv/dWHf/onf3bpxXNLy4NPPr7mXH3l5Rf+i//yP0/bbe/mhHFdq3/23/0PO9u7+WzyvR/+7j/+p/8Re2ubwhXHVMyng07kmun62sI/+L1XEw2Bofam8kmRexHWWm2eGDRNcM5PZ/n4eOwaPj7Ymx3tv3h+4+zmqm9qhVBa/8VX98E3Ks6AIgjl0cHBdDTUitgzCinCuqo+/vxBZRutNaMW0mjS2Wj+wYcfUoRPd3Z/89HnQEgmeu31V9NuG4TBM6EfDg+Px0NAYYCs20ZgW9dEcdpdpqQ9YEAdRQj8rTcvXn7hRFHV3vPW3nxW2ACq3++c3RgEDnHSunV7//MvH5AxrU6fdRT3ei+9ehkFWAAJ724dzqbz4EvvahB77esn46IJSIgILIACLONRHgIE37C3iAikf/vxtfsPniqlbeOUVsz8woVz3/nu2yAMAoERVLK1dX80GgKB0rC8tAAIJmoTkEigTncBwYo2s/mMTPbNN15MEzqe1199vVuUhQ92adAyhqzjJEvvPNz98uZjAElTA2Bqh5df3IwSwyEQwHg8H89y8A2gAaEnD3eFGQA8QwBmhgDUare0wbzI2VugMDk6/uDqp8CAzEoRe9/vZP/oj/+d/tKiOA8oznoW3Nne8VWlgGIdG2WAUiRo8qN8uEsBJI0CMsRJmyWcOtE7sTJ49uz47v1nsTaI3OrEGKWAGkG8uK9uP773YE90TMpUhV3umv6g50NQiNY2tm4IPAcPtkIlIkETKEJAUIoQJYoNCnMQIALEqx9++nDridIUWJhFa/1Hf/xvX3r9ZfGCSCBgjJoNd7cfb7ngXQgqjpZWFwCQVMyILECImM9ztg68BV9E2MSRqipbWw8AiNooPeh1nPfB+cRER4ejn/7qK91abXUWWDg2cPr0hgAIgCABsE57qAyYuLfYESEfBICFGVgkuPXVQZy147RtjB4fHH5w9bfBBRAB4Kapv/nmle9+93VxNSACAAAGsbuP742OjgUphBBFUacdgzCLmDRDZaguZoQ6iTWKB24SE0ykBYlFAgszFHnTlKVWGKfZyspyFOkvv3r40W/vePaoOO10N0+tESIzd7JWmqqqzJkDxPHm2qIiCCICSEjIaHR09vQ6GGOShAx9/tnNnad72miR4Kx/+cq5n/zhD0hFKITgAQIQoFZ37zw6ODgmIvF+odvJWl0AQAJCHWUL1FTT2KjIUJq1mnLOwXbaifigEABEK5pMq6PhXLyzzr54abPba+dl9W/++oPd/aNWbMSWi71IKfKBe1maRaYpqqqcQzmOFACBooCkENGzXxz0X3v5PHhGgKZoPr92SwIb0p5DnMS/9/vfXVlfDUEDEoASIABSKn68fWgDizCLP3XmZLvX5eCJNKnUqIh8mR8fH83Kufe2rm0rS85uLrKIIIQQQLAsGvbsbRgPDwcdvdxvo/D29t77v/gMRKrxYbfFcRqxwOpyN21lnqXxCHFnOJ4Io7fOO+8DuxDOnl1bWu652pLI0fHk8fY+ahQRb91rr5y/fOVCXTUiAcALCAcHwq7m6bRAAEQBhLMXz1GkRRoQNoo1BhodDSezYjotZ+Oh9c7oeGWhp5PIeRFQgUPDktfexFESp/1eb3V5wVtvSH79wfV7dx8hcifBVkwiePLkoopiRGxsBQGf7oxBvLdeRAQYFb505YRS6JxTFI6ORvN5pUh5Dsaot995tT1YUjpVWkC8hIaAgeDo8HA2LgwRBOgvLF+8dBEACBBCLsgYdchZZ7TpdlpKEykMDOvL2VK3FYIgIoA470PwBFiWTVnVSUszBEV6Xtif/urL6bxQgpFWJo5Ob66Ib5QxvU736Hh0594TRAjASOyc21hdeuutVwRIgaU4sU0dnGNvffCLS8ubm6cAJI4NIQEgIQgHEPfo0cN5USetlgS+cG5zeXkJvANB8Y69Qw60tV96TyJRAK1RmyheXkpPrnWcCwisETi44BvSsQAFX3nnABSDEOHNr7ePZtwdLMVRdGpjcO7sRhBMNA7a0Z17Tx7vjkwcG2UQib28/eaVjfVlbkpFiMLtLAYWH3wIvDBY6Pe74N3z5gWgAMm7EOrm6aNt4SBoTNJ69bWXyETBWUBB3VJp9+jwiG5tTbNuGwCYsXF+b28/jtMLp1eBPQsKISGRNlFssiw1WlW1BUQRIcJ52Tw5yJN2u9vtfOP1092EJVhFGCR8+tnd4Bwyk1ESuN9vf/ubl8RaQWQRtrK6srSyMgjMAJJmcRxrCB4hBLY+OB+CNnp7Z+/OvS0d6bouLlxYf+nl86Gpmb2tpiEEW9V//q/+Nd17dHRUms5gOWv3kliBBNS6129prUSEGbrttDtYA6WB7XxeTmY5YuAQQNi5cHQ8a7ezjRNrr185GVwl3hPRrbvPPvrsYZxoQiBAa+3b77xx/oVTtslF0FrfWNvNkgsXzyALCiIIAQNiCE1TlQSKADg0n1z9ZHh8GJgVwbvvfqvd67G3wLaxJWHz87/926sffUHDaXH91gEDBQlp1hosLhpSpze6i4NWcN67sL7aX1xsl3WFCsrSDscVAgGLSCBSSws9Inj7zXPnz65R3GaT6Tj7+NMH02lOSjFIYGxn6Q+/+6KSWilyttaktI5VlL7x2gtRmjCHhYU+xQkQbW09e/p4GxWSaR0ejD779EtgDta99OKFN956FTBSOmLmTnfhxs37f/WXP4/ihJSOPvvs6+PDkaA2USzO+rqiUC8uRME7Y/S5MwuJssXkiHz95PH+bFoSqgDgmLNOevHMmrfVyfUsSRNAo40ZjvNPrz0yRgXnQKBpmjdeu/jCqWx++FSZhNEEVytjgnenTix1um1hWVpZFEXFbPrhb66DMvVsCOLu3L1/NBp7wcXFxX/3Jz/OskQYRFgR37px60/++Z/OZnNgptiY/cPRrXs7S4N+VTRFUczmuTZmY6XPzK2Yzqy1QVwniybj2S9/c6esLCIiKuvkwpmV85uDUFe+afKyKfJKEX59d2vv8NgoksAAGEXqd7/zokmSxiOQluB9cFVZVMUsjZWWoDSdWO0j8tWrn9+983DQbyGEuixv3LhVWw9K/f4f/ODSK68KGHG5SqPj0fx/+5M/23m2JwDCSMzsGD6+tpVPJ7acB8Dj4TAyeGJlgACnTy4sD1LnfGD59edbD3dHxhgBEOFEq99954U0BusaEBTsNKx9kP29I+ccCCuiurFvvXHh8oWNsg4mWwjeIgYRUYaUifM8n0zzhaXs7MnF4fbh3/zNVUKW4JSi4dFw++leU9dXXrr4nXffBkEiQ4ryyfzP/sVf7+0fpWlHkQIEApBIqyc7x3ce7KSdjiKDSpWN7XXiVjs9v9lDcM6FL28d/M0vb3MIShEANs6fPdV/5cUV3/jAEsexBoi0YYF+J0njxAsEAUX47tsXia23wegEgkRxh32J0LRb8f2Hu/PKfvP1F/uLy+//+sunO4drq4MojsvaP3p4b+fZ3tJi53fffSONI/EegJnMX//F337xxddJlBAhIipkYvZKwTyvH+3P6qaBYBf7C500abXwzMnBufUWSTOezH529c54XGqlBMQzKx19/53zGuqqKuIoOj46un37tuFmNh5fefniyY2B975x/vLlE2+8do7JgFYmjgUEtRHr6ulwMpn97JefrSx3v/+db4yOi08//UpHcUTMobHOPXy064L88PtvXtxc4sAAFmO8ee2rX//qN2R0QFQgCOy9JwHFgiHwnXvPgnXB1xBy35TtNP7hO5u9tuaA7/3yxu0722kSiUgIoWqaVy+feP3Vs42HoA2r6F/99bU7jw5iHRRCu9e5fPm0MCuS779zabC0qqLYB56OZwgBwXuIpuPRX/3tB1tPD37ykx+cOb85HI+GRyMFWJSWEDu93vHR8Mqlc+9++3VtMmaHipq8fv+9D+fzkhBEEI3x3i0uLxIAEJIx6tmz2e7umFlKyx6o10s2Ty4mWefBTv7R51tB2AUfRIQhi+O3X9tM0zRpL3az9iefP/jg43vdTAcJxCXZqtPOitqeXB9cvnB2Pm84eEIkBGfrsija/aW94+r/+csPv/ftV3/w7rcFVDvTSct453TUAoyDk26n9e53XldGAyHqDuj46db2nbtbqFTwgTBY63q93j/9J39EzIGQCDHPi+2DUVHZvKitY++cEDaq995HT/O8ighRiIQl8LfevHjh7KptgtHmyc7xv/zXV4HU5sk1RYgon3x+5+rHN5DlzVfPd1po66aqXXCctNtR3DWkSOHPr952tvnRD76hNM+me4N+6/TJDecCAilg5+bfeuP0mZML+XzugyVKQHj32X7V1CLsmZvGtePkP/7H//DyS5dIK83MhNQEabezweKiVgqZ0zjJ4vi9X965++hImZhBK0UssrTU+f43T/V67aPpbDor/s1Pr91/cri50V0YtLzw148m/+x/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",
    "King's Ransom": "iVBORw0KGgoAAAANSUhEUgAAAEAAAABACAIAAAAlC+aJAAAjuElEQVR42n16V69t13XeGLOtsvs+e5/ebm+8hWInRVGiZIuU1SzHsizYTl5iIAiQt/yQPBgIEMAIktiyI0GSrQpKpGhSpFjEy35567mn9933arONPJxLyRKMzKc159M31xhzzO/7xsSnJwKGKGToyFtnUErP0QByho9dmfzLv3q8Wo8JVJYM//577/7ol1vGWxVIa60u7LGp+K+/cf+nvviF0aBrxgNABB7owvg0/d4/v/njNzbJeQALjFFW/Ps/vvC1rz+d5y7NMgB0liZP35/urf73v/nei2+uChUEYeSczbK0VlLf+OOHPvnJK0JGjhzZ9Nrbd37x/K39zUNldSB4qKQtLKKoTU7yU9WICQ5AXDAuBRPSAW+3q597Yv6ZZ8+VKzF4pxR/6bU7//zC6iAtgkAyYAgMGXSGSZaaxbbQWcHjmhBK54WxTpaiqclaZ6+7sz/knDEUnzxX/fo3PofIPSoHMizVGDk92Pr5C2//4IWbxJlSgSfPEDnycZoPusNjixONiaonIg+t6eaxxYZAPOxm41R7BHBOWzsa9PhyNSYEi0DIPDIRBOdOTXz5meWnPnsmCqM8TUqV0t3V/b/97rWV/XEcKs6ELiwy4Ip7R+t7SZm7+y4uO/DpqL9w7kFbZEU6jEqlE8emup18b390fjH4j//hM7XWRG5Mc+m+QHA96kaV8q2PVv72W6/3ExPHMQIBMAdcBgrIHXTTZJyeOtWOSmURlp1Na63KsWPt6clanrth5lOHFgi54MdaDQzDsBTUJ2pLC7Url+pf+MPlU6emrAMRhORpOBz9n3/68K2PuoESkqtcGweE5BGQCemsXdsezDbD5aUZ56zNk9bc4rjXzfOiVo3OnJgO3OBrf3T//OmT48Gw2p5nIhhs3Qjj6t7e7v/8u1fubAzCOEREZ20QRQxZUdggCLwzu/vDSNLx5WkVhhPz5/Ik8Z5a07WFhUoYUaOuJifKUVnxP/n0yfPn2g9cbFw817xysfHQJ9rlcuScaC8cK/JRlox++vz1n72+5zypIMytcc4TOAAkIi4E52yU6r2d/tJiuTXdzge9sFIt1SeS/gFyHoTiEw9frLVbuWVCsPr86cPVDzlHcuY73331pV9vKCW5ks7qMCxPTs8EYZDnGTKSQuRFsbfbn23GU1MN6ygbJl4nxERYn1g+NXvm/MLsXGthqc7/23994NKZ+plTEzPTYbVWAh6iCAtNhSnycf/Nd9a///JOb2RDxQ2Qto4BIJEHAkAkEEIgUneQmzw7s9SKyyWni6BUdkUSCE6cz114ZP3GNSbCIs91MqAiFYK9+qsP//En7xvnpQrIeURstmdOnj7faNTH42GeJlJI8jRKi353eOpEqxTz4cGOLbLW8tmkf9A/2Dn+yBfmLj7WnKry//Ln5+NIlivlPC92OimTgQcYpbnkbHOz870X1m7vFpIDE8JYR+SRPAABeABkiBwZcCTE/b2kFuKZ88cBYLC3HUqpBC+KbO3dN6NKxRUFkHPWlBsTd1fW/9e339jp6EgJAOY9hWGlNT1dqlYFR/JOp3mhUyEUgesNc5OlFy4cb05No1BIVnAsNyZcOhxuX9/b3BZ/863r1ZhPNYKF6Wh+oQ42KzJTKdUYk/2BThIMGJdKGAvOEQIROAREYESeCD2RkAp8XmhYWdtPxnl7dkoJQk+HB4OXX3h748bO5cdPnX/gfBgJFME4LdIks9rGgRIMPXkPnklOCFmexkEYRWUmmCNPjBCYYDQepVluSlWUUgB5Z/3mytbdlY2bd3Y63ZwPRvDR2ujtO4N37wxW14dem4l6SK7ItavVa3vbhwdDZ61DZJ6IEIEIAQERETiyIAiN1UbbRsS/+qWLzUaYj/pK4urN1R9++40P3uv0D9KPPtjMkvHcQlMpNIVutSf1eLCyNbSeALl3ZJxmjCkVWeN2ttYH3Q550IUmbyfK/ItfuNJsROkoCZS6c+PuP/3gtR/89Oqrb6+tbQ12u2M+OVFrNRsijPYOk4297NraoNvL2tVw+fjM4skTAWbr253OwDLGAdGTBwAAB8gAhRKSC1bkhZLw+cfbf/LNr9an55L+zusvvvvcj6/v7/rAO18kWpu7K3sHO4NKSS6eOj534bGAkp31za3DTAUxQyiM1oXRRXHY2R8Oet5bAu+dizh99onjn3rqIWt9FKpfvPD23333jQ9v7GTacSGEFJJzPj1Vj6JA8CBNRpxjUdiVnXS7k7Sq6szpxbgkfZ5u7mWj1AaRNM57TwgMkAGyIAgLnVlrHzxT/6u/+MMTlx9e/+DXP/3Oq6+8tO20UuBMvyetAyRA3Nke3L217Yr+4on5uTMXpN7fWN3f7xVRqAjRGu2NdUXhXcEFs9YxDw+cbn7xy08xFGGknvv529/50XuDcY4MCUBwQZ44l7xWDsbjcZKOhJTOESJyRnuHxUEnn24pAjfdqgqgW+s960lJpZ0DAECKogDI5Ul+crb851+9/4lnnl2/8f6P/+4nb7zZkSzAPKFhvylRAzPWIoJgfJyYrc1OHGQnrlxuzSwWh2s37x7k2kZh5Ix2znnvmWDeOWv80lT49T99uFqJnbPvXdv+1vdfzwoNQPVms1Kpe4KwVKpNTPJaRREQIAIBA04IgIiA3UHSLMn52RYPwsWpUr83WN9JBZecobNWyogB5klSjvmf/uHxL/67r1idv/i9H/3qtUM9LjBPXZ5NSNGQSlufOMcIHSFnOM5MvztqN+XxK4+VI9bbWru7M2KMCxVpY5Ez8N4VbqIEX/nCxQtXTo96h1xG3//hW6ubPan4wrFjs4vHRsMkLsXTs4uzc4u8UQkBgYg8ecR7JZ4xpo3LMvPUJ++TkSpVyq0yrm32OiMXhoElJxjkWYHePXHfxJ9985nZ5VO/+skPn//Z7d5hDqOB10UoVFPIqmSFd9qTAzJABIQMBr0sHw+PnZg4fvnRkPpbG/t7nSyKIkDurdHGhIIevzL96c8/FkQTzcnJax+uPveLD431SslqtbG7tVVvNk6dPX/2wqWZ+QXeqIYAAAgAAICCMwAi5wEAga5cWjxxctbqPIjCUPg7qwdRrVWv1nuHe965U3PRX/zJw/c/9dnrv375p9997e6a8cnQF3kUBqVQlSU7zIrDQlvCULLMk0NAAO/x8DBhND5z5cz0yQsi3727ejAcFXEc5nkG1p5brn7ta5+q1BuowkjQtfdXXr26yhh677ud7uLxU09++nMnzpydmpluTEzwRi28h54AAJRUQOS9J++b1ehTj5yMQyfIMSXbE6Vxt7++PRJh6bDXb1XE1585dfnKqWGv+9x3f/7Bh5lJjRkNAykr1VI9UEEoUkM6t3EpqkTSeCic8wSAaIw/3O2Xy7R86mS5xKUe31jpFADO+5kKfPnZ+0+ePxOWq+NBNwqjzc29q++te2BAHpiIy5V6oyG4dM5aa3mjci8CBCSFYMi1scjAEx1faD79yAICRQqHg56QYrZd3drqr2x1AewfPbn0xINLncPB3sb6L19aHw7RjvvMu0ajCoix4EzyQIXoMY6lAUQER6C9RwDGME1smiWLC5HRtLDYHg/7G9tZwNwfPHniqWefGo8GpTgGpkye6yz96ObeMLWA6DyNh4NO56B7cDga9Dud7r0IEBAyDFVojEGOnDEi/8TlhYfO18Bl3BeSQaNRn12Yldzv7Y8W28HXnjk7Goy1NTsbnbfe2vdZgTpvViNUEoGaUcgJB4M0LzQhae8ceeCCgKxzAICIeZotnmirgEf16vx0bXd9f66pvv7NZ+dPn3PFCIBJToSyXq/tb+/f2ejJIGAIHigv8n6vt7e/u7O5zhvVkCFjyJRUDLi1Bjl6C82y/NxDUxdONvd2969f2719s7t6Z8s7PTvfCnhx/kRjaqrGGEOyb7y6ur0+QGujMAhLQVKYmpI1KTsHo4POyBhD1oeMG0JNJCQnojBQzjmdm3I1OPfA6aKwzXarXYNzZ2cb9crVf3nl6ms33n3rxs7aWmOiOX18uSLz1fV+p5cIwTx5BojgjdUmz/n0RI0jB0Qk0EYDerIUKvGpK82nH5leX9/7px+v/PL1ztUPDj74qH/99natph5+6KwUTskwjNX67c03X9stBgUKUNVQBKEu9LSS3cPRQT9BBI7ovUfnFVcGQTOKo6BSjdOsMNYZXZy+sNSeWyTwM0vLlVLp599//tvfe/ed9zZW7uzdurGzcePG5HRl+dzpVi1Y3egdDoYMPSIBoiNPyPjcZBOAGGPeO08AwKbr4ZOXG08/ONmsqeeeX7u95oDHkVSIuLU/7vaSc/ctT063y+Wof7B/4/3t69f6zlohZaNZVUpiaopBMhiPETkAECBDdEBoXCCURU4cRcAAIM+M1qbZjE+cP12uNfP+zrV3PvrhD9/t97JKXC5JTtbuH4xNln7i009Nt6Ol+UZ/mA0GiXeeEDmXSMDLkUJkQkjvXLMa3Xd84g8eaj10rjQz3RiM6V9+casooI6sPko4kpes3x0dP9E+cWpxOOge7uy//srWwV7CAWQpqlRirQ3mOh2OEQUAHpXnI/LtyHtnVRgYRpxLKUWeFUY7ju7UxfkwLoeSrr7x4dVfb5aEjJxTOmMCnfNK4uJilZGdWZo8f2Zhtj3Ng1KWaas1914cX2yXoqAa4kTMFqdxeTacbIRWG22sZ/HC/OSd1UHgLTdFFMSobVyKFPP7G3eM89vrB7sHGXmHAkuxAiIFzFjrvRXCESEAB+BHNdoDgiVuTKCkNSaMVRjIceo21g7Wrq+VyxVUfHlpqdm8C7krMbAFWe8E55NTrYD5SqNRZFoy+8ijxy/fN7m+NrN+d3c4TMV/+tK85MiFLgXAEZJcJ4WPwygQaLmcnp3Y2Mq18Xm93s+yQZIuNquC2TQvlAjuro1Gw4IBcSUDxY5Umsk1EAAREAHSvQ0AAJAnMs5FnlvnnOVhpNI0Hw/NjQ/unLtyPnN+aroxN9u88eGGqsYsjmxWGOtLMaBixnmt3SjJz198SvCgNXvjvovdwpKohKOAMULuNBFSILBcEqWIWwftOg6PRasrpd0D26OU4nBpuvzYAxONGgaCZUnW7VrSTnAupQRAB4SWtNYA4B0AAXIC1AAAIAEYgPXGCq/KSB3thZBSClPY7u7Am0KWy2Gz+sxXP1EuBWt3D3Jrokbp7Gzryc8/vHTmfOdgr1INm82a69whGbSWT7q8uP3mi0Iwpkrq/Rv7IWeNWrg/8v20QGSViLXK/TQ3Dz0ykWscpgTeVEpmcb4cB2GrUb1+sDEaZkSkhFBSMAaewBbaWycADAEACAeMeQIANIgIyMA65hznKKw3nKlIaW0Hg2zQGxybXbQ6OX56bnamdbjdOez2jRlPT9YYh1/9y2s7u92Ng3FaWMGIoz+51HrgwSvWGTHKrBOqXVe7fXruzWJjKLVB653zeeRNq4JLk+74BB1fbFy8cDYZdvYHY1KCyCKydFwwIhSMcSSPwNDnBXlwDI6EMweAIwmEHhgCMiCfGpOwgAg8EEcEhCLT+Wjos2GhtQfHysG5xy53Nu68e/Wdl97qbA5h9SB3JHPgxJlgaJx79fadtz/a+atvPCMGSToc59bhi7fgzrhSIDLFACjPKXXY6Zgb+2klYGenDyCoXjk3bYMqj1QyGmTjIk+JAwKDIFDOMUbgC+0+xswBPAA7KkYEREjoibyx3ofovUNgyBAB0kSnaZKNu9s7h+35mVF3Pxb8rXfuPP/2cH3ANUgRxoacA2CCOwRyZpjFb66n7B+fE+1m0xTpyzfN3TT2ocq11s4yACY4E5wpRpnuGffmBt38+w++8tDulz57QRuWF35/t+M9MI6CM0+UZXlZBaYwR9TwCLcHsHBvSuTRAyJ468F5y4g7RoiMsSJ33c6Iq6DemtDDXoD4D//3hefeH+SgMFbEZApGew8A5AiAOAMWlSzB9QMjrGeOqev7pusRnLVExMB4YsCBLBPISxF3Djz1Nf/fL+6Ocnj2M2eKUT8ZF0AE6ImhJZcUOvTgnP0NN3cAHMB9/E0EHAA9IPdo0XESzjOODJk3tt8dMQa1euXuzd2fv3LnhZtpoUosVISu8JrIeyIkYMAQwZMHDshFZg0rl2IiRSi08UflD8kROU2WyAGRBesC4ThYsEbIf359//bK7onlNhBniAwEWTDaM8Z1XnjnEO/dXPAx+ntSA8ATeAByniEILj0w54EhI6I8sR6Ec1aosO8rBQguwHpvPPPOe0fgkQgceeu99YDeAhBDZIyXZmenHzk/75EcokeGyAXjijHkgoCHQSg9oPeCK0Hw4PG4HLthTvV6SUpGZLlkXEpHDgJ1RB/+/4OIHEdAEkicgSUnJKtV4mQ0DKPK3Oz0X3zh8qOn51hmlHXCe8mEZALxyI4CQAAGDMEbP9maZKnzGsSFE5PLjbgshWAIAIjAuQhVWCuXBAHmBRUuBv/5S7UvPVRV+WB747DeqnMmPDFnHAcvGUOGJIV3RwIbHbF/Cz14LpCJo6n3SI44x1JVkk8P9vdSg7NzE//5zx76wqOneaHtYCysjjhGggdCciY5EyETyjO0Lii6QgpvdFGpVJ48237rVnfb8cKiYmKm1axUSndvrIy6A8XYucn4kyfZpeMhcqFQxbUAgIWhKAZEjhBJhQgepZQ2L4gAgTgSAHgChr+zByY4IQGBA+a9JyIhpApUKFVmTSmWG7dvzi7N/eWzZ+4/M/uDl65fWz/IswSlkEooIaXg5M14nM6E9KmLLeGyRFXb0g4+c6bsCqd2srX9HpA/3NnvrKVVqS6cap6ZgnOTbG5SLi21+wkRxtoZMR5KSUBgnUNAjlwDCcF/L4cQf3/KhDDoPHnFmbfeWQoCgS7Px5ZHkStGcwvTs4vLnigM9i6cfuzWxvjdWwe3V/f7o/Eo09boSqQuL1ceO1O5eGlBkEl8SsCjaok9cx6fvri4ddDsdA4jQY2o7HRajQwXMBikq1v89uZ4YXFueq7khocmHUYxRyRmvck8Me7IyUAyYN753yLmHwtuvLcDLzmB50hggSwhkFSi3Kw4NKOD4d3ucDwu2MtXl06dvPTQI2LUOb/k7zt2vD+eKzKTJLrwgF43QirXy2leiCDwzo68h6QP5ZjFtBZW3Nk6OpNZUwTlSojylaub73+YbGxliXGl+M4Dn1j4xjc/2WzbcnmdcUHG60KrSsy0ZQKQM689w49B/8Z1OhqcAQNyxITwzpks44hMYnOylWXZP3z71ZWVcZHYUGKt8uvPPnP7M3/0ZP9wp96erpUkxBxaETJIR+MsLVZurzZbk/zP/2A24LxUigeDdH3roNqsh4qKtOeIRrkZje323ujlXw129gFJOOMHY/3Rjb2kMCdOz3U2hpt3ewyc41QuB2QdIrjCOm05gmeIAIDgkQECAhAhlxIDCYBMCp1rm+fAxcX7F5oT/CfPXXv9ascbCLhE4EniN+5u1Rt8ZrrBVeCcYwwVp5WbK/1BGoXh7OysBeSVKFjdSnuDfHa6NDvfTDWXQVmV4/EgK9cm8mz87nv7K6s6lKrEhXKOvM0d9LqjixdmK+X4xofboDUwLiPlPRiPzHmTamQICPjxfydARABCUAEFghhywXRhtXblavzYkyf6w8FrVw+SYd4IVF0I7qx1LkkL8PrM2ale92DQG7Ta9XQ4cNbEldLu1uHPnnv9hZeuip9fHRFQIAbzvzq8/1zzqUfPiIrSGFAJs3FXKVUu12y6zsDYwnhrg1AJspLx4WFnfro2vdDYuFagA51pWQrHw6wsJDD0RPxj9IzIIxARMhSSWQBk6ImAHBDMzVaa07GxocItYUk5KkZ9ZMiFIOCArNfrijCMA7l2+04Yqa2d7i9eevWjld72kJz3vFkvIYjc2M7YrmyMbtzeLIVsaqopFYLTQVRrTc6t3DhgFmu1soxU6m1i/fKxicsXGvVmOU38+so+eecQZaTAAxqKldR5gb8hFfwofxiXCgLlOXAlrHY601LKSw8uHD83u7A4v7eX7G6Nq3FQqtaIYaa1DNXpsxPL8+V2uzrKDZJ/680b3/rRjXfu5P2cPCAC8FpFIRFjjAEYgoOhuXm3K9GeWJ6RYYWHpTCORkPX64xIiME4S40LYnHmZNyoU605HZei1Vv72bAARC6YQsytqZXroQyKPCMk5EAEjFDIwEnhA0AEYGhTrXM9O9u4/4kl4/JavVIul2/d2hnn1nssjCHEVju4eHmiVOKm0MyZV1+7850XdjZ7nnGUnItAluKINyrhkdPCpXTecuBpjhs7vbKi+fmm9UxImJquglSZgSCSU1Pli5caJ46FUmKpFNaa9e7ucGOzIxCdcUVhQAoEXq02QhHkaeKBGComQ8MBBILkeWag8N46B3jlwcWlE2Ec8cbkVLXVXFieCaMKKV6fqpw803r8sYXF+WpnkIRB8NrbOz98Za+bkBKSCEWoGs2JaqnEG9UwCINAcufJOY8AnGOiaf9gON2oTjSF96wS0fJS6b7zk8cWxKmTfKolnDOlUlSrt3gYMOC3bhyUeMh1keQ5MYyCQPFARmEcRjbLiYuMM48InBlnoSjAGwAsN6MHHp0LQqOCSOeF93bh2NTZiwtnzk1dvG/6zMlSeyI87AyikK+sDX7wy4OdgZOcyDrnXSCZ1Xpv94BP1itEIAQJwZz15I9McBpkLk/HZ4+3K+XA5SPyllPGMEVwSWoL47XW2zt7Mqo027XBQdLZ7jNjGUBuNEc+Ua4bBlLJGmMdU1jkiNx5a03BwCFjDmBhobFwqopguoeDzuHB5uaW96JcrUaBVpipgBfJMM2KUWJ//vrBjZ1coPeOrPdcAAPUeUFMsCCMOfIk8Vlu8eOaBwRA+MGdwZtXVxg5o02RpUTWO5+kfucwETIqLH/v5s5HH92sVIOHnjhZbkVOCsV4CCIZjci5uoqUthURTMURB8+AnNXoHSPuQYSxWjpZK4Ws202Gabpw+hyLWj/58S+6B/ulUoXJEFggwxiA3rs5uL42JnLOk/fEGTCGhXbeO/SWjZNEcFGt1jhTdFSuCcgDI8g0vPHe/uH+QEVlZ5k1BsFFEZ9q18rlalQqO0cTk1MeaPJY89NfejhqlUmKCBnzvjvsuTwNrPEAk3GlyoQ3BXrHQTgmPIfzlyZPn29wNNPzM489/fTs1FT/oIcikCE3OpXMr9y4vbq6NRzpD24PRplnwKxHQBAMkRCBQEgQyBux1EZbZ5WSQXCvOXDv4kdIczdZlwtzLYeQFwWAM0bHYTh/7EQyGkqfLy1OgxsDl5PzbXJ0sNe32gvvkVEoJSBYgMMsT7LMkycApoRBPH+p/eCj03HEoppqTrQr1Vp3d3s8Gp04e+7kiVlXDDr7nWzY847ev91/88bQeE7giIghE0wAY8TAeSQC3qhEiOi9s8Y4R0JyztE6DwAMQRtiQOcWYxVI61E7d3jQQyCdp8zmSwvNKPCSM2sZCjW1MJVlemurG8qQW0sEPFajPNs+7AF6jwiCFd4fO1l78OF2WGKTU1MzC5NSBK4wltjcseWFhWkZsCwZr1y7KQTLM/vye4PNQw8IQI4hBEoi44Ujd9QIBxQfs1wEQmstcirHAhDy3CEQAq7vjkbjvNmMFA92d7vW+UKborPXbpS4kAwZD+ox8CLrOacf+uTSsD+68/62IJGkWeYdeS8YMck1oPOwfKL28OPTc3NRaiCuVPJCcVmOSqrU5Nq7PE8pwUEnYYyRd+PU7PU0gGXAAbkUGClKC+s98Y+bYrxRjn6Hu3svFJOSO+M8IQAZS0szpcWZiJEbD/pplnPOJOf9sV3dy2+tpZv7eV4UtUZjosZ0Pj5+/mRhaGe7y5FbY7W2TPICyTK8/4HZRx+fObZcPrbYTFK6dXdw9fru9ZX9vd0Ooq9Vy+DBaRMI2x/0Gfrr68m7K+PcWM4ZAIYKEVmuAem3IkPco7wfD09gDYUhSMV9bgihsLS5OwDbSvPCAQBj2vqVLfvubbPV07mxANuS8xOzq1/+/KXzS9XBcPszX7l/Zn7qlz97J98bKc4zskLig4/OX/nEdKsOAYcfvrD+ynvDu3t5qjWBD6VamLz12ceOP/HYWcaJKaWiqBgODro6yRFIElEoQDDMLVj/W8/mKALB72hWQECmBGfIjCUA8gSTDXHpeLXbG4/SFInubLhfvJ+tHRSFJS4UMDlK7U4nvf7RxuJiuz1RBsTFY+25pdm9zqhzOKxNBk99bvnMuYojX4nky+/sfu+l7t3dtCDmPLPEPPDDvrlx+zCS/tzxiWF3v9frW+3evVtsHFiGFHAIJAfGC0Pak0MkAHvk3DTK4W99D7ynQKTgknNjrXdkCVpVed9yECoaJsV+31694zc6nnOQUslAIYEpCiIY5L7XHZ1eiGw64Dyst6PFk1OVqjx+MpybC5x3B91ka3f04nvj9Y5ljAspAqmYEM5bT9540e+nrbJvV23AfXeg31spdnoFoFMcGROEMrXe/aalSgAI7F///KNUIk/GEAI/2gwSGEvDVOfaOoKdQ7vdKZhAlAqlKHRuyUolAYAB3l7rbe90Ap5500vSrFLh912K2y3qDYalOGw3g71+vrOvgUBIJqXiQgghAxkKYAzdxkH6zrUtXxgOOM5tVhQAhAjEmAPSxpLzgjwn+k1vW/wbzgcAEcFv2TAAwiizgKgkAxTjLGGIsSwnOh8nY85kGCgGZL03Dra2RzMNrvO+gD4DNt0UI1WpRs27G9uz7RIQJNo562UogNx4nJLzUSkKA55mqSbsj4uDYaY4SM6QSUSDQEgIwOjIHEbwR+CICFH8rneGAMQQCNB7R0QACEgcCJ13lpq10nxbhTIz3murA85dGCJy8gSInnCmValUosPBqFrOkxwiwXfF7NT8IhOMIfr88MRCs1LKi7F1nivJolJkrGeMmbxwwOJYTbUruTYiwoBDLRJI4AkdASdQghfWW/BH6BEICH7Pe0IAhkwwBoU1zvt7Sww8kpBBGJYWj83OTFW19UxKqVQ5qoRBaI0hIgKaqHEhwToyBRVFcW3N/I9/fPe5F9/3RFNzc1FjqjlRPb3U5MijchWAxUFYKZe1tZYQkJdCFgdIgCIMhWJhgEdGjCdg3EvuOb+XUwh05BWIf1VF772EQ4YAUBjnj1KNUbPGC2NyG4mgPFVvPHKFNje77daMEHz97goyxgVLsqIWyWPTzNssI4wU3N2jF98f7vb0zuEK5/DsZy4DxjOz5U89FN9c7VnrEPhwOISjJ6vAONpjU6IRuzT1QRjGkShFDJCQkAidR8m95KywFogA7j0d441a+HsxkJwDsCM2YRyVI/no+UqkXJoXExOtQAaT7Uq9Ut/cOugNxsM0L4wHZPPt6PMPtpamWZabOOSjzD//jt7tFRzIera+PZhrBZFiwOTybHWyNbm20UlSXRhfGMOQ1UrBU5ebD5+L4xCSTBe5mW+VB2P7wVpivBdcAiBnyJkojCMAIAYIQCiAPjYPEMADY4wxZr0jT4jgCdq1UqRQa1+uxoDOeqM4PPVw+/yZxspmsrPfCxlr1nkzTpplu3c49uC1pV9f1+v7SSAlorDO7Q3Md5//6K//9PK4txOFy5fONWZnH9s89Nv73XTYb09UZ6t2qpoXRbZ3OJhuV+Ioyo2dacp6SewNDKAnEMZhKEFynhsL5IExIOCNau3oRAARQ8659N5ba+FozeMTlyfnWz7NNGNxo1HjHMFZBi4OzVTFXDlZPz0vZ8qpYpk21hAUud4f4ms3DDkEDtrqo2B3h0U9chdPTyTJgJgoKZqZFOePx/dfnG9FI2H2ueB5oclZwVBFYZHbSiVc3bFb3QKJhAy44N55BDI2B6Sj/OeNWhmAyHPJRa1Ws1YXujg6O9ZRtaIev1D2PueMcQSEfNg/NEU6GvTAUTLYLtKRKDUGwyRLUiGEsTQcm2ur5u5+HgWBttpaxwA5skI7U7jLx8oSMpQKWZiPemnndrdrKo1JB2SIlWuT5UpFqHDQHZQiVS4HjIsPbo+sJ0AKwvCI6UuprAVPHgF4o1rmiFGlXK/VEP1oND463ohgHJ1ebJxcQG2KOOT1irTWKQXWOEZ+2B9ubugPPhwNu+nSiTnjzUF3rLXuJv7dFaMNI3TaaAQkIOSMgIyh+QlRjWGgfb/f311fW90Yv/769sbK4eTcTHtxnjFXqdbjUtnrBMFGkVICP1pNuok5CmMYBd5Ro1IL49C4gpz5f/aKRb+4OrRiAAAAAElFTkSuQmCC",
    'Catalyst': "iVBORw0KGgoAAAANSUhEUgAAAEAAAABACAIAAAAlC+aJAAAdWElEQVR42nV66ZNt13XXb621h3POvbe73yQ9PSu2HCsecPCUSpxACB4gSQUwEAeK8IUq4O8J/wRfKFKBKqqgCAlQSRgqtuPYchTLiiVZsqWnN/Vw7z3D3nutxYfTT1agOB+6um7frrPHtX4TfezFD83TvLTi5u4gAhwATM3hu5MzYapqS6llWQgwX/8OAGDAICxCDlhr6IZhsx3GaRqPIxMZqVAEICQcOUiYx3le5m7ozk7OhmHIKbjVkPs8DPNhmqYJAftpPH9yefjyz2zncvsbf/5Tn/jYL33xy//oH/8mKYEAAvT6/e4uw2ZoVZeqDpDDCSB2BGNWGLPkFM38OE7uIIAJT+eI9TeGgwTE5gY3YS5zgSuImWR9DQunLtVW5mWOKZ7sttshn904NWjfDZ/5zGf/wVe+8mu/+stf+OKXHjx48MbrrwfyJXB78fn4xjunfa/ge8994O6zd1ttxAQGCM7ODGbhqmbqaqiOqqgKcid3gpTazCWmGGO4nj1ABCYAgK3TYGYnczdvatO8NFPiQERC6/fQWpv3x+U4MfNmO/RdOj29UcxKrU5scAmx35x87OMf/5f/4p+/8Pzzfd/3bz5w8/L8s+++82iejt/77svMElIE4OamJpAn5xeSQq6tYX0TAQQiZwIRA6SmKYTtMLhQWcq6Cf6+U0SAiDBx06ZufdcTyB0gkBvBCQ4wM7s7EefcnWy3u2Fg4ePhMI3lZLu9dfvm7Tt3zm7eZObtbvvtb790/+FDPRznPuPOmbz6Vsr98TBthqHruyAcRLq+H4/jb/2r3wq1qjAZw/3HY4K7Ezkc7rVVNcqpCzI2a/bjLwKAiBCTKYpqn1LK0dQBVTcCGUBEBHJ3MwVRCEEkIITj8TgdDhTyuiLLsizzjNPTLnef+fSnv/XSS5vNcPX9H9YvfU5Pu4fvvPPMM8/929/57Z/44L1NNwSJH/noR77+9W/88de+JptNxwwjEBAIdH3ACMQEdzfAYxBrOk+LmgVmIl8nwcwsAmApi7Cc7HY5pdoWbQXuALOwg+DGcIaYOYhiDArb7U4YIKLNbnfnzjPP3bsrTCEmUxuG4Y+//rXjstjVtNy7HSK37795/0c/rMfjfDw+ePjo0aPHf/KNr333le/GmEMkOEEABpgIgF+vsQPEIG3Waq2qVRscxOTmYAoSmBhAqQWE7XYTU3Cz9f9UjUjZ4E7k6gQiIVCtdalLbfXZW88Od7rz8wt3evzw8Q/f+AFZA3GK+Tvf+XbTWmvj1qyUx1/4dPfsDb48ProaX3nwZrycu6JRW4rp/HKS7aYjgAEiOOj6CAHuICZyaw6QNDV3Z15PBROui5E1VdW+77d9slanUlLO41JU3YGm7m4OMAdiYUZTZVAIwsQhRQXFEEMI7n56dnbz5s3Ly8t//zu/XeZy/uR8Hg/cpVxdHlzWofNnb9aPPL+8eG984e703M2ryMs2BfylquhOZE5wODMR1BpJBIxgMTAT3NEMtN5yN7jnnIch9126OpoIT+PYqq6bSXy9oeYu7EQCtFJr7uI4HZ69c+MwHg6HZqoSJXS5lOm//O5/vrg8HK4ux3GUnHf3r9L+B+y0vPKjuS0UeOnz8uxtz6m+8Fz79E/K6e7E3d4rQWtFdzciqHpV67t+yJlh7M5ETGupYlnHT55S7nIXgjTTudRpmvlp9QRfLw4R0fqhQF0DB3I7O7t195lnHz18l5li6p48efDSt779F3/x2jiNDx8+IJZhu+mHTUqx2/XD7iSd7GJKPJfNfko/fISXv8/3L6QbejMjrC0M7g4wcXTz0moOebfdibBqqUZGazWEXJ80d2sG5JTdfZ7KvCx/qUr5052FExET83o9QCHI4ThxkNyl07ObJyenb7/1ztvv3i/a3n3nHXbvh+2m33Qx3bl186QfdkOv42ilMpBy3904cYZ9/+3gBgU5nF0McHNhgnutLYhsd32IovOs1RlOTzu4AeoEVyJYq60tJF0zIwIzm9n7sQbeWxoCEzNRVa3NxvHR/Yf3u5RCTIEjEQx2HA9q1ndD3/U5pjs3b2k1I79146RLeZrmVuv+eHj4+FEwhL4LRMRguAJwkAiJ+1KqEza7bc6d2bJYcSGt9b37vQ7KiAFWaGkaIrZ9d1WLvg8rwX4MWogpSGjWHO5uSylwTiE5aJmXxReHw83cYsqbYeiT3Lp95qRzWcrhME2Tw2OMXe76oc/7tH9ywfDg5GwgIoW7o5o3hwPDputzcLNlKVrVXd/XvkBYu+26wlaWmlLrIhNRs7Wp/KWHwTHEmOO8n7VqiomJAFOHuwuvkMqaGgnnmFnk9OyGpHS4uqzT0hTHps6IUeZxXEp1dXeSGENIMbiTu7oZRM0dFnLe9F1kWkolGIjc/P2DaoABsm4aBVVttTZJqYvNzPR9aINB7hJD36dlWVprgUPX5RiZ4EtVEMzczdUIYDeoamtqbvM4VbVxWbpuMDMmLqXWUlpVVWURFgkRTgwyELG5E6M6BaIAipIatVlhT8ENHL7eTAeRww3E7OuVqdFCjrmKLVbgLsQGwMBMm80A0HgYHRi2Q86J2QGOvgCkpBDuhzhP87RM1Uqscjwenrv3/DSNRZsvM8yM3B1u3kozU7fmQoHd4DAnEBHcXKFo3lrUospMtSqvZ5kEcJi9D1RfT4xFWm3NzMHX+If4miY4ct8JyeXFlZoPmyF3OecUU2il1VLMiUnMrNSFA0slb01DnZdKxORk1ZY2m8HRiMidVNXN4W5ust0N5kwAkRugSubWCBwCGDArpbo7Ma8tby0moOs5OcBM6mitBQm11VbrCnLcHEBMMcV4nMZ5nvuu3+12fd/1254M87w4KOes7mZqagCRe2vKEs2NhXI/HI/HdQzr0TRzNTWzlLOIyGazdQfcHa4Go7V4GMG7lAOLu9fmTAxvcH+vR60Qg5mZqJTKIjEEtet+5ysYhJv6UpdSlhzTbrvt+27Y9GZapmkpVSSAoaRrSTBXBzU1Zwos7i3FWEqd5nmFJO5uZtY0Bu43wzzPvFY5AxQCZnKASACrqtWJQ9f3IDc3OPwpqXEnATMRMZXWAPSpE74mMAZzwGmdH7u1wNIPm6HPQ5/NMY/jMk8iYCYYXN3hBgecGCKi2hxeFgMkpuiq7g53qLkZETZDrksZx6NstwmkIIM/BXIMYlJVZpEUmrdSqzWFw8BrcTESJgZRa02bDv2QU3YAtjJrAYHA7u6qDguS+tx3XUpdujqOrakqnKhpg0Nda6vXTIiZAa/KREIMVwoswilnFiYhMPVdR0yXVwfTFoAEFMBBCichYvcGVnAppdNc5sWbEbM5aKUCLMLs7qraastDTjmlwEvV5u7uvoJVcoKDRcxrraXVaaY8dOw0zYtIcGtk7jCGMcHU3FyIIFIItdYQw5Mn56yFjUyEwBwCByb4fj/WWnPfBQEUCe6gCnJzcagwCYuilVq0wtfm6SbMcDAxgVS1WUt96vs+hbCutMIbjNwFRGB1AjtzsLksbcnK02Hqu24eDyA4KIZwmI4SRDi6VRImYm2Nmca/9snxIx9AKXS5j+9eyX5yc7nc83G2qVUtXZTddgjXQJQISEBTb4TgZmY1hOCqhMaR2R1gg6u6qsLRtMUQh9ynENh1aQXg1to1HyKPbgEwBAkSk9rSWvRpmnKXg3BVc6C5x5jNHICAiNmF22GePvvi/It/dfedN/x8XzuZn7uBT3xQT7YEo+aWEo/j7j99M9UWVhLDcEdTA4OIfSkG877LSdKChVsFoSlAHATkru5JUu5ySh3M1Ilzvnxycd0YgLU4kAg7SRDTsJRSagshzfPCMZEurZmSroKAN4s5soTxYj99+N74pc9tXnv31ktv1f242GLToin5ZnCGg8onPlR+5bP8jTfohw9kuxlWOQvkBBHhalaqdl3edvm9bmWAEwtBiFSh2kKMXZ+DuKmT8OXV3tXWvZRVdyECBxcw2EHNFWZR4jhPqo2IXHjTb8i1aWHhlGLZH8Y7p8e//4u7h1d3/+A7g4TGILeYs4t0FPq58MWev//28tHnk3B45a3AAMjc4U6BuZrXUvskm00vMZW56DUvXAkJmYPY0LzW6tYVU3KM+0MrdSU7AWAiBQlf8x8zj8KVULs4CnwupgYCM2ypgAmRpLgc5jGFw6/8TH+Yn/2jl/sQVNWOB5tLcxC7QoyZt0PYH+OfvXH12Z/qAnFVVTVzY0Jzm2uJgU+2Q4zRzKqqm5pWWCWrZs3M3CFCbtqakos21WbMTADTKmuAiEEBcAG2m0FrbSJ2Y6fkMJcQg0RyXpZ5WUopbbo8jqaHL30mg5/7wz/rHZLiNE9WNDAHkUAiRK7alpm72L38uuZQPnyHHVDz2lwVrTWG583AqSdtbRnZ1ayZK9xczVTNFGDm4LBa61oBJEYiYriQmLMZhAjkppZzJlgpRZ+7kbrUFXWnVquaOog4cgggWvp8+MKn6Mbu2f/xcl8091nnSk5gNmJfW7RIzEmEpc/p8YEenI8f/zAn4ZBCTslBcO66LqfM6tqMmGpd1iVfQeiKoolgBAXVUtUsxighkLkIE4HIKTCYAGMJEvPlk8vDB2/bvZsnU4lOm+1ms9uEEBzrLjZbFr19onfvPPPNN7aXx263qdVqUxgkxCCBiImJmQMHdlirLBxeen386Adld3IGkLMZPEpMQ5+iwOvcqi61tQYicgDQlTeDmIjBTGRmMSajaxZsRkGYyE0YRkLh5MbJ/tH5ftctn/7J2+8edldjHDKAZo3Am90gDAqizLRU33bD+X5YKqdQSnEzd0QJgQ1OXe7cfD3u5MZBcHksn3ohEMBk7tQcTUtuYS3kVNvS2jr4VdbWazJpCgQEEBTm80xgg3abzp0AZ+GqHjrZbXfL8XAkmz73sZPLcfPgKp/cZLLD4d3NsOEY58MRCALjTuq0lIeXx5vb/ODJsPR1WmKiFImYDkenIP2Qzi/mpZYYoptzH+hQ+LW3g6CuRIydmrZa6qpxzU7OQqYG6Ps9gZWeM4QkQqd7N+TOGe4/Wc4PvDSqygwR2d250+bl4tGj6YufohvbO6/8qOv6EHkuy3Z3lmLYnJ7a6VmK6dGjR4fDVYjp+Oii3Hq+Es3Hsbp18aRLnbmV5lkYRrvtycZsf9inlIXCZItvu1CNrkkd3J1KrSGl2hq5kqsCDf/3IyIcgo8zPnDz/J/+bT/bYVroMPLFUR5cyJOLcH4xPd7j8X7+5IfaB+89//VXu8W7G5vj4er0ZLe5s52nUpcqQUIId27dOhyuKjSO03Sc69DFw5K7LhIPw6Cmw3Zotdbacsr7cT/NU+r6/cPH02c+Un7uU8G9AgAFcoKQWiVtEiLcqq4qrr5f5yHnGAPDjr0cfvXnaUjbP/ymOsrtG5qjfvgOfvoFMOHhBY+T5Xjyyo9298/z6S0zu/vcvU3fX11eMjEJj2WKMcUuhRCdg4zHeLGvQ24X83YYDuORIufUd32fY27epmm6fPJEAh+vLsdNmL7y+f7VN8OqCTHQ3BhiqrVplACmyoKmTLxCTLADFGKIOS3HafzSp9pf+Ymz//btm3/yetVa5wVJaoq17zwEI59vnSb23ctvV9DJje1xf9RWpqNfHQ5O6HN32g/WFiTZDsPjy4sAL1ej3dgZ+8WTJyA+vP1ODCmmRMJBpNYqEptqORznf/bL3OXb/+73wlOJTZnZjY2otBZTZg4SzM2cmCUQQbXFEHLf1+Nx/PCz5Quf27z81o3//T1KATFFNxZOLmlyDvXq6ip/901V1W5zDPz40eMQ5O3757du3t6dnJaymPmy1JADgJwTw3NKy3H2zaDs035vzCGIpFBLUTiDRES6OL9zPv7CJ+vPfeKZ3/6jdH4IK3mCXRN1DqzWliH5NNd5QjNyMxROkYgAquN8FD7+nZ+P++Xmf30pQ0qpflxIYOwQK9zq3CCSN8NxHKtrpnBxcdX1vYFSSoFpcW/aNrvNyh2aGZGUVlGbT6U4iIUIVdtyecVgBjFL7FM9P58+9Mz01b+x/fr3Tr/9g3y6CU+9gFWhI590+cyLl//wb6IVfvucH1/yg0t58ATjyPul7WfXdvzqL9kHnrnzb/779nLUyMtxCTkIBw4cSMBOyJcXVyFIEGlak8Xi1gGbbthsNzdOz96+f3+/37da7929e3V1uLy4Sild7q8MiHOlagAJsVAghsNXVaEdJ815+o0vpf105/e/RUFqraGuWICZk9Sx1BeenX7zy8hduH/ePv5CPe3AActE04z9HN5+whf7+vlP7P70tZPX7ocsZSkhCAsTjMHmTs1y3212m/GwTzmNx7HU0uVcliXm+OTy/OzGTWHuch42m9bw5ltvgWi/P1izFNNGSUMoZisDNqb3ajg3LV/6abt38+a//v1dYzrpL588CQ5iCAn50tpuGL/6BTs7ufUf/3h45YcTk+46O9votq+3d35r1z5yr/Y5vfng9A9fyiGBybVICOZqZmuDSDGZY7vdHI57cUmUqlZYnKexP9ks4/zSt74NN2+V4e/ev9/qomrHcQwi/dBLDDFw36c+53mep7kaORGaeR1dW+NppstjaY0KyDmwMwdx90J+/PVf0I+9cPZ73zj5xp9rjOnyyO+SUyBzRLI+1j4vpnJxxZMeJPWcqxkrTM3dAlvu+s12IyQO7/Mwj8eUUimlaIkxjfsjul5biyk2ogcP3gXIVa+uroho6PsupX676VLsUtpstm+8+WbXSykVVndnN6YY2iuvL7/0Sb17c37nLyJ1hhJYhIRKLePf+tn6+U9uv/by7T/4U1avl1Oz6kRwYYErvFmcGj05L9NcT0/F6+HYELAbdmpqXgXczKZpLnXpuq7L3TRO/aab66xFia0c9pdPLiQEESJeNRdelqU163KXu64b+qHrzm6c/Nrf/XtnZzfefudtcn/w7v3XXnvtlVdfpX4Tr8757cfjh58ZvvWqxFTGg5z0A5Z5/NyL8z/5cn798d3/8L9SbVO1ZVmWspg204ZaSAGtAjhxM2OilQD03dC8QU1SdFAkSSk4IYqYFgPIaZmXBiPYtY4HMjNV1dasLbVZlLjdbnOXNsNm2Gx+/Te+eu/uBy4vL+8+e5eIb5zdvH37mbfe/OGTqwuoLn3XXvyJ4Xs/aoejOYfDz77orU1f+etyqLd+9xvxYt+iWJ1rKwG0glAlIoeAXZUJwtJaCyEASIFKrdpMyXLqckgQGmI8XhwO07jdDY8fX5RacsoxxlorTFf1DERE7KqRKecYA53ttg564UM/sR2Gb37zTw77qw998CefXDxJOU/TRMyBPEo8vv728fMfrbd33dW43W3D4atfRA6keut3/ufuzXdKkLrUeakOd6L3PEACyMna6sGgNnU3NQf0dHdyHMelaPHaSqNAXcrTMg3b7Tge5zIL0zD0IqHLHQi1zOYwNbOmzqvfs9TibiGG0tr3Xv3e1eXl2emtJ0+e3H/3fjf0r73+/YcPH3pVCiFcHHyu+txtvPrOYb+XXUx4vN/90XdOXv4BCbei01yqVlrXCWBAVpeX+am4DnNjIgmhVd2enq6CSilLa6Us5Xg8xpwBf3J5bmrb3SZ1XZfyZujN3RwhCAmlmBjUzM2dmEutN2/dvNofrPndZ+6q+rvv3j8crx49fHh1dTEex6UUJLGl1js39fZpeOXNuc5y43wM3/m+vPkwxMjkpbRaCvFThHHtajGIQcTMq0FvZs0tcFhKG8ejmYFJAueuc7MUYtfFR48flVKHbthsNiJ85/bNsizjNIkwE/ph4wawO1BrTTG1pimlYdN33TDP88OHDx4/fnQ4HC8vrqZpKqW6WwyxXB6Xe7eWFz9Qc2wfuhMaXESqtdoaQGqNmc0U9NTTY3YIEeDOLAhQVcBdm5biwHgsh8Nx3ZBu07vWPvcXl+dlWVLI22GITKcnN5alzrXFlIiJGUkiJRrnSUSYvbaaolxdXNy8cfbo0TtEUpvN86jVVNs4za3VLuWr/dVcy/D9d4bS7MHjBglsqwFKTTWFFCQ0rUz0XqiDHOQGgYPMLYdcSmmtJWGHg1hE1vyOmx2v9gCN42JmJHE7bHNIJ6cnLHR5vp+WhYhziupWbFHz1dYNLK3WFGSZ5uNx6nIcp9FAyzTXVp0wl3k7dMtcDuMoOW4eXPFhhqBeTbLdbN2dwaaNQ3SHuRGzm60KLYEESkQUpB/6Wuo4jkTcdX3K6anwDb82ZkREzM3Nhn4YNkPOQ4q8Px6X0rQ1N6utejNzalavlVaW2ipTCIEB9LvTaZ5rWbSVubZpnlOK1urFxYWDhr4LXV4tAIhLN3SrqahqxCQsgIcg7td31xVO7qCh3zDJ5dWFm/fDMHQ5hrCq6g5iYXIC3NXUjYT71IcYNpt+mg7zXJyII9VazQxOzVprlYkdHkJwraothHSYpv3VVdNmrkRMxDFEb36+v6xNh65LXSYgBq5TKXMJ1owDg8DMrTTpxOzaZ+QQgjA7mVnMiZkvr8616dANQ+4kSEhxPE6tGRFTABgMIcVcW2u1zIWF5+kgksBq2tzczd29oa5VwshIiJnBQWtdlurw/bJgb0y8evsp5VpLLbVLXco5iIjINE+tNXYEgIRhBoWucRhVXaNOroBIJIeEIGE8jstScuyGPseI1A9qzdwAh7kWI5A6co45hHasi5fYQimSu1hqmaeZrlN5Tq6g4ExElFN3HA+lLcyyigYsTJD1esB9nif1FkKIMQaJSYLV2ZZFzdlaCEECy9JmrTWnzuBg8JrkI7ijmIkuh1pLbSGEftOHmHLOzHy4mupUCQ6ouCsc4NqYiURETd3aUsASA6CmBsN15sPJW0LqulxbaWUhRe5zTLGWdQUBAswJ5t7YJaUcU4wpgHA1jq0aQY0QQgzWtFQVCTllEqq1tqZPK5ARBSKr1iSEru9jDsMwkOHq8mIqs9sq2Pm1b+nGbkochF1raZolBmHqEh1HgMhcQAYRoaEL7u04jqre90PXd2rKwusczc3EXA0I6rom9cxsqVXV1W2NCwQ3n0sxx3YYQoquJhxcVofIScnNV6xP7CKcYpIQx8PhOI+2Kl/Xxwi+og7VyAIJREXVAG9lIZEYU3RtrbmDA+WuA4fxuG+ldl3OXSZiCXD4fJzdXQTMrLim5FWrNDHV5ro2pTVRIl2fa2ld7vpNTyAzNVN7qqYz8WrXEbh6Y+YQIhzH47GUQg6FBglgdn0arrHrY0yEWhsLj/M0jROtOZ0QJUYRDiEs0zSVJcU0dEOKMfWdMC3TMi/zGvtwd3JiYRa2WoWZmFtr5G6rqwOISAgShs2QYwwEg1bVUqqZmdla4YOQE6sZPc37ubs1I2JfLVXQGrFZbY2copvBW1UHHG4w0lWbN7gbzLWUZVkg0vdDSikPvVrb7/fH40j0XqwH9LQXrWnRwNHM17jSOgVmoN/0qUskcFitusxlHeLqQ6opMUKiwKxVzayUAjeHqyn5NbgnAhGcEEPMOYNoWera2IjYaI3aEbGbWa21lmrgPveruF1bPVxdTdNITO8PuVynGcxFUlWtWmMM11xoPSPDkHOfYowOG5dlmgreH/ghOLw53MAs5u5qBAOcwTBXb0/NZRAhSMjdUFurtTanlFO/6ZjDU98Da0Lb4M09pZhT7lJm5rKUpdT3El4QXC8z4HASgpuwFC0gBMiaIQkMjv3Qh6i1zfMyz4uZ4f1pn1U0agaHCJNArcLcnEmIhQMLgYjIQATu+w7wUuZS5q7rtidbuDFxCIGJWYJweJqxwHr5hWwp8/F4bE39PYeQ3j+KNRpjgdmam6nD1YxgTJDd6Y7BRcs0La0ZEf7fh4iiYN1KVxdJa9xilZOEg7AIS+pyjLLM0zjPIaSz09MuZ6gr2Vrdr9djnTuhmgZ4g5Wiqurk134vfhzSXn9eJ6KISQE3Y61NicSdQx2rZzc1bYb/z2NuThHmzKFpK7Wo6XqbheBOYCKQqJTZ5nlhlpPdru+Ctmatai2qCuD6oocgHFyE6tyqgZ3W0u/XB8cBOAMMtLoGJENCWzGWtWZsxM5gENH/AVOamIFe9faJAAAAAElFTkSuQmCC",
    'Abyss': "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",
}


# ---------------------------------------------------------------- acciones
def preparar_juego(estado, T):
    hwnd = buscar_ventana()
    if not hwnd:
        titulos = [t for _h, t in listar_ventanas() if t.strip()]
        if sys.stdout:
            print("Ventanas visibles:\n  " + "\n  ".join(titulos))
        estado(T["no_ventana"])
        return False
    if not enfocar(hwnd):
        estado(T["no_foco"])
        return False
    return True


def ejecutar(pasos, cfg, estado, T):
    for cmd, espera in pasos:
        estado(T["escribiendo"].format(cmd))
        comando(cmd, cfg)
        time.sleep(espera)


# Modos que necesitan elegir reliquias antes de entrar
MODOS_CON_RELIQUIA = {"zm_rb_rh_mod", "zm_rb_r_mod", "zm_rb_r_mod_survival"}   # Mister Peeks, Cursed, Cursed Survival

# Super easter egg de Rex Infernus (no se manda en Directed, Training Course ni Rogue Run)
SUPER_EE_MAPA = "zm_sat_scarab"
SUPER_EE_EXCLUIR = {"zm_guided", "zm_training_course", "zm_rb_echo"}
SUPER_EE = ("set enable_rh 1;set skip_zm_rh_validation 1;set enable_scarab_br 1;set enable_firefly_rh 1;"
            "set enable_ruby_rh 1;set enable_mantis_rh 1;set enable_locust_rh 1;set enable_hornet_rh 1;"
            "set enable_scarab_rh 1;set enable_scarab_ee 1;set enable_scarab_sq 1")

# Comandos para activar los easter eggs de cada mapa (se mandan siempre)
EASTER_EGGS = {
    "zm_sat_scarab": "set enable_scarab_ee 1;set enable_scarab_sq 1;set enable_scarab_rh 1;set enable_scarab_br 1",
    "zm_sat_firefly": "set enable_firefly_ee 1;set enable_firefly_mq 1;set enable_firefly_sq 1;"
                      "set enable_firefly_sq_c 1;set enable_firefly_sq_v 1;set enable_firefly_rh 1",
    "zm_sat_ruby": "set enable_ruby_ee 1;set enable_ruby_rh 1",
    "zm_sat_mantis": "set enable_mantis_ee 1;set enable_mantis_mq 1;set enable_mantis_sq 1;set enable_mantis_rh 1",
    "zm_sat_locust": "set enable_locust_ee 1;set enable_locust_mq 1;set enable_locust_sq 1;set enable_locust_rh 1",
    "zm_sat_hornet": "set enable_hornet_ee 1;set enable_hornet_mq 1;set enable_hornet_sq 1;set enable_hornet_rh 1;"
                     "set enable_hornet_ee_pew 1;set enable_hornet_ee_neigh 1;set enable_hornet_ee_cafe 1;"
                     "set enable_hornet_ee_jump 1;set enable_hornet_ee_nya 1;set enable_hornet_ee_roll 1;"
                     "set enable_hornet_ee_bat 1;set enable_hornet_ee_rocker 1",
}


def lanzar_survival(mapa_id, poi, modo_id, confirmar, cfg, estado, T):
    lanzar(mapa_id, modo_id, confirmar, cfg, estado, T, poi=poi)


def lanzar(mapa_id, modo_id, confirmar, cfg, estado, T, poi=None):
    # cfg["zombie_cheat"]: True -> set zombie_cheat 3 (+100k esencia, +25k chatarra, +25k chatarra rara, abre puertas)
    if not preparar_juego(estado, T):
        return
    if modo_id in MODOS_CON_RELIQUIA:
        ejecutar([("luiOpenMenu RelicSelectMenu", 0)], cfg, estado, T)
        estado(T["esperando_reliquia"])
        if not confirmar(modo_id):                 # espera a que el jugador elija y confirme
            estado(T["cancelado"])
            return
        if not preparar_juego(estado, T):   # volver al juego
            return
        time.sleep(0.5)
    pasos = [
        ("xstartprivateparty", cfg["espera_comando"]),
        ("xstartlobby_patched", cfg["espera_lobby"]),
        ("luiOpenMenu zmpubliclobby", cfg["espera_comando"]),   # muestra mapa y modo en el lobby
        (f"ui_mapname {mapa_id}", cfg["espera_comando"]),
        (f"setgametype {modo_id}", cfg["espera_comando"]),
    ]
    survival = modo_id in MODOS_SURVIVAL
    if survival and poi:
        pasos.append((f"set scr_{mapa_id}_survival_poi {poi}", cfg["espera_comando"]))
    if not survival and mapa_id in EASTER_EGGS:
        pasos.append((EASTER_EGGS[mapa_id], cfg["espera_comando"]))
    if not survival and mapa_id == SUPER_EE_MAPA and modo_id not in SUPER_EE_EXCLUIR:
        pasos.append((SUPER_EE, cfg["espera_comando"]))
    if modo_id not in RAMPAGE_EXCLUIR_MODOS and mapa_id not in RAMPAGE_EXCLUIR_MAPAS:
        pasos.append((RAMPAGE_CMD, cfg["espera_comando"]))
    if cfg.get("zombie_cheat"):
        pasos.append(("set zombie_cheat 3", cfg["espera_comando"]))
    pasos.append(("xpartygo", 0))
    ejecutar(pasos, cfg, estado, T)
    estado(T["hecho_mapa"].format(f"{mapa_id} ({poi})" if poi else mapa_id))


def aplicar_camo(nombre, index, loadout, arma, cfg, estado, T):
    if not preparar_juego(estado, T):
        return
    cmd = (f'setStorageFile "sat_zm_loadouts" "loadouts" {loadout} '
           f'"weaponSetups" {arma} "camoLootID" {index}')
    ejecutar([(cmd, 0)], cfg, estado, T)
    estado(T["hecho_camo"].format(nombre))


def poner_arma(nombre, index, cfg, estado, T):
    if not preparar_juego(estado, T):
        return
    ejecutar([(f'setStorageFile "sat_zm_loadouts" "loadouts" 0 "weaponSetups" 0 "weaponlootid" {index}', 0)],
             cfg, estado, T)
    estado(T["arma_hecha"].format(nombre))


SCAN_ESC = 0x01


def salir_partida(cfg, estado, T):
    """Manda disconnect y después spamea ESC unos segundos (evita el bug de menús lentos)."""
    if not preparar_juego(estado, T):
        return
    ejecutar([("disconnect", 1.0)], cfg, estado, T)
    duracion = float(cfg.get("espera_esc", 5.0))
    estado(T["spam_esc"])
    fin = time.time() + duracion
    while time.time() < fin:
        if modo_directo():
            _post_tecla(0x1B, SCAN_ESC, 0.02)
        else:
            tecla_scan(SCAN_ESC, 0.02)
        time.sleep(0.08)
    estado(T["salida_hecha"])


def reiniciar_arma(cfg, estado, T):
    """Pone weaponlootid 0 (arma por defecto): sirve para desbugear la clase."""
    if not preparar_juego(estado, T):
        return
    ejecutar([('setStorageFile "sat_zm_loadouts" "loadouts" 0 "weaponSetups" 0 "weaponlootid" 0', 0)],
             cfg, estado, T)
    estado(T["reset_hecho"])


def probar_consola(estado, T):
    if not preparar_juego(estado, T):
        return
    estado(T["probando"].format(metodo_consola[0]))
    abrir_consola()
    estado(T["se_abrio"])


# ---------------------------------------------------------------- interfaz
BG, PANEL, TXT, ROJO = "#14161a", "#2a2f38", "#c9c9c9", "#d23b3b"


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.resizable(False, False)
        self.configure(bg=BG)
        self.cfg = cargar_config()
        self.ocupado = False
        self.idioma = tk.StringVar(value=self.cfg.get("idioma", "es"))
        self.metodo = tk.StringVar(value=self.cfg.get("metodo_consola", METODO_DEFAULT))
        if self.metodo.get() not in METODOS_CONSOLA:
            self.metodo.set(METODO_DEFAULT)
        self.loadout = tk.StringVar(value=str(self.cfg.get("loadout", 0)))
        self.arma = tk.StringVar(value=str(self.cfg.get("arma", 0)))
        self.vars = {k: tk.StringVar(value=str(self.cfg[k]))
                     for k in ("espera_comando", "espera_lobby", "espera_consola", "espera_esc")}
        self.tab_actual = 0
        self.zombie_cheat = tk.BooleanVar(value=bool(self.cfg.get("zombie_cheat", False)))
        ids_modos = [m[0] for m in MODOS]
        modo_guardado = self.cfg.get("modo", "zm_rb")
        self.modo = tk.StringVar(value=modo_guardado if modo_guardado in ids_modos else "zm_rb")
        self.imgs = {}
        for nombre, data in CAMO_IMG.items():
            try:
                self.imgs[nombre] = tk.PhotoImage(data=data)
            except tk.TclError:
                pass

        st = ttk.Style(self)
        st.theme_use("clam")
        st.configure("Mapa.TButton", font=("Segoe UI", 11, "bold"), padding=10,
                     background=PANEL, foreground="#e8e8e8", borderwidth=0)
        st.map("Mapa.TButton", background=[("active", "#7a1f1f")])
        st.configure("Camo.TButton", font=("Segoe UI", 10), padding=6,
                     background=PANEL, foreground="#e8e8e8", borderwidth=0)
        st.map("Camo.TButton", background=[("active", "#7a5a1f")])
        st.configure("TLabel", background=BG, foreground=TXT, font=("Segoe UI", 9))
        st.configure("TFrame", background=BG)
        st.configure("TRadiobutton", background=BG, foreground=TXT)
        st.configure("TCheckbutton", background=BG, foreground=TXT)
        st.configure("TLabelframe", background=BG, foreground=TXT)
        st.configure("TLabelframe.Label", background=BG, foreground=TXT)
        st.configure("TNotebook", background=BG, borderwidth=0)
        st.configure("TNotebook.Tab", background=PANEL, foreground=TXT, padding=(10, 4))
        st.map("TNotebook.Tab", background=[("selected", "#7a1f1f")])

        self.construir()

    @property
    def T(self):
        return TEXTOS[self.idioma.get()]

    def construir(self):
        for w in self.winfo_children():
            w.destroy()
        T = self.T
        self.title(T["titulo"])

        tk.Label(self, text="BO7 ZOMBIES", bg=BG, fg=ROJO,
                 font=("Segoe UI", 18, "bold")).pack(pady=(12, 0))
        tk.Label(self, text="SIMPLE TOOL", bg=BG, fg=TXT,
                 font=("Segoe UI", 9, "bold")).pack(pady=(0, 4))

        nb = ttk.Notebook(self)
        nb.pack(padx=12, fill="both")
        self.nb = nb

        # --- Mapas
        f = ttk.Frame(nb)
        nb.add(f, text=T["tab_mapas"])
        ttk.Label(f, text=T["elige_modo"]).pack(pady=(8, 2), anchor="w", padx=10)
        mb = ttk.Frame(f)
        mb.pack(padx=10, fill="x")
        es = self.idioma.get() == "es"
        for i, (mid, en, sp) in enumerate(MODOS):
            ttk.Radiobutton(mb, text=sp if es else en, value=mid, variable=self.modo,
                            command=self._llenar_mapas
                            ).grid(row=i // 2, column=i % 2, sticky="w", padx=4, pady=2)
        ttk.Checkbutton(f, text=T["zombie_cheat"], variable=self.zombie_cheat
                        ).pack(pady=(10, 0), anchor="w", padx=10)
        ttk.Label(f, text=T["elige_mapa"]).pack(pady=(10, 4), anchor="w", padx=10)
        self.grid_mapas = ttk.Frame(f)
        self.grid_mapas.pack(padx=8, pady=(0, 8))
        self._llenar_mapas()

        ttk.Button(f, text=T["salir"], command=lambda: self._hilo(salir_partida)
                   ).pack(pady=(0, 10))

        # --- Camuflajes
        f = ttk.Frame(nb)
        nb.add(f, text=T["tab_camos"])
        ttk.Label(f, text=T["elige_camo"]).pack(pady=8)
        if MOSTRAR_SELECTOR_CLASE:
            # Solo para Multijugador (varias clases y arma principal/secundaria).
            sel = ttk.Frame(f)
            sel.pack(pady=(0, 6))
            ttk.Label(sel, text=T["loadout"]).grid(row=0, column=0, padx=(0, 4))
            tk.Spinbox(sel, from_=0, to=9, width=3, textvariable=self.loadout).grid(row=0, column=1, padx=(0, 16))
            ttk.Label(sel, text=T["arma"]).grid(row=0, column=2, padx=(0, 4))
            ttk.Radiobutton(sel, text=T["principal"], value="0", variable=self.arma).grid(row=0, column=3)
            ttk.Radiobutton(sel, text=T["secundaria"], value="1", variable=self.arma).grid(row=0, column=4)
        ttk.Button(f, text=T["reset_arma"], style="Mapa.TButton",
                   command=self.reiniciar_arma).pack(pady=(0, 8))
        sub = ttk.Notebook(f)
        sub.pack(fill="both", expand=True, padx=4, pady=(0, 6))
        for juego in ("BO6", "MW2", "MW3"):
            cont = self._scroll(sub)
            sub.add(cont.master_frame, text=f"  {juego}  ")
            if juego == "BO6":
                # Maestrías de BO6 con imagen
                for clave, lista in CAMOS.items():
                    box = ttk.LabelFrame(cont, text=f" {T[clave]} ")
                    box.pack(fill="x", padx=6, pady=4)
                    for i, (nombre, idx) in enumerate(lista):
                        ttk.Button(box, text=nombre, image=self.imgs.get(nombre), compound="top",
                                   style="Camo.TButton", width=13,
                                   command=lambda n=nombre, x=idx: self.accion_camo(n, x)
                                   ).grid(row=0, column=i, padx=3, pady=6)
            for seccion, lista in CAMOS_JUEGOS[juego]:
                box = ttk.LabelFrame(cont, text=f" {T['sec_' + seccion]} ")
                box.pack(fill="x", padx=6, pady=4)
                for i, (nombre, idx) in enumerate(lista):
                    ttk.Button(box, text=f"{nombre}\n{idx}", style="Camo.TButton", width=13,
                               command=lambda n=nombre, x=idx: self.accion_camo(n, x)
                               ).grid(row=i // 4, column=i % 4, padx=3, pady=3)

        # --- Armas maravilla
        f = ttk.Frame(nb)
        nb.add(f, text=T["tab_ww"])
        ttk.Label(f, text=T["elige_ww"]).pack(pady=8)
        g = ttk.Frame(f)
        g.pack(padx=8, pady=(0, 8))
        for i, (nombre, idx) in enumerate(ARMAS_MARAVILLA):
            ttk.Button(g, text=nombre, style="Mapa.TButton", width=22,
                       command=lambda n=nombre, x=idx: self._hilo(poner_arma, n, x)
                       ).grid(row=i // 2, column=i % 2, padx=4, pady=4, sticky="ew")
        ttk.Button(f, text=T["reset_arma"], command=self.reiniciar_arma).pack(pady=(4, 10))

        # --- Ajustes
        f = ttk.Frame(nb)
        nb.add(f, text=T["tab_ajustes"])
        box = ttk.LabelFrame(f, text=T["idioma"])
        box.pack(fill="x", padx=8, pady=(10, 6))
        for i, (code, txt) in enumerate((("es", "Español"), ("en", "English"))):
            ttk.Radiobutton(box, text=txt, value=code, variable=self.idioma,
                            command=self.cambiar_idioma).grid(row=0, column=i, padx=8, pady=6)
        box = ttk.LabelFrame(f, text=T["tiempos"])
        box.pack(fill="x", padx=8, pady=6)
        for i, (k, clave) in enumerate((("espera_comando", "entre_cmd"),
                                        ("espera_lobby", "esperar_lobby"),
                                        ("espera_consola", "abrir_consola"),
                                        ("espera_esc", "esperar_esc"))):
            ttk.Label(box, text=T[clave]).grid(row=i // 2, column=(i % 2) * 2, padx=(8, 2), pady=4, sticky="w")
            ttk.Entry(box, textvariable=self.vars[k], width=5).grid(row=i // 2, column=(i % 2) * 2 + 1, padx=(0, 12))
        box = ttk.LabelFrame(f, text=T["tecla_consola"])
        box.pack(fill="x", padx=8, pady=(6, 10))
        ttk.Combobox(box, textvariable=self.metodo, values=list(METODOS_CONSOLA),
                     state="readonly", width=28).grid(row=0, column=0, padx=8, pady=6)
        ttk.Button(box, text=T["probar"], command=self.probar).grid(row=0, column=1, padx=6)

        nb.select(self.tab_actual)

        self.lbl = ttk.Label(self, text=T["listo"])
        self.lbl.pack(pady=(8, 12))

    def _scroll(self, parent, alto=360):
        """Marco con barra de desplazamiento. Devuelve el frame interior
        (su .master_frame es lo que se agrega al Notebook)."""
        outer = ttk.Frame(parent)
        canvas = tk.Canvas(outer, bg=BG, highlightthickness=0, height=alto, width=470)
        bar = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        inner = ttk.Frame(canvas)
        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.configure(yscrollcommand=bar.set)
        canvas.pack(side="left", fill="both", expand=True)
        bar.pack(side="right", fill="y")

        def rueda(e):
            canvas.yview_scroll(int(-e.delta / 120), "units")
        outer.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", rueda))
        outer.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))
        inner.master_frame = outer
        return inner

    def _llenar_mapas(self):
        """Muestra los mapas normales o los de sobrevivencia según el modo elegido."""
        g = self.grid_mapas
        for w in g.winfo_children():
            w.destroy()
        if self.modo.get() in MODOS_SURVIVAL:
            es = self.idioma.get() == "es"
            for i, (en, sp, mid, poi) in enumerate(MAPAS_SURVIVAL):
                ttk.Button(g, text=sp if es else en, style="Mapa.TButton", width=22,
                           command=lambda m=mid, z=poi: self.accion(
                               lanzar_survival, m, z, self.modo.get(), self.confirmar_reliquia)
                           ).grid(row=i // 2, column=i % 2, padx=4, pady=4, sticky="ew")
        else:
            for i, (nombre, mid) in enumerate(MAPAS):
                ttk.Button(g, text=nombre, style="Mapa.TButton", width=22,
                           command=lambda m=mid: self.accion(
                               lanzar, m, self.modo.get(), self.confirmar_reliquia)
                           ).grid(row=i // 2, column=i % 2, padx=4, pady=4, sticky="ew")

    def cambiar_idioma(self):
        self.tab_actual = self.nb.index(self.nb.select())
        self.cfg["idioma"] = self.idioma.get()
        guardar_config(self.cfg)
        self.construir()

    def estado(self, txt):
        self.after(0, lambda: self.lbl.config(text=txt))

    def _guardar(self):
        metodo_consola[0] = self.metodo.get()
        self.cfg["metodo_consola"] = self.metodo.get()
        try:
            for k, v in self.vars.items():
                self.cfg[k] = float(v.get().replace(",", "."))
            self.cfg["loadout"] = int(self.loadout.get())
            self.cfg["arma"] = int(self.arma.get())
        except ValueError:
            messagebox.showerror("Error", self.T["err_tiempos"])
            return False
        self.cfg["modo"] = self.modo.get()
        self.cfg["zombie_cheat"] = bool(self.zombie_cheat.get())
        guardar_config(self.cfg)
        return True

    def _hilo(self, fn, *args):
        if self.ocupado or not self._guardar():
            return
        self.ocupado = True
        T = self.T

        def run():
            try:
                fn(*args, self.estado, T) if fn is probar_consola else fn(*args, self.cfg, self.estado, T)
            finally:
                self.ocupado = False

        threading.Thread(target=run, daemon=True).start()

    def accion(self, fn, *args):
        self._hilo(fn, *args)

    def accion_camo(self, nombre, index):
        if MOSTRAR_SELECTOR_CLASE:
            self._hilo(aplicar_camo, nombre, index, self.loadout.get(), self.arma.get())
        else:
            self._hilo(aplicar_camo, nombre, index, 0, 0)

    def probar(self):
        self._hilo(probar_consola)

    def reiniciar_arma(self):
        self._hilo(reiniciar_arma)

    def confirmar_reliquia(self, modo_id):
        """Se llama desde el hilo de trabajo: muestra un aviso y espera la respuesta."""
        listo = threading.Event()
        resultado = [False]
        T = self.T

        def mostrar():
            d = tk.Toplevel(self)
            titulo = T["reliquia_titulo_" + modo_id]
            d.title(titulo)
            d.configure(bg=BG)
            d.resizable(False, False)
            d.attributes("-topmost", True)
            tk.Label(d, text=titulo, bg=BG, fg="#e0b040",
                     font=("Segoe UI", 14, "bold")).pack(padx=20, pady=(14, 6))
            ttk.Label(d, text=T["reliquia_txt_" + modo_id], justify="left").pack(padx=20, pady=(0, 12))
            fila = ttk.Frame(d)
            fila.pack(pady=(0, 14))

            def cerrar(ok):
                resultado[0] = ok
                d.destroy()
                listo.set()

            ttk.Button(fila, text=T["continuar"], style="Mapa.TButton",
                       command=lambda: cerrar(True)).pack(side="left", padx=6)
            ttk.Button(fila, text=T["cancelar"],
                       command=lambda: cerrar(False)).pack(side="left", padx=6)
            d.protocol("WM_DELETE_WINDOW", lambda: cerrar(False))
            d.lift()
            d.focus_force()

        self.after(0, mostrar)
        listo.wait()
        return resultado[0]


def es_admin():
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def pythonw():
    """Ruta de pythonw.exe (Python sin ventana de consola)."""
    import sys
    exe = sys.executable
    w = os.path.join(os.path.dirname(exe), "pythonw.exe")
    return w if os.path.exists(w) else exe


def ocultar_consola():
    try:
        h = ctypes.windll.kernel32.GetConsoleWindow()
        if h:
            ctypes.windll.user32.ShowWindow(h, 0)   # SW_HIDE
    except Exception:
        pass


if __name__ == "__main__":
    import sys
    ocultar_consola()
    if not es_admin() and not getattr(sys, "frozen", False):
        # Se vuelve a abrir como Administrador (Windows bloquea las teclas
        # simuladas hacia juegos que corren como admin si este programa no lo es).
        # Se usa pythonw.exe para que no aparezca la ventana negra de consola.
        params = " ".join(f'"{a}"' for a in sys.argv)
        r = ctypes.windll.shell32.ShellExecuteW(None, "runas", pythonw(), params, None, 0)
        if r > 32:
            sys.exit(0)
    App().mainloop()
