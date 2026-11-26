import os
import sys
import json
import time
import shutil
import socket
import subprocess
import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

try:
    from stun_p2p import StunUdpPeer
except Exception:
    StunUdpPeer = None


def get_cli_arg(flag, default):
    if flag in sys.argv:
        idx = sys.argv.index(flag) + 1
        if idx < len(sys.argv):
            return sys.argv[idx]
    return default


ACTIVE_PROFILE = get_cli_arg("--profile", "Default Run")
SAVE_FILE = get_cli_arg("--save", os.path.join(os.path.dirname(os.path.abspath(__file__)), "soullink_save.json"))
NET_MODE = get_cli_arg("--mode", "local").lower()

GEN1_TYPES = {
    0: "Normal", 1: "Fighting", 2: "Flying", 3: "Poison", 4: "Ground",
    5: "Rock", 7: "Bug", 8: "Ghost", 20: "Fire", 21: "Water",
    22: "Grass", 23: "Electric", 24: "Psychic", 25: "Ice", 26: "Dragon"
}

SPECIES_DATA = {
    1: ("Bulbasaur", "Grass"), 2: ("Ivysaur", "Grass"), 3: ("Venusaur", "Grass"),
    4: ("Charmander", "Fire"), 5: ("Charmeleon", "Fire"), 6: ("Charizard", "Fire"),
    7: ("Squirtle", "Water"), 8: ("Wartortle", "Water"), 9: ("Blastoise", "Water"),
    10: ("Caterpie", "Bug"), 11: ("Metapod", "Bug"), 12: ("Butterfree", "Bug"),
    13: ("Weedle", "Bug"), 14: ("Kakuna", "Bug"), 15: ("Beedrill", "Bug"),
    16: ("Pidgey", "Normal"), 17: ("Pidgeotto", "Normal"), 18: ("Pidgeot", "Normal"),
    19: ("Rattata", "Normal"), 20: ("Raticate", "Normal"), 21: ("Spearow", "Normal"),
    22: ("Fearow", "Normal"), 23: ("Ekans", "Poison"), 24: ("Arbok", "Poison"),
    25: ("Pikachu", "Electric"), 26: ("Raichu", "Electric"), 27: ("Sandshrew", "Ground"),
    28: ("Sandslash", "Ground"), 29: ("Nidoran F", "Poison"), 30: ("Nidorina", "Poison"),
    31: ("Nidoqueen", "Poison"), 32: ("Nidoran M", "Poison"), 33: ("Nidorino", "Poison"),
    34: ("Nidoking", "Poison"), 35: ("Clefairy", "Normal"), 36: ("Clefable", "Normal"),
    37: ("Vulpix", "Fire"), 38: ("Ninetales", "Fire"), 39: ("Jigglypuff", "Normal"),
    40: ("Wigglytuff", "Normal"), 41: ("Zubat", "Poison"), 42: ("Golbat", "Poison"),
    43: ("Oddish", "Grass"), 44: ("Gloom", "Grass"), 45: ("Vileplume", "Grass"),
    46: ("Paras", "Bug"), 47: ("Parasect", "Bug"), 48: ("Venonat", "Bug"),
    49: ("Venomoth", "Bug"), 50: ("Diglett", "Ground"), 51: ("Dugtrio", "Ground"),
    52: ("Meowth", "Normal"), 53: ("Persian", "Normal"), 54: ("Psyduck", "Water"),
    55: ("Golduck", "Water"), 56: ("Mankey", "Fighting"), 57: ("Primeape", "Fighting"),
    58: ("Growlithe", "Fire"), 59: ("Arcanine", "Fire"), 60: ("Poliwag", "Water"),
    61: ("Poliwhirl", "Water"), 62: ("Poliwrath", "Water"), 63: ("Abra", "Psychic"),
    64: ("Kadabra", "Psychic"), 65: ("Alakazam", "Psychic"), 66: ("Machop", "Fighting"),
    67: ("Machoke", "Fighting"), 68: ("Machamp", "Fighting"), 69: ("Bellsprout", "Grass"),
    70: ("Weepinbell", "Grass"), 71: ("Victreebel", "Grass"), 72: ("Tentacool", "Water"),
    73: ("Tentacruel", "Water"), 74: ("Geodude", "Rock"), 75: ("Graveler", "Rock"),
    76: ("Golem", "Rock"), 77: ("Ponyta", "Fire"), 78: ("Rapidash", "Fire"),
    79: ("Slowpoke", "Water"), 80: ("Slowbro", "Water"), 81: ("Magnemite", "Electric"),
    82: ("Magneton", "Electric"), 83: ("Farfetch'd", "Normal"), 84: ("Doduo", "Normal"),
    85: ("Dodrio", "Normal"), 86: ("Seel", "Water"), 87: ("Dewgong", "Water"),
    88: ("Grimer", "Poison"), 89: ("Muk", "Poison"), 90: ("Shellder", "Water"),
    91: ("Cloyster", "Water"), 92: ("Gastly", "Ghost"), 93: ("Haunter", "Ghost"),
    94: ("Gengar", "Ghost"), 95: ("Onix", "Rock"), 96: ("Drowzee", "Psychic"),
    97: ("Hypno", "Psychic"), 98: ("Krabby", "Water"), 99: ("Kingler", "Water"),
    100: ("Voltorb", "Electric"), 101: ("Electrode", "Electric"), 102: ("Exeggcute", "Grass"),
    103: ("Exeggutor", "Grass"), 104: ("Cubone", "Ground"), 105: ("Marowak", "Ground"),
    106: ("Hitmonlee", "Fighting"), 107: ("Hitmonchan", "Fighting"), 108: ("Lickitung", "Normal"),
    109: ("Koffing", "Poison"), 110: ("Weezing", "Poison"), 111: ("Rhyhorn", "Ground"),
    112: ("Rhydon", "Ground"), 113: ("Chansey", "Normal"), 114: ("Tangela", "Grass"),
    115: ("Kangaskhan", "Normal"), 116: ("Horsea", "Water"), 117: ("Seadra", "Water"),
    118: ("Goldeen", "Water"), 119: ("Seaking", "Water"), 120: ("Staryu", "Water"),
    121: ("Starmie", "Water"), 122: ("Mr. Mime", "Psychic"), 123: ("Scyther", "Bug"),
    124: ("Jynx", "Ice"), 125: ("Electabuzz", "Electric"), 126: ("Magmar", "Fire"),
    127: ("Pinsir", "Bug"), 128: ("Tauros", "Normal"), 129: ("Magikarp", "Water"),
    130: ("Gyarados", "Water"), 131: ("Lapras", "Water"), 132: ("Ditto", "Normal"),
    133: ("Eevee", "Normal"), 134: ("Vaporeon", "Water"), 135: ("Jolteon", "Electric"),
    136: ("Flareon", "Fire"), 137: ("Porygon", "Normal"), 138: ("Omanyte", "Rock"),
    139: ("Omastar", "Rock"), 140: ("Kabuto", "Rock"), 141: ("Kabutops", "Rock"),
    142: ("Aerodactyl", "Rock"), 143: ("Snorlax", "Normal"), 144: ("Articuno", "Ice"),
    145: ("Zapdos", "Electric"), 146: ("Moltres", "Fire"), 147: ("Dratini", "Dragon"),
    148: ("Dragonair", "Dragon"), 149: ("Dragonite", "Dragon"), 150: ("Mewtwo", "Psychic"),
    151: ("Mew", "Psychic"),
    152: ("Chikorita", "Grass"), 153: ("Bayleef", "Grass"), 154: ("Meganium", "Grass"),
    155: ("Cyndaquil", "Fire"), 156: ("Quilava", "Fire"), 157: ("Typhlosion", "Fire"),
    158: ("Totodile", "Water"), 159: ("Croconaw", "Water"), 160: ("Feraligatr", "Water"),
    161: ("Sentret", "Normal"), 162: ("Furret", "Normal"), 163: ("Hoothoot", "Normal"),
    164: ("Noctowl", "Normal"), 165: ("Ledyba", "Bug"), 166: ("Ledian", "Bug"),
    167: ("Spinarak", "Bug"), 168: ("Ariados", "Bug"), 169: ("Crobat", "Poison"),
    170: ("Chinchou", "Water"), 171: ("Lanturn", "Water"), 172: ("Pichu", "Electric"),
    173: ("Cleffa", "Normal"), 174: ("Igglybuff", "Normal"), 175: ("Togepi", "Normal"),
    176: ("Togetic", "Normal"), 177: ("Natu", "Psychic"), 178: ("Xatu", "Psychic"),
    179: ("Mareep", "Electric"), 180: ("Flaaffy", "Electric"), 181: ("Ampharos", "Electric"),
    182: ("Bellossom", "Grass"), 183: ("Marill", "Water"), 184: ("Azumarill", "Water"),
    185: ("Sudowoodo", "Rock"), 186: ("Politoed", "Water"), 187: ("Hoppip", "Grass"),
    188: ("Skiploom", "Grass"), 189: ("Jumpluff", "Grass"), 190: ("Aipom", "Normal"),
    191: ("Sunkern", "Grass"), 192: ("Sunflora", "Grass"), 193: ("Yanma", "Bug"),
    194: ("Wooper", "Water"), 195: ("Quagsire", "Water"), 196: ("Espeon", "Psychic"),
    197: ("Umbreon", "Dark"), 198: ("Murkrow", "Dark"), 199: ("Slowking", "Water"),
    200: ("Misdreavus", "Ghost"), 201: ("Unown", "Psychic"), 202: ("Wobbuffet", "Psychic"),
    203: ("Girafarig", "Normal"), 204: ("Pineco", "Bug"), 205: ("Forretress", "Bug"),
    206: ("Dunsparce", "Normal"), 207: ("Gligar", "Ground"), 208: ("Steelix", "Steel"),
    209: ("Snubbull", "Normal"), 210: ("Granbull", "Normal"), 211: ("Qwilfish", "Water"),
    212: ("Scizor", "Bug"), 213: ("Shuckle", "Bug"), 214: ("Heracross", "Bug"),
    215: ("Sneasel", "Dark"), 216: ("Teddiursa", "Normal"), 217: ("Ursaring", "Normal"),
    218: ("Slugma", "Fire"), 219: ("Magcargo", "Fire"), 220: ("Swinub", "Ice"),
    221: ("Piloswine", "Ice"), 222: ("Corsola", "Water"), 223: ("Remoraid", "Water"),
    224: ("Octillery", "Water"), 225: ("Delibird", "Ice"), 226: ("Mantine", "Water"),
    227: ("Skarmory", "Steel"), 228: ("Houndour", "Dark"), 229: ("Houndoom", "Dark"),
    230: ("Kingdra", "Water"), 231: ("Phanpy", "Ground"), 232: ("Donphan", "Ground"),
    233: ("Porygon2", "Normal"), 234: ("Stantler", "Normal"), 235: ("Smeargle", "Normal"),
    236: ("Tyrogue", "Fighting"), 237: ("Hitmontop", "Fighting"), 238: ("Smoochum", "Ice"),
    239: ("Elekid", "Electric"), 240: ("Magby", "Fire"), 241: ("Miltank", "Normal"),
    242: ("Blissey", "Normal"), 243: ("Raikou", "Electric"), 244: ("Entei", "Fire"),
    245: ("Suicune", "Water"), 246: ("Larvitar", "Rock"), 247: ("Pupitar", "Rock"),
    248: ("Tyranitar", "Rock"), 249: ("Lugia", "Psychic"), 250: ("Ho-Oh", "Fire"),
    251: ("Celebi", "Psychic"),
    252: ("Treecko", "Grass"), 253: ("Grovyle", "Grass"), 254: ("Sceptile", "Grass"),
    255: ("Torchic", "Fire"), 256: ("Combusken", "Fire"), 257: ("Blaziken", "Fire"),
    258: ("Mudkip", "Water"), 259: ("Marshtomp", "Water"), 260: ("Swampert", "Water"),
    261: ("Poochyena", "Dark"), 262: ("Mightyena", "Dark"), 263: ("Zigzagoon", "Normal"),
    264: ("Linoone", "Normal"), 265: ("Wurmple", "Bug"), 266: ("Silcoon", "Bug"),
    267: ("Beautifly", "Bug"), 268: ("Cascoon", "Bug"), 269: ("Dustox", "Bug"),
    270: ("Lotad", "Water"), 271: ("Lombre", "Water"), 272: ("Ludicolo", "Water"),
    273: ("Seedot", "Grass"), 274: ("Nuzleaf", "Grass"), 275: ("Shiftry", "Grass"),
    276: ("Taillow", "Normal"), 277: ("Swellow", "Normal"), 278: ("Wingull", "Water"),
    279: ("Pelipper", "Water"), 280: ("Ralts", "Psychic"), 281: ("Kirlia", "Psychic"),
    282: ("Gardevoir", "Psychic"), 283: ("Surskit", "Bug"), 284: ("Masquerain", "Bug"),
    285: ("Shroomish", "Grass"), 286: ("Breloom", "Grass"), 287: ("Slakoth", "Normal"),
    288: ("Vigoroth", "Normal"), 289: ("Slaking", "Normal"), 290: ("Nincada", "Bug"),
    291: ("Ninjask", "Bug"), 292: ("Shedinja", "Bug"), 293: ("Whismur", "Normal"),
    294: ("Loudred", "Normal"), 295: ("Exploud", "Normal"), 296: ("Makuhita", "Fighting"),
    297: ("Hariyama", "Fighting"), 298: ("Azurill", "Normal"), 299: ("Nosepass", "Rock"),
    300: ("Skitty", "Normal"), 301: ("Delcatty", "Normal"), 302: ("Sableye", "Dark"),
    303: ("Mawile", "Steel"), 304: ("Aron", "Steel"), 305: ("Lairon", "Steel"),
    306: ("Aggron", "Steel"), 307: ("Meditite", "Fighting"), 308: ("Medicham", "Fighting"),
    309: ("Electrike", "Electric"), 310: ("Manectric", "Electric"), 311: ("Plusle", "Electric"),
    312: ("Minun", "Electric"), 313: ("Volbeat", "Bug"), 314: ("Illumise", "Bug"),
    315: ("Roselia", "Grass"), 316: ("Gulpin", "Poison"), 317: ("Swalot", "Poison"),
    318: ("Carvanha", "Water"), 319: ("Sharpedo", "Water"), 320: ("Wailmer", "Water"),
    321: ("Wailord", "Water"), 322: ("Numel", "Fire"), 323: ("Camerupt", "Fire"),
    324: ("Torkoal", "Fire"), 325: ("Spoink", "Psychic"), 326: ("Grumpig", "Psychic"),
    327: ("Spinda", "Normal"), 328: ("Trapinch", "Ground"), 329: ("Vibrava", "Ground"),
    330: ("Flygon", "Ground"), 331: ("Cacnea", "Grass"), 332: ("Cacturne", "Grass"),
    333: ("Swablu", "Normal"), 334: ("Altaria", "Dragon"), 335: ("Zangoose", "Normal"),
    336: ("Seviper", "Poison"), 337: ("Lunatone", "Rock"), 338: ("Solrock", "Rock"),
    339: ("Barboach", "Water"), 340: ("Whiscash", "Water"), 341: ("Corphish", "Water"),
    342: ("Crawdaunt", "Water"), 343: ("Baltoy", "Ground"), 344: ("Claydol", "Ground"),
    345: ("Lileep", "Rock"), 346: ("Cradily", "Rock"), 347: ("Anorith", "Rock"),
    348: ("Armaldo", "Rock"), 349: ("Feebas", "Water"), 350: ("Milotic", "Water"),
    351: ("Castform", "Normal"), 352: ("Kecleon", "Normal"), 353: ("Shuppet", "Ghost"),
    354: ("Banette", "Ghost"), 355: ("Duskull", "Ghost"), 356: ("Dusclops", "Ghost"),
    357: ("Tropius", "Grass"), 358: ("Chimecho", "Psychic"), 359: ("Absol", "Dark"),
    360: ("Wynaut", "Psychic"), 361: ("Snorunt", "Ice"), 362: ("Glalie", "Ice"),
    363: ("Spheal", "Ice"), 364: ("Sealeo", "Ice"), 365: ("Walrein", "Ice"),
    366: ("Clamperl", "Water"), 367: ("Huntail", "Water"), 368: ("Gorebyss", "Water"),
    369: ("Relicanth", "Water"), 370: ("Luvdisc", "Water"), 371: ("Bagon", "Dragon"),
    372: ("Shelgon", "Dragon"), 373: ("Salamence", "Dragon"), 374: ("Beldum", "Steel"),
    375: ("Metang", "Steel"), 376: ("Metagross", "Steel"), 377: ("Regirock", "Rock"),
    378: ("Regice", "Ice"), 379: ("Registeel", "Steel"), 380: ("Latias", "Dragon"),
    381: ("Latios", "Dragon"), 382: ("Kyogre", "Water"), 383: ("Groudon", "Ground"),
    384: ("Rayquaza", "Dragon"), 385: ("Jirachi", "Steel"), 386: ("Deoxys", "Psychic")
}
KANTO_MAPS = {
    0: "Pallet Town", 1: "Viridian City", 2: "Pewter City", 3: "Cerulean City",
    4: "Lavender Town", 5: "Vermilion City", 6: "Celadon City", 7: "Fuchsia City",
    8: "Cinnabar Island", 9: "Indigo Plateau", 10: "Saffron City",
    12: "Route 1", 13: "Route 2", 14: "Route 3", 15: "Route 4",
    16: "Route 5", 17: "Route 6", 18: "Route 7", 19: "Route 8",
    20: "Route 9", 21: "Route 10", 22: "Route 11", 23: "Route 12",
    24: "Route 13", 25: "Route 14", 26: "Route 15", 27: "Route 16",
    28: "Route 17", 29: "Route 18", 30: "Route 19", 31: "Route 20",
    32: "Route 21", 33: "Route 22", 34: "Route 23", 35: "Route 24",
    36: "Route 25", 51: "Viridian Forest", 59: "Mt. Moon", 82: "Rock Tunnel",
    108: "Pokemon Tower", 142: "Safari Zone", 159: "Seafoam Islands",
    194: "Victory Road", 197: "Diglett's Cave", 214: "Pokemon Mansion", 226: "Cerulean Cave"
}

HOENN_MAPS = {
    0: "Littleroot Town", 1: "Oldale Town", 2: "Dewford Town", 3: "Lavaridge Town",
    4: "Fallarbor Town", 5: "Verdanturf Town", 6: "Pacifidlog Town", 7: "Petalburg City",
    8: "Slateport City", 9: "Mauville City", 10: "Rustboro City", 11: "Fortree City",
    12: "Lilycove City", 13: "Mossdeep City", 14: "Sootopolis City", 15: "Ever Grande City",
    16: "Route 101", 17: "Route 102", 18: "Route 103", 19: "Route 104",
    20: "Route 105", 21: "Route 106", 22: "Route 107", 23: "Route 108",
    24: "Route 109", 25: "Route 110", 26: "Route 111", 27: "Route 112",
    28: "Route 113", 29: "Route 114", 30: "Route 115", 31: "Route 116",
    32: "Route 117", 33: "Route 118", 34: "Route 119", 35: "Route 120",
    36: "Route 121", 37: "Route 122", 38: "Route 123", 39: "Route 124",
    40: "Route 125", 41: "Route 126", 42: "Route 127", 43: "Route 128",
    44: "Route 129", 45: "Route 130", 46: "Route 131", 47: "Route 132",
    48: "Route 133", 49: "Route 134",
    257: "Route 101", 258: "Oldale Town", 259: "Route 102",
    260: "Petalburg City", 261: "Route 104", 262: "Petalburg Woods", 263: "Rustboro City",
    264: "Route 116", 265: "Rusturf Tunnel", 266: "Route 103", 267: "Granite Cave",
    268: "Route 110", 269: "Mauville City", 270: "Route 117", 271: "Route 111",
    272: "Fiery Path", 273: "Route 112", 274: "Route 113", 275: "Route 114",
    276: "Meteor Falls", 277: "Route 115", 278: "Jagged Pass", 279: "Route 118",
    280: "Route 119", 281: "Route 120", 282: "Route 121", 283: "Mt. Pyre",
    284: "Route 123", 285: "Safari Zone", 286: "Route 124", 287: "Route 125",
    288: "Shoal Cave", 289: "Route 126", 290: "Route 127", 291: "Route 128",
    292: "Seafloor Cavern", 293: "Cave of Origin", 294: "Victory Road",
    4096: "Route 101", 4352: "Route 102", 4608: "Route 103", 4864: "Route 104",
    5120: "Route 105", 5376: "Route 106", 5632: "Route 107", 5888: "Route 108",
    6144: "Route 109", 6400: "Route 110", 6656: "Route 111", 6912: "Route 112",
    7168: "Route 113", 7424: "Route 114", 7680: "Route 115", 7936: "Route 116",
    8192: "Route 117", 8448: "Route 118", 8704: "Route 119", 8960: "Route 120",
    9216: "Route 121", 9472: "Route 122", 9728: "Route 123", 9984: "Route 124",
    10240: "Route 125", 10496: "Route 126", 10752: "Route 127", 11008: "Route 128",
    11264: "Route 129", 11520: "Route 130", 11776: "Route 131", 12032: "Route 132",
    12288: "Route 133", 12544: "Route 134",
    256: "Oldale Town", 512: "Dewford Town", 768: "Lavaridge Town",
    1024: "Fallarbor Town", 1280: "Verdanturf Town", 1536: "Pacifidlog Town",
    1792: "Petalburg City", 2048: "Slateport City", 2304: "Mauville City",
    2560: "Rustboro City", 2816: "Fortree City", 3072: "Lilycove City",
    3328: "Mossdeep City", 3584: "Sootopolis City", 3840: "Ever Grande City",
}


TYPE_ORDER = [
    "Normal", "Fire", "Water", "Electric", "Grass", "Ice", "Fighting", "Poison",
    "Ground", "Flying", "Psychic", "Bug", "Rock", "Ghost", "Dragon", "Dark", "Steel"
]

TYPE_COLORS = {
    "Normal": "#A8A77A", "Fire": "#EE8130", "Water": "#6390F0", "Electric": "#F7D02C",
    "Grass": "#7AC74C", "Ice": "#96D9D6", "Fighting": "#C22E28", "Poison": "#A33EA1",
    "Ground": "#E2BF65", "Flying": "#A98FF3", "Psychic": "#F95587", "Bug": "#A6B91A",
    "Rock": "#B6A136", "Ghost": "#735797", "Dragon": "#6F35FC", "Dark": "#705746",
    "Steel": "#B7B7CE", "Unknown": "#6c7086"
}

TYPE_CHART = {
    "Normal":   {"Rock": 0.5, "Ghost": 0.0, "Steel": 0.5},
    "Fire":     {"Fire": 0.5, "Water": 0.5, "Grass": 2.0, "Ice": 2.0, "Bug": 2.0, "Rock": 0.5, "Dragon": 0.5, "Steel": 2.0},
    "Water":    {"Fire": 2.0, "Water": 0.5, "Grass": 0.5, "Ground": 2.0, "Rock": 2.0, "Dragon": 0.5},
    "Electric": {"Water": 2.0, "Electric": 0.5, "Grass": 0.5, "Ground": 0.0, "Flying": 2.0, "Dragon": 0.5},
    "Grass":    {"Fire": 0.5, "Water": 2.0, "Grass": 0.5, "Poison": 0.5, "Ground": 2.0, "Flying": 0.5, "Bug": 0.5, "Rock": 2.0, "Dragon": 0.5, "Steel": 0.5},
    "Ice":      {"Fire": 0.5, "Water": 0.5, "Grass": 2.0, "Ice": 0.5, "Ground": 2.0, "Flying": 2.0, "Dragon": 2.0, "Steel": 0.5},
    "Fighting": {"Normal": 2.0, "Ice": 2.0, "Poison": 0.5, "Flying": 0.5, "Psychic": 0.5, "Bug": 0.5, "Rock": 2.0, "Ghost": 0.0, "Dark": 2.0, "Steel": 2.0},
    "Poison":   {"Grass": 2.0, "Poison": 0.5, "Ground": 0.5, "Rock": 0.5, "Ghost": 0.5, "Steel": 0.0},
    "Ground":   {"Fire": 2.0, "Electric": 2.0, "Grass": 0.5, "Poison": 2.0, "Flying": 0.0, "Bug": 0.5, "Rock": 2.0, "Steel": 2.0},
    "Flying":   {"Electric": 0.5, "Grass": 2.0, "Fighting": 2.0, "Bug": 2.0, "Rock": 0.5, "Steel": 0.5},
    "Psychic":  {"Fighting": 2.0, "Poison": 2.0, "Psychic": 0.5, "Dark": 0.0, "Steel": 0.5},
    "Bug":      {"Fire": 0.5, "Grass": 2.0, "Fighting": 0.5, "Poison": 0.5, "Flying": 0.5, "Psychic": 2.0, "Ghost": 0.5, "Dark": 2.0, "Steel": 0.5},
    "Rock":     {"Fire": 2.0, "Ice": 2.0, "Fighting": 0.5, "Ground": 0.5, "Flying": 2.0, "Bug": 2.0, "Steel": 0.5},
    "Ghost":    {"Normal": 0.0, "Psychic": 2.0, "Ghost": 2.0, "Dark": 0.5, "Steel": 0.5},
    "Dragon":   {"Dragon": 2.0, "Steel": 0.5},
    "Dark":     {"Fighting": 0.5, "Psychic": 2.0, "Ghost": 2.0, "Dark": 0.5, "Steel": 0.5},
    "Steel":    {"Fire": 0.5, "Water": 0.5, "Electric": 0.5, "Ice": 2.0, "Rock": 2.0, "Steel": 0.5}
}


def safe_tk_text(val):
    if val is None:
        return ""
    return "".join(ch if ord(ch) < 65536 else "?" for ch in str(val))


def get_species_and_type(species_id, raw_type1=-1):
    sp_name, t_name = SPECIES_DATA.get(species_id, (f"Species #{species_id}", "Unknown"))
    if t_name == "Unknown" and raw_type1 in GEN1_TYPES:
        t_name = GEN1_TYPES[raw_type1]
    return sp_name, t_name


def resolve_area_name(gen, sub, map_id):
    if gen == 3 and sub == "RSE" and map_id in HOENN_MAPS:
        return HOENN_MAPS[map_id]
    if map_id in KANTO_MAPS:
        return KANTO_MAPS[map_id]
    return f"Area #{map_id}"
class SoulLinkHubApp:
    def __init__(self, root):
        self.root = root
        self.is_mac = (sys.platform == "darwin")
        self.bg_main  = "#eceff4" if self.is_mac else "#1e1e2e"
        self.bg_card  = "#e5e9f0" if self.is_mac else "#181825"
        self.bg_input = "#ffffff" if self.is_mac else "#313244"
        self.fg_text  = "#11111b" if self.is_mac else "#ffffff"
        self.fg_title = "#5e35b1" if self.is_mac else "#cba6f7"
        self.fg_sub   = "#b45309" if self.is_mac else "#f9e2af"

        self.root.title(f"Soul Link Companion Hub — [{ACTIVE_PROFILE}]")
        self.root.geometry("580x850")

        try:
            icon_path = os.path.join(BUNDLE_DIR, "icon.ico")
            self.root.iconbitmap(icon_path)
        except Exception:
            passs

        if self.is_mac:
            sw = self.root.winfo_screenwidth()
            sh = max(650, self.root.winfo_screenheight() - 60)
            hub_w = 580
            hub_x = max(400, sw - hub_w) if NET_MODE in ("host", "join") else max(320, (sw - hub_w) // 2)
            self.root.geometry(f"{hub_w}x{sh}+{hub_x}+28")

        self.root.configure(bg=self.bg_main)

        self.lock = threading.RLock()
        self.clients = {}
        self.parties = {1: [], 2: []}
        self.known_uids = {1: set(), 2: set()}
        self.seen_uids = {1: set(), 2: set()}
        self.active_battle = {1: None, 2: None}
        self.battle_end_ticks = {1: 0, 2: 0}
        self.unlocked_balls = {1: False, 2: False}
        self.box_baselined = {1: False, 2: False}
        self.prev_box = {1: None, 2: None}   # Gen 1/2: (box_id, set of uids) of the open box
        self.player_gens = {1: 1, 2: 1}
        self.player_regions = {1: "KANTO", 2: "KANTO"}
        self.rendered_chart_gens = {1: None, 2: None}
        self.manual_chart_override = {1: False, 2: False}

        self.pairs = []
        self.routes = {}
        self.nickname_rule_enabled = tk.BooleanVar(value=True)
        self.nickname_rule_bool = True
        self.type_rule_enabled = tk.BooleanVar(value=True)
        self.type_rule_bool = True
        self.net_status_text = "Mode: Local Co-Op"
        self.stun_peer = None

        self.build_ui()
        if NET_MODE != "join":
            self.load_project()
        self.start_socket_server()
        if NET_MODE in ("host", "join"):
            self.start_online_p2p()
        self.refresh_ui_loop()

    def build_ui(self):
        hdr = tk.Frame(self.root, bg=self.bg_card, pady=8)
        hdr.pack(fill="x")
        tk.Label(
            hdr, text=f"SOUL LINK COMPANION — {safe_tk_text(ACTIVE_PROFILE).upper()}",
            font=("Segoe UI", 12, "bold"), bg=self.bg_card, fg=self.fg_title
        ).pack()

        status_row = tk.Frame(hdr, bg=self.bg_card)
        status_row.pack(pady=3)
        self.lbl_conn = tk.Label(status_row, text="Connected Windows: 0 / 2", font=("Segoe UI", 9, "bold"), bg=self.bg_card, fg="#f38ba8")
        self.lbl_conn.pack(side="left", padx=8)

        tk.Checkbutton(
            status_row, text="Rule 3: Nicknames",
            variable=self.nickname_rule_enabled,
            command=self.on_toggle_rules,
            bg=self.bg_card, fg=self.fg_sub, selectcolor=self.bg_input,
            activebackground=self.bg_card, activeforeground=self.fg_sub,
            font=("Segoe UI", 8, "bold")
        ).pack(side="left", padx=6)

        tk.Checkbutton(
            status_row, text="Rule 5: No Type Dups",
            variable=self.type_rule_enabled,
            command=self.on_toggle_rules,
            bg=self.bg_card, fg=self.fg_sub, selectcolor=self.bg_input,
            activebackground=self.bg_card, activeforeground=self.fg_sub,
            font=("Segoe UI", 8, "bold")
        ).pack(side="left", padx=6)

        if NET_MODE in ("host", "join"):
            net_bar = tk.Frame(hdr, bg=self.bg_card, pady=3)
            net_bar.pack(fill="x", padx=12)
            self.lbl_net = tk.Label(net_bar, text="Starting STUN P2P...", font=("Segoe UI", 8, "bold"), bg=self.bg_card, fg="#89b4fa")
            self.lbl_net.pack(side="left")

            tk.Button(
                net_bar, text="1. Copy My Code",
                command=self.copy_my_room_code,
                bg="#89b4fa", fg="#11111b", font=("Segoe UI", 8, "bold"), relief="flat", padx=6
            ).pack(side="right", padx=(4, 0))

            tk.Button(
                net_bar, text="2. Connect Code",
                command=self.connect_peer_code_from_entry,
                bg="#a6e3a1", fg="#11111b", font=("Segoe UI", 8, "bold"), relief="flat", padx=6
            ).pack(side="right", padx=4)

            self.peer_code_var = tk.StringVar()
            ent = tk.Entry(net_bar, textvariable=self.peer_code_var, width=15, bg=self.bg_input, fg=self.fg_text, insertbackground=self.fg_text, font=("Consolas", 9))
            ent.pack(side="right", padx=4)
            ent.bind("<Return>", lambda e: self.connect_peer_code_from_entry())
        else:
            self.lbl_net = tk.Label(hdr, text="Mode: Local Co-Op", font=("Segoe UI", 8, "bold"), bg=self.bg_card, fg="#89b4fa")
            self.lbl_net.pack()

        self.alert_banner = tk.Label(
            self.root, text="All Active Soul Link Rules Satisfied!",
            font=("Segoe UI", 10, "bold"), bg="#15803d" if self.is_mac else "#1e3a2f",
            fg="#ffffff" if self.is_mac else "#a6e3a1", pady=6
        )
        self.alert_banner.pack(fill="x", padx=10, pady=(6, 4))

        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass
        style.configure("TNotebook", background=self.bg_main, borderwidth=0)
        style.configure("TNotebook.Tab", background=self.bg_input, foreground=self.fg_text, padding=[10, 4], font=("Segoe UI", 9, "bold"))
        style.map("TNotebook.Tab", background=[("selected", "#cba6f7")], foreground=[("selected", "#11111b")])

        self.tabs = ttk.Notebook(self.root)
        self.tabs.pack(fill="both", expand=True, padx=10, pady=4)

        self.tab_parties = tk.Frame(self.tabs, bg=self.bg_main)
        self.tab_routes  = tk.Frame(self.tabs, bg=self.bg_main)
        self.tab_pairs   = tk.Frame(self.tabs, bg=self.bg_main)
        self.tab_chart1  = tk.Frame(self.tabs, bg=self.bg_main)
        self.tab_chart2  = tk.Frame(self.tabs, bg=self.bg_main)

        self.tabs.add(self.tab_parties, text="Live Parties")
        self.tabs.add(self.tab_routes,  text="Encounters")
        self.tabs.add(self.tab_pairs,   text="Pairs Log")
        self.tabs.add(self.tab_chart1,  text="P1 Type Chart")
        self.tabs.add(self.tab_chart2,  text="P2 Type Chart")

        self.build_parties_tab()
        self.build_routes_tab()
        self.build_pairs_tab()
        self.build_type_chart_tab(1, self.tab_chart1)
        self.build_type_chart_tab(2, self.tab_chart2)
    def build_parties_tab(self):
        container = tk.Frame(self.tab_parties, bg=self.bg_main)
        container.pack(fill="both", expand=True, pady=4)
        self.slot_widgets = {1: [], 2: []}

        for p_id, title in ((1, "PLAYER 1 (HOST)"), (2, "PLAYER 2 (GUEST)")):
            col = tk.Frame(container, bg=self.bg_card, padx=6, pady=6)
            col.pack(side="left", fill="both", expand=True, padx=4)
            tk.Label(col, text=title, font=("Segoe UI", 10, "bold"), bg=self.bg_card, fg="#89b4fa").pack(pady=(0, 4))

            for s in range(6):
                card = tk.Frame(col, bg=self.bg_input, padx=6, pady=4)
                card.pack(fill="x", pady=3)
                top = tk.Frame(card, bg=self.bg_input)
                top.pack(fill="x")
                lbl_name = tk.Label(top, text=f"Slot {s+1}: Empty", font=("Segoe UI", 9, "bold"), bg=self.bg_input, fg=self.fg_text, anchor="w")
                lbl_name.pack(side="left")
                lbl_type = tk.Label(top, text="", font=("Segoe UI", 7, "bold"), bg=self.bg_input, fg="#11111b", padx=5)
                lbl_type.pack(side="right")

                lbl_sub = tk.Label(card, text="Waiting for emulator...", font=("Segoe UI", 8), bg=self.bg_input, fg="#9399b2", anchor="w")
                lbl_sub.pack(fill="x")
                self.slot_widgets[p_id].append((lbl_name, lbl_type, lbl_sub))

        ctrl = tk.Frame(self.tab_parties, bg=self.bg_card, pady=6, padx=8)
        ctrl.pack(fill="x", pady=(4, 0))
        tk.Label(ctrl, text="Manual Link / Unlink:", font=("Segoe UI", 8, "bold"), bg=self.bg_card, fg=self.fg_sub).pack(side="left", padx=(0, 6))
        self.var_p1_slot = tk.StringVar(value="P1 Slot 1")
        self.var_p2_slot = tk.StringVar(value="P2 Slot 1")
        ttk.Combobox(ctrl, textvariable=self.var_p1_slot, values=[f"P1 Slot {i}" for i in range(1, 7)], width=9, state="readonly").pack(side="left", padx=2)
        ttk.Combobox(ctrl, textvariable=self.var_p2_slot, values=[f"P2 Slot {i}" for i in range(1, 7)], width=9, state="readonly").pack(side="left", padx=2)
        tk.Button(ctrl, text="Link", command=self.link_selected_slots, bg="#a6e3a1", fg="#11111b", font=("Segoe UI", 8, "bold"), relief="flat", padx=8).pack(side="left", padx=4)
        tk.Button(ctrl, text="Unlink", command=self.unlink_selected_slots, bg="#f38ba8", fg="#11111b", font=("Segoe UI", 8, "bold"), relief="flat", padx=8).pack(side="left", padx=2)

    def build_routes_tab(self):
        tk.Label(self.tab_routes, text="First Wild / Starter / Gift Encounter per Area (Rule 2, 4 & 7):", font=("Segoe UI", 9, "bold"), bg=self.bg_main, fg=self.fg_sub).pack(anchor="w", pady=(6, 4))
        self.route_list = tk.Listbox(self.tab_routes, bg=self.bg_card, fg=self.fg_text, font=("Consolas", 8), selectbackground="#cba6f7", selectforeground="#11111b", exportselection=False)
        self.route_list.pack(fill="both", expand=True)
        tk.Button(self.tab_routes, text="Reset Selected Route Encounter", command=self.reset_selected_route, bg="#fab387", fg="#11111b", font=("Segoe UI", 9, "bold"), relief="flat", pady=5).pack(fill="x", pady=6)

    def build_pairs_tab(self):
        tk.Label(self.tab_pairs, text="Active & Fallen Soul Link Pairs:", font=("Segoe UI", 9, "bold"), bg=self.bg_main, fg=self.fg_sub).pack(anchor="w", pady=(6, 4))
        self.pair_list = tk.Listbox(self.tab_pairs, bg=self.bg_card, fg=self.fg_text, font=("Consolas", 9), selectbackground="#cba6f7", selectforeground="#11111b", exportselection=False)
        self.pair_list.pack(fill="both", expand=True)
        tk.Button(self.tab_pairs, text="Delete Selected Pair", command=self.delete_selected_pair, bg="#f38ba8", fg="#11111b", font=("Segoe UI", 9, "bold"), relief="flat", pady=5).pack(fill="x", pady=6)

    def build_type_chart_tab(self, player_id, parent):
        top = tk.Frame(parent, bg=self.bg_card, pady=5, padx=8)
        top.pack(fill="x", pady=(4, 2))
        lbl = tk.Label(top, text=f"Player {player_id} Type Chart (Gen 1 Rules)", font=("Segoe UI", 9, "bold"), bg=self.bg_card, fg=self.fg_title)
        lbl.pack(side="left")

        btn_f = tk.Frame(top, bg=self.bg_card)
        btn_f.pack(side="right")
        for g_num in (1, 2, 3):
            tk.Button(
                btn_f, text=f"Gen {g_num}",
                command=lambda g=g_num, pid=player_id: self.set_manual_chart_gen(pid, g),
                bg="#45475a", fg="#ffffff", font=("Segoe UI", 7, "bold"), relief="flat", padx=5
            ).pack(side="left", padx=2)

        # Dual-Type Defender Calculator Bar
        calc_card = tk.Frame(parent, bg=self.bg_card, padx=8, pady=6)
        calc_card.pack(fill="x", pady=3)
        row1 = tk.Frame(calc_card, bg=self.bg_card)
        row1.pack(fill="x")
        tk.Label(row1, text="Dual-Type Calculator:", font=("Segoe UI", 8, "bold"), bg=self.bg_card, fg=self.fg_sub).pack(side="left", padx=(0, 6))

        if not hasattr(self, "calc_t1_vars"):
            self.calc_t1_vars = {}
            self.calc_t2_vars = {}
            self.calc_res_labels = {}
            self.chart_containers = {}
            self.chart_labels = {}

        v1 = tk.StringVar(value="Water")
        v2 = tk.StringVar(value="None")
        self.calc_t1_vars[player_id] = v1
        self.calc_t2_vars[player_id] = v2

        cb1 = ttk.Combobox(row1, textvariable=v1, values=TYPE_ORDER, width=10, state="readonly")
        cb1.pack(side="left", padx=3)
        cb2 = ttk.Combobox(row1, textvariable=v2, values=["None"] + TYPE_ORDER, width=10, state="readonly")
        cb2.pack(side="left", padx=3)

        res_lbl = tk.Label(calc_card, text="", font=("Segoe UI", 8), bg=self.bg_card, fg=self.fg_text, justify="left", wraplength=530, anchor="w")
        res_lbl.pack(fill="x", pady=(4, 0))
        self.calc_res_labels[player_id] = res_lbl

        cb1.bind("<<ComboboxSelected>>", lambda e, pid=player_id: self.update_dual_type_calc(pid))
        cb2.bind("<<ComboboxSelected>>", lambda e, pid=player_id: self.update_dual_type_calc(pid))

        grid_frame = tk.Frame(parent, bg=self.bg_main)
        grid_frame.pack(fill="both", expand=True, pady=2)
        self.chart_containers[player_id] = grid_frame
        self.chart_labels[player_id] = lbl
        self.render_type_chart_grid(player_id, 1)

    def get_pair_multiplier(self, atk_t, def_t, gen_num):
        mult = TYPE_CHART.get(atk_t, {}).get(def_t, 1.0)
        if gen_num == 1 and atk_t == "Ghost" and def_t == "Psychic":
            mult = 0.0
        if gen_num == 1 and atk_t == "Bug" and def_t == "Poison":
            mult = 2.0
        if gen_num == 1 and atk_t == "Poison" and def_t == "Bug":
            mult = 2.0
        if gen_num == 1 and atk_t == "Ice" and def_t == "Fire":
            mult = 1.0
        return mult

    def update_dual_type_calc(self, player_id):
        gen_num = self.player_gens.get(player_id, 1)
        t1 = self.calc_t1_vars[player_id].get()
        t2 = self.calc_t2_vars[player_id].get()
        active_types = [t for t in TYPE_ORDER if not (gen_num == 1 and t in ("Dark", "Steel"))]

        buckets = {4.0: [], 2.0: [], 0.5: [], 0.25: [], 0.0: []}
        for atk in active_types:
            m1 = self.get_pair_multiplier(atk, t1, gen_num)
            m2 = 1.0 if (t2 == "None" or t2 == t1) else self.get_pair_multiplier(atk, t2, gen_num)
            tot = m1 * m2
            if tot in buckets:
                buckets[tot].append(atk)

        parts = []
        if buckets[4.0]:
            parts.append("4x Weak: " + ", ".join(buckets[4.0]))
        if buckets[2.0]:
            parts.append("2x Weak: " + ", ".join(buckets[2.0]))
        if buckets[0.5]:
            parts.append("½x Resist: " + ", ".join(buckets[0.5]))
        if buckets[0.25]:
            parts.append("¼x Resist: " + ", ".join(buckets[0.25]))
        if buckets[0.0]:
            parts.append("0x Immune: " + ", ".join(buckets[0.0]))

        self.calc_res_labels[player_id].config(text="  |  ".join(parts) if parts else "1x Neutral to all types")

    def set_manual_chart_gen(self, player_id, gen_num):
        self.manual_chart_override[player_id] = True
        self.player_gens[player_id] = gen_num
        self.render_type_chart_grid(player_id, gen_num)

    def render_type_chart_grid(self, player_id, gen_num):
        self.rendered_chart_gens[player_id] = gen_num
        self.chart_labels[player_id].config(text=f"Player {player_id} Type Chart (Gen {gen_num} Rules)")
        if hasattr(self, "calc_res_labels") and player_id in self.calc_res_labels:
            self.update_dual_type_calc(player_id)

        frame = self.chart_containers[player_id]
        for child in frame.winfo_children():
            child.destroy()

        active_types = [t for t in TYPE_ORDER if not (gen_num == 1 and t in ("Dark", "Steel"))]
        tk.Label(frame, text="ATK\\DEF", font=("Segoe UI", 6, "bold"), bg=self.bg_card, fg=self.fg_text, width=6).grid(row=0, column=0, padx=1, pady=1)
        for c_idx, def_t in enumerate(active_types, start=1):
            tk.Label(frame, text=def_t[:3].upper(), font=("Segoe UI", 6, "bold"), bg=TYPE_COLORS.get(def_t, "#555"), fg="#11111b", width=3).grid(row=0, column=c_idx, padx=1, pady=1)

        for r_idx, atk_t in enumerate(active_types, start=1):
            tk.Label(frame, text=atk_t[:3].upper(), font=("Segoe UI", 6, "bold"), bg=TYPE_COLORS.get(atk_t, "#555"), fg="#11111b", width=6).grid(row=r_idx, column=0, padx=1, pady=1)
            for c_idx, def_t in enumerate(active_types, start=1):
                mult = self.get_pair_multiplier(atk_t, def_t, gen_num)
                if mult == 2.0:
                    txt, bg_c, fg_c = "2x", "#a6e3a1", "#11111b"
                elif mult == 0.5:
                    txt, bg_c, fg_c = "½", "#f38ba8", "#11111b"
                elif mult == 0.0:
                    txt, bg_c, fg_c = "0", "#11111b", "#cdd6f4"
                else:
                    txt, bg_c, fg_c = "", self.bg_card, self.fg_text
                tk.Label(frame, text=txt, font=("Segoe UI", 6, "bold"), bg=bg_c, fg=fg_c, width=3).grid(row=r_idx, column=c_idx, padx=1, pady=1)

    def start_socket_server(self):
        def server_worker():
            srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            srv.bind(("127.0.0.1", 55355))
            srv.listen(4)
            while True:
                try:
                    conn, _ = srv.accept()
                    threading.Thread(target=self.handle_mgba_client, args=(conn,), daemon=True).start()
                except Exception:
                    time.sleep(0.5)

        threading.Thread(target=server_worker, daemon=True).start()

    def handle_mgba_client(self, conn):
        player_id = None
        with self.lock:
            if NET_MODE in ("host", "join"):
                player_id = 1
            else:
                player_id = 1 if 1 not in self.clients else 2
            self.clients[player_id] = conn

        try:
            assign_msg = json.dumps({"action": "ASSIGN", "player": player_id}) + "\n"
            conn.sendall(assign_msg.encode("utf-8"))
        except Exception:
            pass

        buf = ""
        try:
            while True:
                chunk = conn.recv(4096)
                if not chunk:
                    break
                buf += chunk.decode("utf-8", errors="ignore")
                while "\n" in buf:
                    line, buf = buf.split("\n", 1)
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        pkt = json.loads(line)
                        if NET_MODE == "join":
                            with self.lock:
                                self.parties[1] = pkt.get("party", [])
                                self.player_gens[1] = pkt.get("gen", 1)
                            if self.stun_peer:
                                self.stun_peer.send_json({"net_type": "P2_STATE", "payload": pkt})
                        else:
                            self.process_player_packet(player_id, pkt)
                            if NET_MODE == "host":
                                self.broadcast_state_to_guest()
                    except Exception:
                        pass
        finally:
            with self.lock:
                if self.clients.get(player_id) is conn:
                    del self.clients[player_id]
            try:
                conn.close()
            except Exception:
                pass
    def start_online_p2p(self):
        if not StunUdpPeer:
            self.net_status_text = "stun_p2p.py missing!"
            return
        try:
            self.stun_peer = StunUdpPeer(self.on_stun_message, self.on_stun_status)
            if self.stun_peer.local_code:
                upnp_tag = " (UPnP ✓)" if getattr(self.stun_peer, "upnp_active", False) else ""
                self.net_status_text = f"Code Ready{upnp_tag} — Share & Connect!"
            else:
                self.net_status_text = "STUN Unreachable (Check Firewall)"
        except Exception as e:
            self.net_status_text = f"Net Error: {e}"

    def on_stun_status(self, text):
        self.net_status_text = text

    def copy_my_room_code(self):
        if not self.stun_peer or not self.stun_peer.local_code:
            messagebox.showwarning("Room Code Unavailable", "STUN could not discover your public IP/port yet.")
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(self.stun_peer.local_code)
        self.root.update()
        self.net_status_text = f"Copied: {self.stun_peer.local_code}"

    def connect_peer_code_from_entry(self):
        if not self.stun_peer:
            return
        code = self.peer_code_var.get().strip()
        if not code:
            return
        try:
            self.stun_peer.set_peer_code(code)
            if NET_MODE == "host":
                self.broadcast_state_to_guest()
        except Exception:
            messagebox.showerror("Invalid Code", "Please paste a valid SL-... Room Code (or IP:Port).")

    def broadcast_state_to_guest(self):
        if NET_MODE != "host" or not self.stun_peer:
            return
        with self.lock:
            p1_list = list(self.parties.get(1, ()))
            p2_list = list(self.parties.get(2, ()))
            compact_routes = {}
            for rk, rv in self.routes.items():
                compact_routes[rk] = {
                    "name": rv.get("name", rk),
                    "p1": {"status": rv.get("p1", {}).get("status", "Pending"), "uid": rv.get("p1", {}).get("uid")},
                    "p2": {"status": rv.get("p2", {}).get("status", "Pending"), "uid": rv.get("p2", {}).get("uid")},
                }
            pg_dict = {str(k): v for k, v in self.player_gens.items()}
            pr_dict = {str(k): v for k, v in self.player_regions.items()}
            pkg = {
                "net_type": "HUB_SYNC",
                "run_name": ACTIVE_PROFILE,
                "parties": {1: p1_list, 2: p2_list},
                "pairs": list(self.pairs),
                "routes": compact_routes,
                "player_gens": pg_dict,
                "player_regions": pr_dict,
                "nickname_rule": self.nickname_rule_bool,
                "type_rule": self.type_rule_bool
            }
        self.stun_peer.send_json(pkg)

    def _mac_post_launch_lua(self, lua_script):
        time.sleep(1.6)
        try:
            subprocess.run(["pbcopy"], input=lua_script.encode("utf-8"), check=False)
        except Exception:
            pass
        applescript = '''
        tell application "mGBA" to activate
        delay 0.6
        tell application "System Events"
            tell process "mGBA"
                click menu item "Scripting..." of menu "Tools" of menu bar 1
                delay 0.7
                click menu item "Load script..." of menu "File" of menu bar 1
                delay 0.7
                keystroke "g" using {command down, shift down}
                delay 0.5
                keystroke "v" using {command down}
                delay 0.3
                keystroke return
                delay 0.5
                keystroke return
                delay 0.5
                if exists window "Scripting" then
                    try
                        perform action "AXPress" of (first button of window "Scripting" whose subrole is "AXCloseButton")
                    on error
                        keystroke "w" using {command down}
                    end try
                end if
            end tell
        end tell
        '''
        try:
            subprocess.run(["osascript", "-e", applescript], check=False)
        except Exception:
            pass

    def launch_guest_mgba_for_run(self, run_name):
        if getattr(self, "guest_mgba_launched", False):
            return
        self.guest_mgba_launched = True
        self.root.title(f"Soul Link Companion Hub — [{run_name}]")

        profiles_path = os.path.join(os.path.dirname(SAVE_FILE), "profiles.json")
        pdata = {}
        if os.path.exists(profiles_path):
            try:
                with open(profiles_path, "r", encoding="utf-8") as f:
                    pdata = json.load(f)
            except Exception:
                pdata = {}

        slug = "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in run_name).strip("_") or "Guest_Run"
        saves_dir = os.path.join(os.path.dirname(SAVE_FILE), "saves")
        os.makedirs(saves_dir, exist_ok=True)
        guest_save = os.path.join(saves_dir, f"{slug}_P2_online.sav")

        guest_runs = pdata.setdefault("guest_runs", {})
        entry = guest_runs.get(slug, {})
        played_before = bool(entry)
        guest_rom = entry.get("rom", "")

        if not guest_rom or not os.path.exists(guest_rom):
            guest_rom = filedialog.askopenfilename(
                title=f"[{run_name}] Select YOUR ROM (Save: {slug}_P2_online.sav)",
                filetypes=(("GB/GBC/GBA ROMs", "*.gb *.gbc *.gba"), ("All Files", "*.*"))
            )
            if not guest_rom:
                self.guest_mgba_launched = False
                return
            guest_runs[slug] = {"run_name": run_name, "rom": guest_rom, "save": guest_save}
            try:
                with open(profiles_path, "w", encoding="utf-8") as f:
                    json.dump(pdata, f, indent=2)
            except Exception:
                pass

        mgba_exe = pdata.get("mgba_exe", "")
        if not mgba_exe or not os.path.exists(mgba_exe):
            return

        bundle_dir = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
        lua_script = os.path.normpath(os.path.join(bundle_dir, "soullink_p1.lua"))

        try:
            from launch_soullink import ensure_save_directory, prepare_instance_script
            migrated = guest_save + "_files"
            if os.path.isdir(migrated) and not os.path.isfile(guest_save):
                guest_save = migrated
            first_folder = not os.path.exists(guest_save)
            guest_save = ensure_save_directory(guest_save, guest_rom)
            if first_folder and played_before:
                # An earlier session may have saved next to the ROM: copy it in.
                rom_save = os.path.splitext(guest_rom)[0] + ".sav"
                if os.path.isfile(rom_save):
                    shutil.copy2(rom_save, os.path.join(guest_save, os.path.basename(rom_save)))
            lua_script = prepare_instance_script(lua_script, guest_save)
        except Exception as exc:
            print(f"[SoulLink] Could not prepare the guest save folder: {exc}")

        if self.is_mac:
            app_bundle = None
            if ".app/Contents/MacOS/" in mgba_exe:
                prefix, _ = mgba_exe.split(".app/Contents/MacOS/", 1)
                app_bundle = prefix + ".app"
            if app_bundle:
                subprocess.Popen(["open", "-n", "-a", app_bundle, guest_rom, "--args", "-C", f"savegamePath={guest_save}"], start_new_session=True)
            else:
                subprocess.Popen([mgba_exe, "-C", f"savegamePath={guest_save}", guest_rom], start_new_session=True)
            threading.Thread(target=self._mac_post_launch_lua, args=(lua_script,), daemon=True).start()
        else:
            subprocess.Popen([mgba_exe, "-C", f"savegamePath={guest_save}", guest_rom], start_new_session=True)
            try:
                from launch_soullink import load_lua_into_mgba, position_windows
                import pygetwindow as gw
                position_windows(expected_mgba_count=1)
                time.sleep(0.4)
                mgba_wins = [w for w in gw.getAllWindows() if "mGBA" in w.title and "Scripting" not in w.title]
                if mgba_wins:
                    load_lua_into_mgba(next(iter(mgba_wins)), lua_script)
            except Exception:
                pass
    def on_stun_message(self, msg):
        should_sync = False
        faint_payload = None
        local_mgba = None
        with self.lock:
            if NET_MODE == "host":
                ntype = msg.get("net_type")
                if ntype == "P2_STATE":
                    self.process_player_packet(2, msg.get("payload", {}))
                    should_sync = True
                elif ntype == "GUEST_CMD":
                    cmd = msg.get("cmd")
                    if cmd == "SET_RULES":
                        self.nickname_rule_bool = bool(msg.get("nickname_rule", True))
                        self.type_rule_bool = bool(msg.get("type_rule", True))
                        self.pending_nickname_rule = self.nickname_rule_bool
                        self.pending_type_rule = self.type_rule_bool
                        self.save_project()
                        should_sync = True
                    elif cmd == "LINK_SLOTS":
                        s1, s2 = int(msg.get("s1", 0)), int(msg.get("s2", 0))
                        p1_list, p2_list = self.parties.get(1, ()), self.parties.get(2, ())
                        if s1 < len(p1_list) and s2 < len(p2_list):
                            self.create_link("Manual Link", p1_list[s1], p2_list[s2])
                            should_sync = True
                    elif cmd == "UNLINK_SLOTS":
                        s1, s2 = int(msg.get("s1", 0)), int(msg.get("s2", 0))
                        p1_list, p2_list = self.parties.get(1, ()), self.parties.get(2, ())
                        u1 = p1_list[s1]["uid"] if s1 < len(p1_list) else None
                        u2 = p2_list[s2]["uid"] if s2 < len(p2_list) else None
                        if u1 or u2:
                            self.pairs = [p for p in self.pairs if p["p1_uid"] != u1 and p["p2_uid"] != u2]
                            self.save_project()
                            should_sync = True
                    elif cmd == "DELETE_PAIR":
                        idx = int(msg.get("idx", -1))
                        if 0 <= idx < len(self.pairs):
                            del self.pairs[idx]
                            self.save_project()
                            should_sync = True
                    elif cmd == "RESET_ROUTE":
                        rkey = msg.get("key")
                        if rkey in self.routes:
                            del self.routes[rkey]
                            self.save_project()
                            should_sync = True

            elif NET_MODE == "join":
                if msg.get("net_type") == "HUB_SYNC":
                    incoming_run = msg.get("run_name", "").strip()
                    if incoming_run and not getattr(self, "guest_mgba_launched", False):
                        self.pending_guest_run_name = incoming_run

                    raw_parties = msg.get("parties", {})
                    if isinstance(raw_parties, dict):
                        self.parties.update({
                            1: raw_parties.get("1", raw_parties.get(1, [])),
                            2: raw_parties.get("2", raw_parties.get(2, []))
                        })
                    self.pairs = msg.get("pairs", [])
                    self.routes = msg.get("routes", {})
                    pg = msg.get("player_gens", {})
                    pr = msg.get("player_regions", {})
                    if isinstance(pg, dict):
                        self.player_gens.update({
                            1: pg.get("1", pg.get(1, 1)),
                            2: pg.get("2", pg.get(2, 2))
                        })
                    if isinstance(pr, dict):
                        self.player_regions.update({
                            1: pr.get("1", pr.get(1, "KANTO")),
                            2: pr.get("2", pr.get(2, "KANTO"))
                        })
                    self.nickname_rule_bool = bool(msg.get("nickname_rule", True))
                    self.type_rule_bool = bool(msg.get("type_rule", True))
                    self.pending_nickname_rule = self.nickname_rule_bool
                    self.pending_type_rule = self.type_rule_bool
                elif msg.get("action") == "FAINT":
                    local_mgba = self.clients.get(1)
                    faint_payload = (json.dumps(msg) + "\n").encode("utf-8")

        if should_sync:
            self.broadcast_state_to_guest()
        if local_mgba and faint_payload:
            try:
                local_mgba.sendall(faint_payload)
            except Exception:
                pass
    def _sorted_route_keys(self):
        return sorted(self.routes.keys(), key=lambda k: (0 if k == "starter" else 1, self.routes[k].get("order", 9999), k))

    def packet_area(self, pkt):
        """Area name for this packet. Prefer the name the bridge resolved from the
        game's own map group/number; fall back to the hub's map_id tables."""
        route = str(pkt.get("route", "") or "").strip()
        if route and not route.startswith("Map "):
            return route
        return resolve_area_name(pkt.get("gen", 1), pkt.get("sub", "RBY"), pkt.get("map_id", 0))

    def resolve_route(self, pkey, area):
        """Find (or claim, or create) the encounter row for `area` for this player.

        Rows are encounter *slots* shared by both players. P1 and P2 are usually in
        different regions (Route 1 vs Route 101), so names can't be the pairing key:
          1. a row this player already owns for this area
          2. a row with the same name that this player hasn't claimed yet
          3. the oldest row the other player opened that this player hasn't claimed
          4. otherwise open a new row
        """
        area_key = f"{pkey}_area"
        ordered = sorted(
            ((rk, rv) for rk, rv in self.routes.items() if rk != "starter"),
            key=lambda kv: (kv[1].get("order", 9999), kv[0]),
        )
        for rk, rv in ordered:
            if rv.get(area_key) == area:
                return rk, rv["name"]

        def claim(rk, rv):
            rv[area_key] = area
            names = [rv.get("p1_area"), rv.get("p2_area")]
            names = [n for i, n in enumerate(names) if n and n not in names[:i]]
            if names:
                rv["name"] = " / ".join(names)
            return rk, rv["name"]

        for rk, rv in ordered:
            if rv.get(area_key) is None and rv.get("name", "").lower() == area.lower() \
                    and rv.get(pkey, {}).get("status") == "Pending":
                return claim(rk, rv)
        for rk, rv in ordered:
            if rv.get(area_key) is None and rv.get(pkey, {}).get("status") == "Pending":
                return claim(rk, rv)

        slot_num = len(ordered) + 1
        rkey = f"route_{slot_num:02d}"
        while rkey in self.routes:
            slot_num += 1
            rkey = f"route_{slot_num:02d}"
        self.routes[rkey] = {
            "name": area,
            "order": slot_num,
            "p1": {"status": "Pending", "uid": None},
            "p2": {"status": "Pending", "uid": None},
            area_key: area,
        }
        return rkey, area

    def create_link(self, route_name, p1_mon, p2_mon):
        for p in self.pairs:
            if p["p1_uid"] == p1_mon["uid"] or p["p2_uid"] == p2_mon["uid"]:
                return
        sp1, _ = get_species_and_type(p1_mon["species"], p1_mon.get("type1", -1))
        sp2, _ = get_species_and_type(p2_mon["species"], p2_mon.get("type1", -1))
        n1 = p1_mon["nick"].strip() or sp1
        n2 = p2_mon["nick"].strip() or sp2
        self.pairs.append({
            "route": route_name,
            "p1_uid": p1_mon["uid"], "p1_name": n1, "p1_species": sp1,
            "p2_uid": p2_mon["uid"], "p2_name": n2, "p2_species": sp2,
            "dead": False
        })
        self.save_project()

    def trigger_partner_faint(self, partner_id, partner_uid):
        payload = (json.dumps({"action": "FAINT", "uid": partner_uid}) + "\n").encode("utf-8")
        if NET_MODE == "host" and partner_id == 2 and self.stun_peer:
            self.stun_peer.send_json({"action": "FAINT", "uid": partner_uid})
            return
        conn = self.clients.get(partner_id)
        if conn:
            try:
                conn.sendall(payload)
            except Exception:
                pass

    def process_player_packet(self, player_id, pkt):
        faint_targets = []
        with self.lock:
            pkt_gen = pkt.get("gen", 1)
            pkt_sub = pkt.get("sub", "RBY")
            self.player_gens[player_id] = pkt_gen
            self.player_regions[player_id] = "HOENN" if pkt_sub == "RSE" else "KANTO"

            if pkt.get("has_balls", False):
                self.unlocked_balls[player_id] = True

            party = pkt.get("party", [])
            self.parties[player_id] = party
            pkey = "p1" if player_id == 1 else "p2"
            other_pkey = "p2" if player_id == 1 else "p1"
            partner_id = 2 if player_id == 1 else 1

            # 1. Check for newly fainted Pokémon in party -> knock out linked partner (and enforce dead pairs stay at 0 HP)
            for m in party:
                if m.get("hp", 1) == 0:
                    for p in self.pairs:
                        if not p.get("dead"):
                            if player_id == 1 and p["p1_uid"] == m["uid"]:
                                p["dead"] = True
                                faint_targets.append((partner_id, p["p2_uid"]))
                                self.save_project()
                            elif player_id == 2 and p["p2_uid"] == m["uid"]:
                                p["dead"] = True
                                faint_targets.append((partner_id, p["p1_uid"]))
                                self.save_project()
                else:
                    for p in self.pairs:
                        if p.get("dead"):
                            if (player_id == 1 and p["p1_uid"] == m["uid"]) or (player_id == 2 and p["p2_uid"] == m["uid"]):
                                faint_targets.append((player_id, m["uid"]))

            # 2. Detect newly obtained Pokémon (Starter, Gift, or Caught Wild Encounter)
            new_mons = [m for m in party if m["uid"] not in self.seen_uids[player_id]]
            for m in party:
                self.seen_uids[player_id].add(m["uid"])

            map_id = pkt.get("map_id", 0)
            battle_type = pkt.get("battle_type", 0)
            enemy_sp = pkt.get("enemy_species", 0)
            area = self.packet_area(pkt)

            # PC boxes (Gen 3 bridge): a Pokemon that is sent straight to the box never
            # shows up in the party. The first box list after the hub starts is only a
            # baseline (everything already there is marked seen); after that, any unseen
            # box Pokemon is treated as newly obtained, like a party arrival.
            box_new = []
            box = pkt.get("box")
            if isinstance(box, list):
                if pkt_gen == 3:
                    # Gen 3 exposes every PC box, so any unseen box Pokemon is new.
                    if not self.box_baselined[player_id]:
                        if party:  # only baseline once a save is loaded
                            for bm in box:
                                self.seen_uids[player_id].add(bm.get("uid"))
                            self.box_baselined[player_id] = True
                    else:
                        for bm in box:
                            uid = bm.get("uid")
                            if uid and uid not in self.seen_uids[player_id]:
                                self.seen_uids[player_id].add(uid)
                                bm.setdefault("nick", "")
                                bm["type1"] = -1
                                box_new.append(bm)
                else:
                    # Gen 1/2 only expose the OPEN box. Switching boxes swaps its whole
                    # contents, so only a change of exactly one new Pokemon in the same
                    # box counts as an arrival; anything bigger is treated as a swap.
                    box_id = pkt.get("box_id")
                    cur = {bm.get("uid") for bm in box if bm.get("uid")}
                    prev = self.prev_box[player_id]
                    if not self.box_baselined[player_id]:
                        if party:
                            self.seen_uids[player_id].update(cur)
                            self.box_baselined[player_id] = True
                            self.prev_box[player_id] = (box_id, cur)
                    else:
                        added = cur - prev[1] if prev else cur
                        same_box = prev is not None and prev[0] == box_id
                        if same_box and len(added) == 1:
                            for bm in box:
                                uid = bm.get("uid")
                                if uid in added and uid not in self.seen_uids[player_id]:
                                    bm.setdefault("nick", "")
                                    bm["type1"] = -1
                                    box_new.append(bm)
                        self.seen_uids[player_id].update(cur)
                        self.prev_box[player_id] = (box_id, cur)

            incoming = [(m, False) for m in new_mons] + [(m, True) for m in box_new]
            for nm, from_box in incoming:
                sp_name, _ = get_species_and_type(nm["species"], nm.get("type1", -1))
                # Starter slot
                if "starter" not in self.routes:
                    self.routes["starter"] = {
                        "name": "Starter",
                        "order": 0,
                        "p1": {"status": "Pending", "uid": None},
                        "p2": {"status": "Pending", "uid": None}
                    }
                if not from_box and self.routes["starter"][pkey]["status"] == "Pending" and len(party) == 1:
                    self.routes["starter"].update({pkey: {"status": f"Received {sp_name}", "uid": nm["uid"], "mon": nm}})
                    other_st = self.routes["starter"].get(other_pkey, {})
                    if other_st.get("mon"):
                        p1_m = nm if player_id == 1 else other_st["mon"]
                        p2_m = other_st["mon"] if player_id == 1 else nm
                        self.create_link("Starter", p1_m, p2_m)
                    self.save_project()
                    continue

                # Wild catch or route gift
                if self.unlocked_balls.get(player_id, False):
                    rkey, rname = self.resolve_route(pkey, area)
                    cur_stat = self.routes[rkey][pkey]["status"]
                    if cur_stat == "Pending" or cur_stat.startswith("Battling"):
                        # No wild battle in progress when it arrived -> gift / egg / fossil / in-game trade
                        is_gift = battle_type != 1 and self.active_battle[player_id] is None
                        verb = "Gift" if is_gift else "Caught"
                        self.routes[rkey].update({pkey: {"status": f"{verb} {sp_name}", "uid": nm["uid"], "mon": nm}})
                        other_rt = self.routes[rkey].get(other_pkey, {})
                        if other_rt.get("mon"):
                            p1_m = nm if player_id == 1 else other_rt["mon"]
                            p2_m = other_rt["mon"] if player_id == 1 else nm
                            self.create_link(rname, p1_m, p2_m)
                        self.save_project()

            # 3. Track active wild battle & failed encounters (Rule 2 & 4)
            if self.unlocked_balls.get(player_id, False):
                if battle_type == 1 and enemy_sp > 0:
                    self.battle_end_ticks[player_id] = 0
                    rkey, rname = self.resolve_route(pkey, area)
                    if self.routes[rkey][pkey]["status"] == "Pending":
                        esp_name, _ = get_species_and_type(enemy_sp, -1)
                        self.routes[rkey].update({pkey: {"status": f"Battling {esp_name}", "uid": None}})
                        self.active_battle[player_id] = (rkey, esp_name)
                        self.save_project()
                elif battle_type == 0 and self.active_battle[player_id] is not None:
                    self.battle_end_ticks[player_id] += 1
                    if self.battle_end_ticks[player_id] >= 3:
                        rkey, esp_name = self.active_battle[player_id]
                        self.active_battle[player_id] = None
                        self.battle_end_ticks[player_id] = 0
                        if rkey in self.routes and self.routes[rkey][pkey]["status"].startswith("Battling"):
                            self.routes[rkey].update({pkey: {"status": f"FAILED ({esp_name})", "uid": None}})
                            self.save_project()

        for pid, uid in faint_targets:
            self.trigger_partner_faint(pid, uid)
    def evaluate_rules(self):
        violations, used_types = [], {}
        active_uids = {m["uid"] for p_id in (1, 2) for m in self.parties.get(p_id, ())}

        if self.nickname_rule_bool:
            for p_id in (1, 2):
                for m in self.parties.get(p_id, ()):
                    sp_name, _ = get_species_and_type(m["species"], m.get("type1", -1))
                    nick = m["nick"].strip()
                    if not nick or nick.upper() == sp_name.upper():
                        violations.append(f"Rule 3 (Nickname): P{p_id}'s {sp_name} must be nicknamed!")

        if self.type_rule_bool:
            for p_id in (1, 2):
                for m in self.parties.get(p_id, ()):
                    sp_name, t_name = get_species_and_type(m["species"], m.get("type1", -1))
                    if t_name != "Unknown":
                        if t_name in used_types:
                            violations.append(f"Rule 5 (Type Dup): {t_name} used by {used_types[t_name]} & P{p_id} {sp_name}")
                        else:
                            used_types[t_name] = f"P{p_id} {sp_name}"

        for _, r in self.routes.items():
            p1_stat = r.get("p1", {}).get("status", "")
            p2_stat = r.get("p2", {}).get("status", "")
            if "FAILED" in p1_stat and r.get("p2", {}).get("uid") in active_uids:
                violations.append(f"Rule 4 ({r['name']}): P1 failed — P2 must box/release encounter!")
            if "FAILED" in p2_stat and r.get("p1", {}).get("uid") in active_uids:
                violations.append(f"Rule 4 ({r['name']}): P2 failed — P1 must box/release encounter!")

        return violations

    def on_toggle_rules(self):
        self.nickname_rule_bool = self.nickname_rule_enabled.get()
        self.type_rule_bool = self.type_rule_enabled.get()
        if NET_MODE == "join" and self.stun_peer:
            self.stun_peer.send_json({
                "net_type": "GUEST_CMD",
                "cmd": "SET_RULES",
                "nickname_rule": self.nickname_rule_bool,
                "type_rule": self.type_rule_bool
            })
        else:
            self.save_project()
            if NET_MODE == "host":
                self.broadcast_state_to_guest()

    def link_selected_slots(self):
        s1 = int(self.var_p1_slot.get().split()[-1]) - 1
        s2 = int(self.var_p2_slot.get().split()[-1]) - 1
        if NET_MODE == "join" and self.stun_peer:
            self.stun_peer.send_json({"net_type": "GUEST_CMD", "cmd": "LINK_SLOTS", "s1": s1, "s2": s2})
            return
        with self.lock:
            p1_list, p2_list = self.parties.get(1, ()), self.parties.get(2, ())
            if s1 >= len(p1_list) or s2 >= len(p2_list):
                messagebox.showwarning("Empty Slot", "Both players must have a Pokémon in those slots.")
                return
            self.create_link("Manual Link", p1_list[s1], p2_list[s2])
        if NET_MODE == "host":
            self.broadcast_state_to_guest()

    def unlink_selected_slots(self):
        s1 = int(self.var_p1_slot.get().split()[-1]) - 1
        s2 = int(self.var_p2_slot.get().split()[-1]) - 1
        if NET_MODE == "join" and self.stun_peer:
            self.stun_peer.send_json({"net_type": "GUEST_CMD", "cmd": "UNLINK_SLOTS", "s1": s1, "s2": s2})
            return
        with self.lock:
            p1_list, p2_list = self.parties.get(1, ()), self.parties.get(2, ())
            u1 = p1_list[s1]["uid"] if s1 < len(p1_list) else None
            u2 = p2_list[s2]["uid"] if s2 < len(p2_list) else None
            self.pairs = [p for p in self.pairs if p["p1_uid"] != u1 and p["p2_uid"] != u2]
            self.save_project()
        if NET_MODE == "host":
            self.broadcast_state_to_guest()

    def delete_selected_pair(self):
        sel = self.pair_list.curselection()
        if not sel:
            return
        idx = next(iter(sel))
        if NET_MODE == "join" and self.stun_peer:
            self.stun_peer.send_json({"net_type": "GUEST_CMD", "cmd": "DELETE_PAIR", "idx": idx})
            return
        with self.lock:
            if 0 <= idx < len(self.pairs):
                del self.pairs[idx]
                self.save_project()
        if NET_MODE == "host":
            self.broadcast_state_to_guest()

    def reset_selected_route(self):
        sel = self.route_list.curselection()
        if not sel:
            return
        idx = next(iter(sel))
        keys = self._sorted_route_keys()
        if 0 <= idx < len(keys):
            rkey = keys[idx]
            if NET_MODE == "join" and self.stun_peer:
                self.stun_peer.send_json({"net_type": "GUEST_CMD", "cmd": "RESET_ROUTE", "key": rkey})
                return
            with self.lock:
                del self.routes[rkey]
                self.save_project()
            if NET_MODE == "host":
                self.broadcast_state_to_guest()

    def save_project(self):
        if NET_MODE == "join":
            return
        try:
            payload = {
                "pairs": self.pairs,
                "routes": self.routes,
                "nickname_rule": self.nickname_rule_bool,
                "type_rule": self.type_rule_bool,
                "seen_p1": list(self.seen_uids.get(1, ())),
                "seen_p2": list(self.seen_uids.get(2, ())),
                "unlocked_balls": {"1": self.unlocked_balls.get(1, False), "2": self.unlocked_balls.get(2, False)}
            }
            with open(SAVE_FILE, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2)
        except Exception:
            pass

    def load_project(self):
        if not os.path.exists(SAVE_FILE):
            return
        try:
            with open(SAVE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.pairs = data.get("pairs", [])
            self.routes = data.get("routes", {})
            self.nickname_rule_enabled.set(data.get("nickname_rule", True))
            self.nickname_rule_bool = self.nickname_rule_enabled.get()
            self.type_rule_enabled.set(data.get("type_rule", True))
            self.type_rule_bool = self.type_rule_enabled.get()
            self.seen_uids[1] = set(data.get("seen_p1", []))
            self.seen_uids[2] = set(data.get("seen_p2", []))
            ub = data.get("unlocked_balls", {})
            self.unlocked_balls[1] = bool(ub.get("1", False))
            self.unlocked_balls[2] = bool(ub.get("2", False))
        except Exception:
            pass

    def refresh_pair_list(self):
        lines = []
        for p in self.pairs:
            status = "DEAD" if p.get("dead") else "ALIVE"
            rt = safe_tk_text(p.get("route", "Unknown"))
            p1_n = safe_tk_text(p.get("p1_name", ""))
            p2_n = safe_tk_text(p.get("p2_name", ""))
            lines.append(f"[{rt}] ({status}) {p1_n} ({p.get('p1_species')}) <---> {p2_n} ({p.get('p2_species')})")

        if getattr(self, "_last_pair_lines", None) == lines:
            return
        self._last_pair_lines = lines

        sel = self.pair_list.curselection()
        prev_idx = next(iter(sel), None)
        self.pair_list.delete(0, tk.END)
        for line in lines:
            self.pair_list.insert(tk.END, line)
        if prev_idx is not None and prev_idx < len(lines):
            self.pair_list.selection_set(prev_idx)

    def refresh_route_list(self):
        rows = []
        for k in self._sorted_route_keys():
            r = self.routes[k]
            rname = safe_tk_text(r.get("name", k)).replace(" (Cross-Game)", "")
            p1_s = safe_tk_text(r.get("p1", {}).get("status", "Pending"))
            p2_s = safe_tk_text(r.get("p2", {}).get("status", "Pending"))
            rows.append((rname, p1_s, p2_s))

        # Size the columns to the content so "Route 1 / Route 101" is never cut off.
        name_w = min(max([len(r[0]) for r in rows] + [10]), 34)
        st_w = min(max([len(x) for r in rows for x in r[1:]] + [10]), 22)
        lines = []
        for rname, p1_s, p2_s in rows:
            if len(rname) > name_w:
                rname = rname[:name_w - 1] + "…"
            if len(p1_s) > st_w:
                p1_s = p1_s[:st_w - 1] + "…"
            if len(p2_s) > st_w:
                p2_s = p2_s[:st_w - 1] + "…"
            lines.append(f"{rname:<{name_w}} | P1:{p1_s:<{st_w}} | P2:{p2_s}")

        if getattr(self, "_last_route_lines", None) == lines:
            return
        self._last_route_lines = lines

        sel = self.route_list.curselection()
        prev_idx = next(iter(sel), None)
        self.route_list.delete(0, tk.END)
        for line in lines:
            self.route_list.insert(tk.END, line)
        if prev_idx is not None and prev_idx < len(lines):
            self.route_list.selection_set(prev_idx)

    def refresh_ui_loop(self):
        try:
            with self.lock:
                guest_run_to_open = getattr(self, "pending_guest_run_name", None)
                if guest_run_to_open:
                    delattr(self, "pending_guest_run_name")
                    self.root.after(50, lambda rn=guest_run_to_open: self.launch_guest_mgba_for_run(rn))

                if hasattr(self, "pending_nickname_rule"):
                    if self.nickname_rule_enabled.get() != self.pending_nickname_rule:
                        self.nickname_rule_enabled.set(self.pending_nickname_rule)
                    delattr(self, "pending_nickname_rule")
                if hasattr(self, "pending_type_rule"):
                    if self.type_rule_enabled.get() != self.pending_type_rule:
                        self.type_rule_enabled.set(self.pending_type_rule)
                    delattr(self, "pending_type_rule")

                ok_fg = "#15803d" if self.is_mac else "#a6e3a1"
                wait_fg = "#b45309" if self.is_mac else "#f9e2af"

                if NET_MODE in ("host", "join"):
                    local_ready = 1 if 1 in self.clients else 0
                    remote_ready = 1 if (self.stun_peer and self.stun_peer.connected) else 0
                    total_ready = local_ready + remote_ready
                    role = "Host" if NET_MODE == "host" else "Guest"
                    self.lbl_conn.config(
                        text=f"Online ({role}): {total_ready} / 2 Ready",
                        fg=ok_fg if total_ready == 2 else wait_fg
                    )
                else:
                    c_count = len(self.clients)
                    self.lbl_conn.config(
                        text=f"Connected Windows: {c_count} / 2",
                        fg=ok_fg if c_count == 2 else wait_fg
                    )

                self.lbl_net.config(text=safe_tk_text(self.net_status_text))

                for p_id in (1, 2):
                    g_now = self.player_gens.get(p_id, 1)
                    if not self.manual_chart_override[p_id] and self.rendered_chart_gens[p_id] != g_now:
                        self.render_type_chart_grid(p_id, g_now)

                    party = self.parties.get(p_id, [])
                    for idx in range(6):
                        lbl_name, lbl_type, lbl_sub = self.slot_widgets[p_id][idx]
                        if idx < len(party):
                            m = party[idx]
                            sp_name, t_name = get_species_and_type(m["species"], m.get("type1", -1))
                            nick = safe_tk_text(m["nick"].strip() or sp_name)
                            hp, mhp = m["hp"], m["max_hp"]
                            status_tag = " [FAINTED]" if hp == 0 else ""
                            lbl_name.config(
                                text=f"{nick} ({sp_name}) Lv.{m['level']}{status_tag}",
                                fg="#dc2626" if (hp == 0 and self.is_mac) else ("#f38ba8" if hp == 0 else self.fg_text)
                            )
                            lbl_type.config(text=t_name.upper(), bg=TYPE_COLORS.get(t_name, "#6c7086"))

                            link_str = "Unlinked"
                            for p in self.pairs:
                                if p_id == 1 and p["p1_uid"] == m["uid"]:
                                    link_str = f"Linked -> {safe_tk_text(p['p2_name'])} ({p['p2_species']})"
                                elif p_id == 2 and p["p2_uid"] == m["uid"]:
                                    link_str = f"Linked -> {safe_tk_text(p['p1_name'])} ({p['p1_species']})"
                            lbl_sub.config(text=f"HP: {hp}/{mhp}  |  {link_str}")
                        else:
                            lbl_name.config(text=f"Slot {idx+1}: Empty", fg="#9399b2")
                            lbl_type.config(text="", bg=self.bg_input)
                            lbl_sub.config(text="Waiting for Pokémon...")

                self.refresh_pair_list()
                self.refresh_route_list()

                violations = self.evaluate_rules()
                if violations:
                    self.alert_banner.config(
                        text="⚠ " + safe_tk_text(next(iter(violations))),
                        bg="#b91c1c" if self.is_mac else "#4a1c24",
                        fg="#ffffff" if self.is_mac else "#f38ba8"
                    )
                else:
                    self.alert_banner.config(
                        text="✅ All Active Soul Link Rules Satisfied!",
                        bg="#15803d" if self.is_mac else "#1e3a2f",
                        fg="#ffffff" if self.is_mac else "#a6e3a1"
                    )
        except Exception:
            pass

        self.root.after(400, self.refresh_ui_loop)


if __name__ == "__main__":
    root = tk.Tk()
    app = SoulLinkHubApp(root)
    root.mainloop()
