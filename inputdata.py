import pandas as pd

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

def prepara_data_simpy():
    df=pd.read_csv("csv-input/voli_LIMF_2025_scheduled_charter_realistic.csv")

    # ora prendo solo le partenze
    df_partenze=df[df["departure"] == "LIMF"].copy()

    #converto orario in datetime
    df_partenze["firstseen"]=pd.to_datetime(df_partenze["firstseen"], utc=True)

    df_partenze["ora"]=df_partenze["firstseen"].dt.hour
    df_partenze["giorno"]=df_partenze["firstseen"].dt.date

    return df_partenze
