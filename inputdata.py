import pandas as pd
import random
from events import Airplane, Passeggero

# ── CHECK-IN ─────────────────────────────────────
BANCHI_CHECKIN_TOTALI = 48        # 4 isole × 12 banchi — dato ufficiale SAGAT
BANCHI_CHECKIN_APERTI = 24        # stima media operativa
PCT_CHECKIN_ONLINE_SOLO_MANO = 0.50   # salta check-in fisico — dato SAGAT low cost
PCT_CHECKIN_ONLINE_BAG_DROP = 0.20    # online ma con bagaglio da consegnare
PCT_CHECKIN_BANCO_COMPLETO = 0.25     # banco fisico completo
PCT_CHECKIN_KIOSK = 0.05              # kiosk self-service
TEMPO_CHECKIN_BANCO_MIN = 2.5     # minuti — dato ufficiale SAGAT
TEMPO_CHECKIN_BANCO_MAX = 4.5     # minuti — dato ufficiale SAGAT
TEMPO_BAG_DROP_MIN = 1.0
TEMPO_BAG_DROP_MAX = 2.0

# ── SECURITY ─────────────────────────────────────
NASTRI_SECURITY = 6               # stima 4-8 linee per aeroporto 3-6M pax
TEMPO_SECURITY_P90 = 4.5          # P90 ufficiale SAGAT 2024
PCT_FAST_TRACK = 0.06             # stima realistica Caselle — acquisto online SAGAT
TEMPO_FAST_TRACK_MIN = 0.5        # scanner C3 — molto veloce
TEMPO_FAST_TRACK_MAX = 1.5

# ── SCHENGEN ─────────────────────────────────────
PCT_SCHENGEN = 0.82               # dato ufficiale SAGAT
PCT_EXTRA_SCHENGEN = 0.18         # dato ufficiale SAGAT
TEMPO_BORDER_CONTROL_MIN = 5      # minuti aggiuntivi extra-schengen
TEMPO_BORDER_CONTROL_MAX = 15
PCT_EGATE = 0.51                  # 50.99% usa e-gate — dato ufficiale 2024

# ── GATE ─────────────────────────────────────────
TEMPO_GATE_VICINO = 3             # gate 01-09 — planimetria SAGAT
TEMPO_GATE_MEDIO = 4              # gate 10-13
TEMPO_GATE_DISTALE = 5.5          # gate 14-22
TEMPO_GATE_PIANO2_VICINO = 6.5    # gate 23-27
TEMPO_GATE_PIANO2_DISTALE = 8     # gate 28-59
ANTICIPO_MIN = 60                 # minuti minimi anticipo passeggero
ANTICIPO_MAX = 120                # minuti massimi anticipo passeggero
GATE_CLOSING = 20                 # minuti prima del volo

# ── TURNAROUND ───────────────────────────────────
TURNAROUND_RYANAIR = 25
SLA_ATTESA_MAX_CHECKIN = 10

# ── PERCENTUALI PASSEGGERO ───────────────────────
PCT_ANZIANO = 0.10                # stima 10% passeggeri anziani
PCT_BAGAGLIO_STIVA = 0.60         # stima 60% con bagaglio stiva
PCT_DISABILE = 0.02               # stima 2% passeggeri con disabilità
PCT_TOLLERANZA_OVERBOOKING = 0.30

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
        # tipo check-in
        r = random.random()
        if r < PCT_CHECKIN_ONLINE_SOLO_MANO:
            checkin = "online_mano"
        elif r < PCT_CHECKIN_ONLINE_SOLO_MANO + PCT_CHECKIN_ONLINE_BAG_DROP:
            checkin = "bag_drop"
        elif r < PCT_CHECKIN_ONLINE_SOLO_MANO + PCT_CHECKIN_ONLINE_BAG_DROP + PCT_CHECKIN_BANCO_COMPLETO:
            checkin = "banco"
        else:
            checkin = "kiosk"

        # dimensione gruppo — include gruppi grandi
        gruppo = random.choices(
            [1, 2, 3, 4, 5, 6],
            weights=[0.45, 0.25, 0.15, 0.10, 0.03, 0.02]
        )[0]

        p = Passeggero(
            nome=f"PAX_{volo.name}_{i+1}",
            schengen=random.random() < PCT_SCHENGEN,
            anziano=random.random() < PCT_ANZIANO,
            bagaglio_stiva=random.random() < PCT_BAGAGLIO_STIVA,
            disabilita=random.random() < PCT_DISABILE,
            checkin_online=checkin,
            gruppo=gruppo,
            tolleranza_overbooking=random.random() < PCT_TOLLERANZA_OVERBOOKING,
            fast_track=random.random() < PCT_FAST_TRACK,
            egate=random.random() < PCT_EGATE,
            volo=volo
        )
        passeggeri.append(p)

    return passeggeri