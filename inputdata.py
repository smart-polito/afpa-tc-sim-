import pandas as pd
import random
from events import Airplane, Passeggero

# prima
PCT_FAST_TRACK = 0.10

# dopo
PCT_FAST_TRACK = 0.06

# ── CHECK-IN ─────────────────────────────────────
BANCHI_CHECKIN_TOTALI = 48
BANCHI_CHECKIN_APERTI = 24
PCT_CHECKIN_ONLINE_SOLO_MANO = 0.50
PCT_CHECKIN_ONLINE_BAG_DROP = 0.20
PCT_CHECKIN_BANCO_COMPLETO = 0.25
PCT_CHECKIN_KIOSK = 0.05
TEMPO_CHECKIN_BANCO_MIN = 2.5
TEMPO_CHECKIN_BANCO_MAX = 4.5
TEMPO_BAG_DROP_MIN = 1.0
TEMPO_BAG_DROP_MAX = 2.0

# ── SECURITY ─────────────────────────────────────
NASTRI_SECURITY = 6
TEMPO_SECURITY_P90 = 4.5
PCT_FAST_TRACK = 0.10
TEMPO_FAST_TRACK_MIN = 0.5
TEMPO_FAST_TRACK_MAX = 1.5

# ── SCHENGEN ─────────────────────────────────────
PCT_SCHENGEN = 0.82
PCT_EXTRA_SCHENGEN = 0.18
TEMPO_BORDER_CONTROL_MIN = 5
TEMPO_BORDER_CONTROL_MAX = 15
PCT_EGATE = 0.51

# ── GATE ─────────────────────────────────────────
TEMPO_GATE_VICINO = 3
TEMPO_GATE_MEDIO = 4
TEMPO_GATE_DISTALE = 5.5
TEMPO_GATE_PIANO2_VICINO = 6.5
TEMPO_GATE_PIANO2_DISTALE = 8
ANTICIPO_MIN = 60
ANTICIPO_MAX = 120
GATE_CLOSING = 20

# ── TURNAROUND ───────────────────────────────────
TURNAROUND_RYANAIR = 25
SLA_ATTESA_MAX_CHECKIN = 10

# ── COMPAGNIE ────────────────────────────────────
compagnie_info = {
    "RYR": {"name": "Ryanair", "aircraft": "B737-800", "capacity": 189, "load_factor": 0.89},
    "DLH": {"name": "Lufthansa", "aircraft": "E190/195", "capacity": 114, "load_factor": 0.83},
    "DLA": {"name": "Air Dolomiti", "aircraft": "E190/195", "capacity": 114, "load_factor": 0.77},
    "IBE": {"name": "Iberia", "aircraft": "CRJ-1000", "capacity": 100, "load_factor": 0.87},
    "TAP": {"name": "TAP Air Portugal", "aircraft": "A320/A321", "capacity": 180, "load_factor": 0.82},
    "THY": {"name": "Turkish Airlines", "aircraft": "B737-800", "capacity": 162, "load_factor": 0.84},
    "BAW": {"name": "British Airways", "aircraft": "A320/A321", "capacity": 185, "load_factor": 0.83},
    "WZZ": {"name": "Wizz Air", "aircraft": "A321", "capacity": 230, "load_factor": 0.85},
    "WMT": {"name": "Volotea", "aircraft": "A319", "capacity": 156, "load_factor": 0.80},
    "EZY": {"name": "EasyJet", "aircraft": "A320", "capacity": 180, "load_factor": 0.87},
    "EJU": {"name": "EasyJet UK", "aircraft": "A319", "capacity": 156, "load_factor": 0.87},
    "AUA": {"name": "Austrian Airlines", "aircraft": "E195/A320", "capacity": 114, "load_factor": 0.81},
    "SAS": {"name": "Scandinavian Airlines", "aircraft": "A319/A320", "capacity": 150, "load_factor": 0.80},
    "SWR": {"name": "Swiss", "aircraft": "A220/A319", "capacity": 125, "load_factor": 0.83},
    "LOT": {"name": "LOT Polish", "aircraft": "E190/E195", "capacity": 110, "load_factor": 0.79},
    "AFR": {"name": "Air France", "aircraft": "A320", "capacity": 180, "load_factor": 0.83},
    "TUI": {"name": "TUI Airways", "aircraft": "B737-800", "capacity": 189, "load_factor": 0.89},
    "KLM": {"name": "KLM", "aircraft": "E75L/E190", "capacity": 98, "load_factor": 0.86},
    "VOE": {"name": "Vueling", "aircraft": "A320", "capacity": 180, "load_factor": 0.85},
    "EXS": {"name": "Jet2.com", "aircraft": "A321", "capacity": 220, "load_factor": 0.85},
    "RAM": {"name": "Royal Air Maroc", "aircraft": "B737-800", "capacity": 159, "load_factor": 0.82},
    "ITY": {"name": "ITA Airways", "aircraft": "A320", "capacity": 180, "load_factor": 0.84},
    "TOM": {"name": "Thomas Cook", "aircraft": "B737-800", "capacity": 189, "load_factor": 0.92},
    "NOS": {"name": "Neos Air", "aircraft": "B737-800", "capacity": 189, "load_factor": 0.90},
}

def dettaglio_aereo(call_sign: str) -> Airplane:
    c = compagnie_info[call_sign]
    return Airplane(c["name"], c["aircraft"], c["capacity"], c["load_factor"])

def prepara_data_simpy():
    df = pd.read_csv("csv-input/voli_LIMF_2025_scheduled_charter_realistic.csv")
    df_partenze = df[df["departure"] == "LIMF"].copy()
    df_partenze["firstseen"] = pd.to_datetime(df_partenze["firstseen"], utc=True)
    df_partenze["ora"] = df_partenze["firstseen"].dt.hour
    df_partenze["giorno"] = df_partenze["firstseen"].dt.date
    return df_partenze

def genera_passeggeri(volo: Airplane) -> list:
    passeggeri = []
    n = volo.passeggeri_totali()

    for i in range(n):
        r = random.random()
        if r < PCT_CHECKIN_ONLINE_SOLO_MANO:
            checkin = "online_mano"
        elif r < PCT_CHECKIN_ONLINE_SOLO_MANO + PCT_CHECKIN_ONLINE_BAG_DROP:
            checkin = "bag_drop"
        elif r < PCT_CHECKIN_ONLINE_SOLO_MANO + PCT_CHECKIN_ONLINE_BAG_DROP + PCT_CHECKIN_BANCO_COMPLETO:
            checkin = "banco"
        else:
            checkin = "kiosk"

        p = Passeggero(
            nome=f"PAX_{volo.name}_{i+1}",
            schengen=random.random() < PCT_SCHENGEN,
            anziano=random.random() < 0.10,
            bagaglio_stiva=random.random() < 0.60,
            disabilita=random.random() < 0.02,
            checkin_online=checkin,
            gruppo=random.choices([1, 2, 3, 4], weights=[0.50, 0.25, 0.15, 0.10])[0],
            tolleranza_overbooking=random.random() < 0.30,
            volo=volo
        )
        passeggeri.append(p)

    return passeggeri