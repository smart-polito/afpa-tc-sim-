import pandas as pd

from events.events import Airplane

#CHECH-IN
BANCHI_CHECKIN_TOTALI = 48        # 4 isole × 12 banchi — dato ufficiale
BANCHI_CHECKIN_APERTI = 24        # stima media (varia con traffico)
PCT_CHECKIN_ONLINE_SOLO_MANO = 0.50   # 40-60% low cost → salta check-in
PCT_CHECKIN_ONLINE_BAG_DROP = 0.20    # bag drop — tempo ridotto
PCT_CHECKIN_BANCO_COMPLETO = 0.25     # banco completo
PCT_CHECKIN_KIOSK = 0.05              # kiosk
TEMPO_CHECKIN_BANCO_MIN = 2.5     # minuti — dato ufficiale SAGAT
TEMPO_CHECKIN_BANCO_MAX = 4.5     # minuti — dato ufficiale SAGAT
TEMPO_BAG_DROP_MIN = 1.0          # più veloce del banco completo
TEMPO_BAG_DROP_MAX = 2.0

#SECURITY
NASTRI_SECURITY = 6               # stima per aeroporto 3-6M pax (4-8 range)
TEMPO_SECURITY_P90 = 4.5          # minuti — dato ufficiale SAGAT 2024
PCT_FAST_TRACK = 0.10             # stima passeggeri con fast track
TEMPO_FAST_TRACK_MIN = 0.5        # più veloce con scanner C3
TEMPO_FAST_TRACK_MAX = 1.5

# SCHENGEN vs EXTRA-SCHENGEN

PCT_SCHENGEN = 0.82               # ~80-85% — dato ufficiale
PCT_EXTRA_SCHENGEN = 0.18         # ~15-20% — dato ufficiale
TEMPO_BORDER_CONTROL_MIN = 5      # minuti aggiuntivi extra-schengen
TEMPO_BORDER_CONTROL_MAX = 15     # minuti aggiuntivi extra-schengen
PCT_EGATE = 0.51                  # 50.99% usa e-gate — dato ufficiale 2024

# GATE — tempi camminata da documento
TEMPO_GATE_VICINO = 3             # gate 01-09 → 2-4 min
TEMPO_GATE_MEDIO = 4              # gate 10-13 → 3-5 min
TEMPO_GATE_DISTALE = 5.5          # gate 14-22 → 4-7 min
TEMPO_GATE_PIANO2_VICINO = 6.5    # gate 23-27 → 5-8 min
TEMPO_GATE_PIANO2_DISTALE = 8     # gate 28-59 → 6-10 min

# PASSEGGERI
ANTICIPO_MIN = 60                 # minuti prima della partenza
ANTICIPO_MAX = 120                # minuti prima della partenza
GATE_CLOSING = 20                 # minuti prima del volo

# TURNAROUND
TURNAROUND_RYANAIR = 25           # minuti target Ryanair
SLA_ATTESA_MAX_CHECKIN = 10       # minuti massimi attesa accettabili

compagnie_info = {
        "RYR": {"name": "Ryanair", "aircraft": "B737-800", "capacity": 189, "load_factor": 0.89},
        "DLH": {"name": "Lufthansa", "aircraft": "E190/195", "capacity": 114, "load_factor": 0.83},
        "DLA": {"name": "air dolomiti", "aircraft": "E190/195", "capacity": 114, "load_factor": 0.77},
        "IBE": {"name": "Iberia", "aircraft": "CRJ-1000", "capacity": 100, "load_factor": 0.87},
        "TAP": {"name": "TAP Air Portugal","aircraft": "A320/A321","capacity": 180, "load_factor": 0.82},
        "THY": {"name": "Turkish Airlines", "aircraft": "B737-800", "capacity": 162, "load_factor": 0.84},
        "BAW": {"name": "British Airways", "aircraft": "A320/A321", "capacity": 185, "load_factor": 0.83},
        "WZZ": {"name": "Wizz Air", "aircraft": "A321", "capacity": 230, "load_factor": 0.85},
        "WMT": {"name": "Volotea", "aircraft": "A319", "capacity": 156, "load_factor": 0.80},
        "EZY": {"name": "EasyJet", "aircraft": "A320", "capacity": 180, "load_factor": 0.87},
        "EJU": {"name": "EasyJet UK", "aircraft": "A319", "capacity": 156, "load_factor": 0.87},
        "AUA": {"name": "Austrian Airlines","aircraft": "E195/A320","capacity": 114,"load_factor": 0.81},
        "SAS": {"name": "Scandinavian Airlines", "aircraft": "A319/A320", "capacity": 150, "load_factor": 0.80},
        "SWR": {"name": "Swiss International Air Lines","aircraft": "A220/A319","capacity": 125, "load_factor": 0.83},
        "LOT": {"name": "LOT Polish Airlines", "aircraft": "E190/E195", "capacity": 110, "load_factor": 0.79},
        "AFR": {"name": "Air France", "aircraft": "A320", "capacity": 180, "load_factor": 0.83},
        "TUI": {"name": "TUI Airways", "aircraft": "B737-800 / B737 MAX", "capacity": 189, "load_factor": 0.89},
        "KLM": {"name": "KLM Royal Dutch Airlines", "aircraft": "E75L/E190", "capacity": 98, "load_factor": 0.86},
        "VOE": {"name": "Vueling", "aircraft": "A320", "capacity": 180, "load_factor": 0.85},
        "EXS": {"name": "Jet2.com", "aircraft": "A321 / A321neo / B737-800", "capacity": 220, "load_factor": 0.85},
        "RAM": {"name": "Royal Air Maroc", "aircraft": "B737-800 / 737 MAX 8", "capacity": 159, "load_factor": 0.82},
        "ITY": {"name": "ITA Airways", "aircraft": "A320", "capacity": 180, "load_factor": 0.84},
        "TOM": {"name": "Thomas Cook", "aircraft": "B737-800", "capacity": 189, "load_factor": 0.92},  # charter
        "EXS": {"name": "Enter Air", "aircraft": "B737-800", "capacity": 189, "load_factor": 0.93},     # charter
        "NOS": {"name": "Neos Air", "aircraft": "B737-800", "capacity": 189, "load_factor": 0.90}       # charter
    }

def dettaglio_aereo(call_sign: str) -> Airplane:
    c = compagnie_info[call_sign]
    return Airplane(c["name"], c["aircraft"], c["capacity"], c["load_factor"])

# Distribuzione passeggeri con disabilità

# Distribuzione passeggeri con biglietto online

def prepara_data_simpy():
    df=pd.read_csv("csv-input/voli_LIMF_2025_scheduled_charter_realistic.csv")

    # ora prendo solo le partenze
    df_partenze=df[df["departure"] == "LIMF"].copy()

    #converto orario in datetime
    df_partenze["firstseen"]=pd.to_datetime(df_partenze["firstseen"], utc=True)

    df_partenze["ora"]=df_partenze["firstseen"].dt.hour
    df_partenze["giorno"]=df_partenze["firstseen"].dt.date

    return df_partenze
