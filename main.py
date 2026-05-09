import simpy
import random
import numpy as np
from scipy import stats
import matplotlib.pyplot as plt
import os
from events.events import Passeggero
from inputdata import (
    prepara_data_simpy, dettaglio_aereo, genera_passeggeri,
    compagnie_info,
    BANCHI_CHECKIN_APERTI, NASTRI_SECURITY,
    PCT_FAST_TRACK, PCT_EGATE,
    TEMPO_CHECKIN_BANCO_MIN,
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
def processo_passeggero(env, pax, checkin, security, orario_volo):

    # genera anticipo casuale — quanto prima arriva in aeroporto
    anticipo = np.clip(
        stats.norm.rvs(loc=90, scale=20),
        ANTICIPO_MIN, ANTICIPO_MAX
    )           #90 sono minuti in cui di solito si arriva prima in aeroporto e 20 è deviazione standard 


    # orario in cui il passeggero arriva in aeroporto
    orario_arrivo = orario_volo - anticipo


    # aspetta fino all'orario di arrivo
    if orario_arrivo > env.now:
        yield env.timeout(orario_arrivo - env.now)

    # segna inizio percorso
    t_start = env.now


    # ── CAMMINATA INGRESSO → CHECK-IN ───────────────
    if pax.disabilita:
        # disabile → molto lento, percorso assistito
        yield env.timeout(random.uniform(7, 12))
    elif pax.anziano:
        # anziano → lento
        yield env.timeout(random.uniform(5, 8))
    elif pax.gruppo > 2:
        # famiglia numerosa → rallentata da bambini/bagagli
        yield env.timeout(random.uniform(4, 7))
    elif pax.gruppo == 2:
        # coppia → leggermente più lento del singolo
        yield env.timeout(random.uniform(3, 5))
    else:
        # singolo → veloce
        yield env.timeout(random.uniform(2, 4))


    # ── CHECK-IN ────────────────────────────────
    if pax.checkin_online == "online_mano":
        # salta il check-in fisico completamente
        tempi_checkin.append(0)

    elif pax.checkin_online == "bag_drop":
        # banco veloce solo per consegnare bagaglio
        t0 = env.now
        with checkin.request() as req:
            yield req
            tempo = random.uniform(TEMPO_BAG_DROP_MIN, TEMPO_BAG_DROP_MAX)
            if pax.anziano:
                tempo *= 1.3
            yield env.timeout(tempo)
        tempi_checkin.append(env.now - t0)

    else:
        # banco completo o kiosk — più lento
        t0 = env.now
        with checkin.request() as req:
            yield req
            tempo = max(TEMPO_CHECKIN_BANCO_MIN,
                        stats.lognorm.rvs(s=0.3, scale=np.exp(1.2)))
            if pax.anziano:
                tempo *= 1.5
            tempo *= pax.gruppo   # famiglia → più lento
            yield env.timeout(tempo)
        tempi_checkin.append(env.now - t0)
    # ── CAMMINATA CHECK-IN → SECURITY ───────────────


    # dal documento SAGAT: area check-in → tornelli → security
    if pax.disabilita:
        # percorso assistito, eventuale ascensore
        yield env.timeout(random.uniform(5, 10))
    elif pax.anziano:
        # lento, si orienta
        yield env.timeout(random.uniform(4, 7))
    elif pax.gruppo > 2:
        # famiglia con bambini e bagagli
        yield env.timeout(random.uniform(3, 6))
    elif pax.gruppo == 2:
        # coppia
        yield env.timeout(random.uniform(2, 5))
    else:
        # singolo frequente — conosce già il percorso
        yield env.timeout(random.uniform(1, 3))

        
    # ── SECURITY ────────────────────────────────
    t1 = env.now
    if pax.disabilita or random.random() < PCT_FAST_TRACK:
        # fast track — corsia dedicata più veloce
        yield env.timeout(
            random.uniform(TEMPO_FAST_TRACK_MIN, TEMPO_FAST_TRACK_MAX)
        )
    else:
        # nastro standard — aspetta risorsa libera
        with security.request() as req:
            yield req
            tempo_sec = max(0.5, stats.lognorm.rvs(s=0.4, scale=np.exp(0.8)))
            if pax.bagaglio_stiva:
                tempo_sec *= 1.2   # bagaglio stiva → più lento
            yield env.timeout(tempo_sec)
    tempi_security.append(env.now - t1)

    # ── BORDER CONTROL (solo extra-schengen) ────
    if not pax.schengen:
        if random.random() < PCT_EGATE:
            # e-gate biometrico — più veloce
            yield env.timeout(random.uniform(2, 5))
        else:
            # sportello manuale — più lento
            yield env.timeout(random.uniform(
                TEMPO_BORDER_CONTROL_MIN, TEMPO_BORDER_CONTROL_MAX
            ))

    # ── CAMMINATA AL GATE ───────────────────────
    yield env.timeout(
        random.uniform(TEMPO_GATE_VICINO, TEMPO_GATE_PIANO2_DISTALE)
    )

    # ── ARRIVO AL GATE ──────────────────────────
    # controlla se arrivato prima della chiusura gate
    orario_target = orario_volo - GATE_CLOSING
    in_tempo = env.now <= orario_target
    passeggeri_in_tempo.append(in_tempo)

    # salva tempo totale solo se positivo
    tempo_totale = env.now - t_start
    if tempo_totale > 0:
        tempi_totali.append(tempo_totale)


# ── GENERATORE VOLI ──────────────────────────────
def spawna_voli(env, df, checkin, security):

    # ordina per orario cronologico
    df = df.sort_values("firstseen").reset_index(drop=True)
    t_inizio = df["firstseen"].min()

    for i, row in df.iterrows():
        airline = row["airline"]
        if airline not in compagnie_info:
            continue

        # converti orario volo in minuti dall'inizio simulazione
        orario_volo = (row["firstseen"] - t_inizio).total_seconds() / 60

        # aspetta fino all'orario del volo
        if orario_volo > env.now:
            yield env.timeout(orario_volo - env.now)

        # crea aereo dalla compagnia
        aereo = dettaglio_aereo(airline)

        # genera tutti i passeggeri del volo
        passeggeri = genera_passeggeri(aereo)

        # lancia processo SimPy per ogni passeggero
        for pax in passeggeri:
            env.process(processo_passeggero(
                env, pax, checkin, security, orario_volo
            ))
        # NON c'è yield qui — passa subito al volo successivo
        # è SimPy che gestisce i passeggeri in parallelo


# ── CALCOLO KPI ──────────────────────────────────
def calcola_kpi():
    if not passeggeri_in_tempo:
        print("Nessun passeggero simulato!")
        return

    otp = sum(voli_puntuali) / len(voli_puntuali) if voli_puntuali else 1.0
    ogar = sum(passeggeri_in_tempo) / len(passeggeri_in_tempo)
    cf = np.mean(tempi_totali) / 45 if tempi_totali else 0
    A = 1.5
    of_ = 1 + A * (1 - otp)
    pfpi = ogar / (cf * of_) if cf > 0 else 0

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


# ── GRAFICI ──────────────────────────────────────
def grafici():
    os.makedirs("output", exist_ok=True)

    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    fig.suptitle("Simulazione Aeroporto Torino Caselle 2025", fontsize=14)

    # grafico 1 — distribuzione tempi totali
    axes[0,0].hist(tempi_totali, bins=30, color="steelblue", edgecolor="black")
    axes[0,0].axvline(x=45, color="red", linestyle="--", label="Target 45 min")
    axes[0,0].set_title("Distribuzione tempi totali")
    axes[0,0].set_xlabel("Minuti")
    axes[0,0].set_ylabel("Passeggeri")
    axes[0,0].legend()

    # grafico 2 — distribuzione tempi check-in
    axes[0,1].hist(tempi_checkin, bins=30, color="orange", edgecolor="black")
    axes[0,1].axvline(x=10, color="red", linestyle="--", label="SLA 10 min")
    axes[0,1].set_title("Distribuzione tempi check-in")
    axes[0,1].set_xlabel("Minuti")
    axes[0,1].set_ylabel("Passeggeri")
    axes[0,1].legend()

    # grafico 3 — distribuzione tempi security
    axes[1,0].hist(tempi_security, bins=30, color="green", edgecolor="black")
    axes[1,0].axvline(x=4.5, color="red", linestyle="--", label="P90 SAGAT 4.5 min")
    axes[1,0].set_title("Distribuzione tempi security")
    axes[1,0].set_xlabel("Minuti")
    axes[1,0].set_ylabel("Passeggeri")
    axes[1,0].legend()

    # grafico 4 — KPI core a barre
    kpi_labels = ["OGAR", "CF", "OF", "PFPI"]
    ogar = sum(passeggeri_in_tempo) / len(passeggeri_in_tempo)
    cf = np.mean(tempi_totali) / 45
    of_ = 1.0
    pfpi = ogar / (cf * of_) if cf > 0 else 0
    kpi_values = [ogar, cf, of_, pfpi]
    colori = ["green" if v >= 1 else "red" for v in kpi_values]
    axes[1,1].bar(kpi_labels, kpi_values, color=colori, edgecolor="black")
    axes[1,1].axhline(y=1, color="black", linestyle="--", label="Target = 1")
    axes[1,1].set_title("KPI Core")
    axes[1,1].legend()

    plt.tight_layout()
    plt.savefig("output/kpi_caselle_2025.png")
    plt.show()
    print("Grafico salvato in output/kpi_caselle_2025.png")


# ── MAIN ─────────────────────────────────────────
def main():
    df = prepara_data_simpy()
    print(f"Voli totali anno 2025: {len(df)}")

    # simula solo il giorno più trafficato
    voli_per_giorno = df.groupby("giorno").size()
    giorno = voli_per_giorno.idxmax()
    df_giorno = df[df["giorno"] == giorno].copy()

    print(f"Simulo giorno: {giorno} — {len(df_giorno)} voli")

    # calcola durata — solo le ore di quel giorno + margine
    t_inizio = df_giorno["firstseen"].min()
    t_fine = df_giorno["firstseen"].max()
    durata = (t_fine - t_inizio).total_seconds() / 60 + 200
    print(f"Durata simulazione: {durata:.0f} minuti")

    # reset liste KPI
    tempi_totali.clear()
    tempi_checkin.clear()
    tempi_security.clear()
    passeggeri_in_tempo.clear()
    voli_puntuali.clear()

    env = simpy.Environment()
    checkin = simpy.Resource(env, capacity=BANCHI_CHECKIN_APERTI)
    security = simpy.Resource(env, capacity=NASTRI_SECURITY)

    env.process(spawna_voli(env, df_giorno, checkin, security))
    env.run(until=durata)

    calcola_kpi()
    grafici()


if __name__ == "__main__":
    main()