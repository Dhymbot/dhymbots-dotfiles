#!/usr/bin/env python3

import sys
from obsws_python import ReqClient

if len(sys.argv) != 2:
    print("Uso: obs-scene.py <nombre-escena>")
    raise SystemExit(1)

client = ReqClient(
    host="192.168.0.21",
    port=4455,
    password="VlKfRyGhmRZZdCjv",  # pon aquí la contraseña si activas autenticación
)

client.set_current_program_scene(sys.argv[1])
#help(client)
print(client.get_hot_key_list())
# A mirar: set_input_volume, trigger_hotkey_by_key_sequence and similars
# cl.toggle_input_mute('Mic/Aux')