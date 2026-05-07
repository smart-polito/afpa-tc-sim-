import simpy
import random
import numpy as np
from scipy import stats
from events import Passeggero
from inputdata import (
    prepara_data_simpy, dettaglio_aereo, genera_passeggeri,
    compagnie_info,
    BANCHI_CHECKIN_APERTI, NASTRI_SECURITY,
    PCT_CHECKIN_ONLINE_SOLO_MANO, PCT_CHECKIN_ONLINE_BAG_DROP,
    PCT_EXTRA_SCHENGEN, PCT_FAST_TRACK, PCT_EGATE,
    TEMPO_CHECKIN_BANCO_MIN, TEMPO_CHECKIN_BANCO_MAX,
    TEMPO_BAG_DROP_MIN, TEMPO_BAG_DROP_MAX,
    TEMPO_FAST_TRACK_MIN, TEMPO_FAST_TRACK_MAX,
    TEMPO_BORDER_CONTROL_MIN, TEMPO_BORDER_CONTROL_MAX,
    TEMPO_GATE_VICINO, TEMPO_GATE_PIANO2_DISTALE,
    ANTICIPO_MIN, ANTICIPO_MAX, GATE_CLOSING
)

# ── RACCOLTA DATI KPI ────────────────────────────
tempi_totali = []
tempi_checkin = []
tempi_security = []
passeggeri_in_tempo = []
voli_puntuali = []

# ── PROCESSO PASSEGGERO ──────────────────────────
def processo_passeggero(env, pax: Passeggero, checkin, security, orario_volo):

    # anticipo arrivo in aeroporto
    anticipo = np.clip(
    stats.norm.rvs(loc=90, scale=20),
    ANTICIPO_MIN, ANTICIPO_MAX
    )
    # aspetta finché non è il momento giusto
    orario_arrivo = max(0, orario_volo - anticipo)
    yield env.timeout(max(0, orario_arrivo - env.now))
    if orario_arrivo > env.now:
        yield env.timeout(orario_arrivo - env.now)

    t_start = env.now

    # ── CHECK-IN ─────────────────────────────────
    if pax.checkin_online == "online_mano":
        # salta check-in fisico
        tempi_checkin.append(0)

    elif pax.checkin_online == "bag_drop":
        t0 = env.now
        with checkin.request() as req:
            yield req
            tempo = random.uniform(TEMPO_BAG_DROP_MIN, TEMPO_BAG_DROP_MAX)
            if pax.anziano:
                tempo *= 1.3
            yield env.timeout(tempo)
        tempi_checkin.append(env.now - t0)

    else:  # banco o kiosk
        t0 = env.now
        with checkin.request() as req:
            yield req
            tempo = stats.lognorm.rvs(s=0.3, scale=np.exp(1.2))
            tempo = max(TEMPO_CHECKIN_BANCO_MIN, tempo)
            if pax.anziano:
                tempo *= 1.5
            tempo *= pax.gruppo  # famiglia → più lento
            yield env.timeout(tempo)
        tempi_checkin.append(env.now - t0)

    # ── SECURITY ─────────────────────────────────
    t1 = env.now
    if pax.disabilita or pax.checkin_online == "online_mano" and random.random() < PCT_FAST_TRACK:
        # fast track
        tempo_sec = random.uniform(TEMPO_FAST_TRACK_MIN, TEMPO_FAST_TRACK_MAX)
        yield env.timeout(tempo_sec)
    else:
        with security.request() as req:
            yield req
            tempo_sec = max(0.5, stats.lognorm.rvs(s=0.4, scale=np.exp(0.8)))
            if pax.bagaglio_stiva:
                tempo_sec *= 1.2  # più lento con bagaglio
            yield env.timeout(tempo_sec)
    tempi_security.append(env.now - t1)

    # ── BORDER CONTROL EXTRA-SCHENGEN ────────────
    if not pax.schengen:
        if random.random() < PCT_EGATE:
            yield env.timeout(random.uniform(2, 5))   # e-gate più veloce
        else:
            yield env.timeout(random.uniform(
                TEMPO_BORDER_CONTROL_MIN,
                TEMPO_BORDER_CONTROL_MAX
            ))

    # ── CAMMINATA AL GATE ────────────────────────
    tempo_gate = random.uniform(TEMPO_GATE_VICINO, TEMPO_GATE_PIANO2_DISTALE)
    yield env.timeout(tempo_gate)

    # ── ARRIVO AL GATE ───────────────────────────
    orario_target = orario_volo - GATE_CLOSING
    in_tempo = env.now <= orario_target
    passeggeri_in_tempo.append(in_tempo)
    tempi_totali.append(env.now - t_start)

# ── GENERATORE VOLI ──────────────────────────────
# prende tutto il df
def spawna_voli(env, df, checkin, security):
    
    # ordina per orario
    df = df.sort_values("firstseen")
    
    t_inizio = df["firstseen"].min()
    
    for _, row in df.iterrows():
        airline = row["airline"]
        if airline not in compagnie_info:
            continue
        
        # calcola orario in minuti dall'inizio simulazione
        orario_volo = (row["firstseen"] - t_inizio).total_seconds() / 60
        
        aereo = dettaglio_aereo(airline)
        passeggeri = genera_passeggeri(aereo)
        
        for pax in passeggeri:
            env.process(processo_passeggero(
                env, pax, checkin, security, orario_volo
            ))
        
        # aspetta fino al prossimo volo
        if _ < len(df) - 1:
            prossimo = df.iloc[_ + 1]
            delta = (prossimo["firstseen"] - row["firstseen"]).total_seconds() / 60
            yield env.timeout(max(0, delta))

# ── CALCOLO KPI ──────────────────────────────────
def calcola_kpi(df_giorno):
    otp = sum(voli_puntuali) / len(voli_puntuali) if voli_puntuali else 1.0

    # OGAR
    ogar = sum(passeggeri_in_tempo) / len(passeggeri_in_tempo)

    # CF
    tempo_target = 45
    cf = np.mean(tempi_totali) / tempo_target

    # OF
    A = 1.5
    of_ = 1 + A * (1 - otp)

    # PFPI
    pfpi = ogar / (cf * of_)

    print("\n─── KPI CORE ───────────────────────────")
    print(f"Passeggeri simulati:      {len(passeggeri_in_tempo)}")
    print(f"OGAR:  {ogar:.2%}   (target > 85%)")
    print(f"CF:    {cf:.2f}     (target < 1.0)")
    print(f"OTP:   {otp:.2%}   (target > 90%)")
    print(f"OF:    {of_:.2f}     (target = 1.0)")
    print(f"PFPI:  {pfpi:.2f}    (target > 1.0)")
    print("────────────────────────────────────────")
    print(f"Tempo medio totale:       {np.mean(tempi_totali):.1f} min")
    print(f"Tempo medio check-in:     {np.mean(tempi_checkin):.1f} min")
    print(f"Tempo medio security:     {np.mean(tempi_security):.1f} min")
    print(f"95° percentile tempo:     {np.percentile(tempi_totali, 95):.1f} min")

# ── MAIN ─────────────────────────────────────────
def main():
    df = prepara_data_simpy()
    
    print(f"Simulo {len(df)} voli totali anno 2025")
    
    env = simpy.Environment()
    checkin = simpy.Resource(env, capacity=BANCHI_CHECKIN_APERTI)
    security = simpy.Resource(env, capacity=NASTRI_SECURITY)
    
    # passa tutto il df non solo un giorno
    env.process(spawna_voli(env, df, checkin, security))
    
    env.run()  # senza until → gira finché non finisce tutto
    
    calcola_kpi(df)

if __name__ == "__main__":
    main()