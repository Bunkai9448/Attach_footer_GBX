#!/usr/bin/env python3
"""
Attach_footer_GBX.py
Conversor Universal a GBX (Game Boy Xtended)
Soporta todos los mappers que mGBA reconoce a través del formato GBX.

Uso:
    python Attach_footer_GBX.py --help
    python Attach_footer_GBX.py --list-mappers
    python Attach_footer_GBX.py <rom> <mapper_id> [--ram N] [--battery] [--rumble] [--timer]
    python Attach_footer_GBX.py <rom> --interactive
"""

import sys
import os
import argparse

# ---------------------------------------------------------------
# Tabla de mappers: ID, descripción, ID de 4 bytes, tiene batería por defecto
# ---------------------------------------------------------------
MAPPER_TABLE = [
    # (ID,     descripción,                                     bytes,       default_battery)
    ("ROM",   "ROM Only (sin mapper)",                          b"ROM\x00",  False),
    ("MBC1",  "MBC1 compatible",                                b"MBC1",     True),
    ("MBC2",  "MBC2",                                           b"MBC2",     True),
    ("MBC3",  "MBC3 compatible",                                b"MBC3",     True),
    ("MBC5",  "MBC5 compatible",                                b"MBC5",     True),
    ("MB1M",  "MBC1M (multicart)",                              b"MB1M",     False),
    ("NTN",   "NT (Makon) new",                                 b"NTN\x00",  True),
    ("NTO1",  "NT (Makon) old type 1",                          b"NTO1",     False),
    ("NTO2",  "NT (Makon) old type 2",                          b"NTO2",     False),
    ("LICH",  "Li Cheng (XingXing/Niutoude)",                    b"LICH",     False),
    ("SACH",  "Sachen MMC1",                                    b"SACH",     False),
    ("SAM2",  "Sachen MMC2",                                    b"SAM2",     False),
    ("BBD",   "BBD",                                            b"BBD\x00",  False),
    ("HITE",  "Hitek",                                          b"HITE",     False),
    ("GB81",  "GGB-81",                                         b"GB81",     False),
    ("ROCK",  "Rocket Games",                                   b"ROCK",     False),
    ("TPP1",  "Pokémon Jade/Diamond",                           b"TPP1",     False),
    ("PKJD",  "Pokémon Jade/Diamond",                           b"PKJD",     False),
]

# Diccionario rápido: ID -> (bytes, descripción, battery)
MAPPER_IDS = {m[0]: (m[2], m[1], m[3]) for m in MAPPER_TABLE}

# ---------------------------------------------------------------
# Construcción del footer GBX
# ---------------------------------------------------------------
def create_gbx_footer(mapper_id, rom_size, ram_size,
                      has_battery=None, has_rumble=False, has_timer=False):
    """Construye el footer de 64 bytes según la especificación GBX v1.0."""
    if mapper_id not in MAPPER_IDS:
        raise ValueError(f"Mapper ID desconocido: {mapper_id}")

    mapper_bytes, _, default_battery = MAPPER_IDS[mapper_id]

    if has_battery is None:
        has_battery = default_battery

    footer = bytearray(64)
    footer[0:4]  = mapper_bytes              # 0x00-0x03: Mapper ID
    footer[4]    = 1 if has_battery else 0   # 0x04: Battery
    footer[5]    = 1 if has_rumble  else 0   # 0x05: Rumble
    footer[6]    = 1 if has_timer   else 0   # 0x06: Timer (RTC)
    footer[7]    = 0                          # 0x07: No usado
    footer[8:12] = rom_size.to_bytes(4, 'big')   # 0x08-0x0B: ROM size
    footer[12:16]= ram_size.to_bytes(4, 'big')   # 0x0C-0x0F: RAM size
    # 0x10-0x2F: variables específicas del mapper
    if mapper_id == "MB1M":
        footer[16] = 4                       # MBC1M necesita 4 aquí
    # 0x30-0x3F: metadata del footer
    footer[48:52] = (64).to_bytes(4, 'big')  # Footer size
    footer[52:56] = (1).to_bytes(4, 'big')   # Major version
    footer[56:60] = (0).to_bytes(4, 'big')   # Minor version
    footer[60:64] = b"GBX!"                  # Firma
    return bytes(footer)


# ---------------------------------------------------------------
# Conversión
# ---------------------------------------------------------------
def convert_to_gbx(input_path, output_path, mapper_id, ram_size=0,
                   has_battery=None, has_rumble=False, has_timer=False):
    if not os.path.exists(input_path):
        print(f"[!] Error: no existe el archivo {input_path}")
        return False

    with open(input_path, "rb") as f:
        rom_data = f.read()

    rom_size = len(rom_data)

    try:
        footer = create_gbx_footer(mapper_id, rom_size, ram_size,
                                   has_battery, has_rumble, has_timer)
    except ValueError as e:
        print(f"[!] {e}")
        return False

    with open(output_path, "wb") as f:
        f.write(rom_data)
        f.write(footer)

    _, desc, _ = MAPPER_IDS[mapper_id]
    print(f"\n[✓] Conversión exitosa: {output_path}")
    print(f"    ROM original : {os.path.basename(input_path)} ({rom_size} bytes)")
    print(f"    Mapper       : {mapper_id} — {desc}")
    print(f"    RAM Size     : {ram_size} bytes (0x{ram_size:X})")
    print(f"    Battery      : {'Sí' if (has_battery if has_battery is not None else MAPPER_IDS[mapper_id][2]) else 'No'}")
    print(f"    Rumble       : {'Sí' if has_rumble else 'No'}")
    print(f"    Timer (RTC)  : {'Sí' if has_timer else 'No'}")
    print(f"    Tamaño final : {rom_size + 64} bytes")
    return True


# ---------------------------------------------------------------
# Ayuda y listado
# ---------------------------------------------------------------
def print_mappers():
    print("\n" + "="*78)
    print(" MAPPERS SOPORTADOS EN GBX (según mGBA)")
    print("="*78)
    print(f"{'ID':<6} {'Bytes':<8} {'Batería':<8} Descripción")
    print("-"*78)
    for mid, desc, mbytes, battery in MAPPER_TABLE:
        bstr = mbytes.decode('ascii', errors='replace').rstrip('\x00')
        print(f"{mid:<6} {bstr:<8} {'Sí' if battery else 'No':<8} {desc}")
    print("="*78)
    print("\nNotas:")
    print("  - Battery: si el juego guarda partida (SRAM). La mayoría de NT new sí.")
    print("  - Algunos mappers (Sintax, Vast Fame) NO están soportados vía GBX.")
    print("    mGBA los detecta por heurística interna, no por footer.")
    print()
    print("Ejemplos de uso:")
    print("  python Attach_footer_GBX.py mi_rom.gbc NTN")
    print("  python Attach_footer_GBX.py mi_rom.gbc NTN --ram 32768")
    print("  python Attach_footer_GBX.py mi_rom.gbc MBC5 --ram 8192 --battery")
    print("  python Attach_footer_GBX.py mi_rom.gbc --interactive")
    print()


def print_help():
    print("""
Attach_footer_GBX.py
Conversor Universal a GBX (Game Boy Xtended)
=============================================

Crea archivos .gbx (ROM + footer de 64 bytes) para que mGBA 0.10.0+
reconozca correctamente mappers oficiales y no licenciados.

SINTAXIS:
    python Attach_footer_GBX.py <rom.gbc> <mapper_id> [opciones]
    python Attach_footer_GBX.py <rom.gbc> --interactive
    python Attach_footer_GBX.py --list-mappers
    python Attach_footer_GBX.py --help

OPCIONES:
    --ram N         Tamaño de RAM en bytes (default: 0)
                    Ejemplos: 8192 (8KB), 32768 (32KB)
    --battery       Marcar el cartucho como que tiene batería (SRAM)
    --no-battery    Marcar como que NO tiene batería
    --rumble        Marcar como que tiene rumble
    --timer         Marcar como que tiene timer (RTC)
    -o, --output    Ruta de salida (default: mismo nombre con .gbx)

EJEMPLOS:
    # Tu Pokémon Diamond (Makon NT new)
    python Attach_footer_GBX.py POKEMONSPECIALDIAMONDSPANISH.gbc NTN --ram 32768

    # Un MBC5 clásico
    python Attach_footer_GBX.py juego.gbc MBC5 --ram 8192 --battery

    # Ver todos los mappers soportados
    python Attach_footer_GBX.py --list-mappers

    # Modo interactivo (pregunta paso a paso)
    python Attach_footer_GBX.py POKEMONSPECIALDIAMONDSPANISH.gbc --interactive
""")


# ---------------------------------------------------------------
# Modo interactivo
# ---------------------------------------------------------------
def interactive_mode(rom_path):
    print("\n" + "="*78)
    print(" MODO INTERACTIVO — Conversor a GBX")
    print("="*78)
    print(f"ROM: {rom_path}\n")

    if not os.path.exists(rom_path):
        print(f"[!] Error: no existe el archivo {rom_path}")
        return

    with open(rom_path, "rb") as f:
        rom_size = len(f.read())
    print(f"Tamaño de ROM: {rom_size} bytes (0x{rom_size:X})\n")

    print_mappers()

    # Elegir mapper
    while True:
        mid = input("Mapper ID (ej. NTN): ").strip().upper()
        if mid in MAPPER_IDS:
            break
        print(f"  [!] '{mid}' no es un mapper válido. Prueba otra vez.")

    _, desc, default_battery = MAPPER_IDS[mid]

    # RAM
    while True:
        ram_str = input("Tamaño de RAM en bytes (0, 8192, 32768) [default: 0]: ").strip()
        if ram_str == "":
            ram_size = 0
            break
        try:
            ram_size = int(ram_str)
            if ram_size < 0:
                raise ValueError
            break
        except ValueError:
            print("  [!] Introduce un número entero >= 0.")

    # Batería
    if default_battery:
        bat = input(f"¿Tiene batería? [S/n, default: S]: ").strip().lower()
        has_battery = bat not in ("n", "no")
    else:
        bat = input(f"¿Tiene batería? [s/N, default: N]: ").strip().lower()
        has_battery = bat in ("s", "si", "sí", "y", "yes")

    # Rumble
    rum = input("¿Tiene rumble? [s/N]: ").strip().lower()
    has_rumble = rum in ("s", "si", "sí", "y", "yes")

    # Timer
    tim = input("¿Tiene timer (RTC)? [s/N]: ").strip().lower()
    has_timer = tim in ("s", "si", "sí", "y", "yes")

    # Salida
    base, _ = os.path.splitext(rom_path)
    output = base + ".gbx"
    out = input(f"Archivo de salida [default: {output}]: ").strip()
    if out:
        output = out

    convert_to_gbx(rom_path, output, mid, ram_size,
                   has_battery, has_rumble, has_timer)


# ---------------------------------------------------------------
# Punto de entrada
# ---------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="Attach_footer_GBX.py — Conversor universal a GBX para mGBA.",
        add_help=False
    )
    parser.add_argument("rom", nargs="?", help="Ruta a la ROM .gb/.gbc")
    parser.add_argument("mapper", nargs="?", help="ID del mapper (ej. NTN, MBC5)")
    parser.add_argument("--ram", type=int, default=0, help="Tamaño de RAM en bytes")
    parser.add_argument("--battery", action="store_true", help="Tiene batería")
    parser.add_argument("--no-battery", action="store_true", help="No tiene batería")
    parser.add_argument("--rumble", action="store_true", help="Tiene rumble")
    parser.add_argument("--timer", action="store_true", help="Tiene timer (RTC)")
    parser.add_argument("-o", "--output", help="Archivo de salida .gbx")
    parser.add_argument("--list-mappers", action="store_true",
                        help="Lista todos los mappers soportados y sale")
    parser.add_argument("--interactive", action="store_true",
                        help="Modo interactivo paso a paso")
    parser.add_argument("-h", "--help", action="store_true",
                        help="Muestra esta ayuda")

    args = parser.parse_args()

    if args.help or (not args.rom and not args.list_mappers):
        print_help()
        return

    if args.list_mappers:
        print_mappers()
        return

    if args.interactive or not args.mapper:
        interactive_mode(args.rom)
        return

    # Determinar batería
    has_battery = None
    if args.battery and args.no_battery:
        print("[!] No puedes especificar --battery y --no-battery a la vez.")
        sys.exit(1)
    if args.battery:
        has_battery = True
    elif args.no_battery:
        has_battery = False

    # Salida por defecto
    output = args.output
    if not output:
        base, _ = os.path.splitext(args.rom)
        output = base + ".gbx"

    ok = convert_to_gbx(args.rom, output, args.mapper.upper(),
                        args.ram, has_battery, args.rumble, args.timer)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()