import simpy
import random
import numpy as np
from scipy import stats
import matplotlib.pyplot as plt
import os
from events.events import Passeggero
from generators import spawna_voli
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

# ── FUNZIONE TEMPO CAMMINATA ─────────────────────
def tempo_camminata(pax, tipo):
    """
    Calcola tempo di camminata in base al tipo di passeggero.
    tipo: "ingresso_checkin", "checkin_security", "security_gate"
    """
    if tipo == "ingresso_checkin":
        # dal documento SAGAT: ingresso → check-in = 2-5 min in condizioni normali
        if pax.disabilita:
            return random.uniform(7, 12)   # percorso assistito
        elif pax.anziano:
            return random.uniform(5, 8)    # lento, si orienta
        elif pax.gruppo >= 3:
            return random.uniform(4, 7)    # famiglia con bagagli
        elif pax.gruppo == 2:
            return random.uniform(3, 5)    # coppia
        else:
            return random.uniform(2, 4)    # singolo veloce

    elif tipo == "checkin_security":
        # dal documento SAGAT: check-in → tornelli → security
        if pax.disabilita:
            return random.uniform(5, 10)   # ascensore, percorso assistito
        elif pax.anziano:
            return random.uniform(4, 7)
        elif pax.gruppo >= 3:
            return random.uniform(3, 6)
        elif pax.gruppo == 2:
            return random.uniform(2, 5)
        else:
            return random.uniform(1, 3)

    elif tipo == "security_gate":
        # dal documento SAGAT: tabella tempi per piano e distanza gate
        if pax.disabilita:
            return random.uniform(8, 15)   # percorso assistito, eventuale bus
        elif pax.anziano:
            return random.uniform(6, 12)
        elif pax.gruppo >= 3:
            return random.uniform(5, 10)
        elif pax.gruppo == 2:
            return random.uniform(4, 8)
        else:
            return random.uniform(TEMPO_GATE_VICINO, TEMPO_GATE_PIANO2_DISTALE)

# ── PROCESSO PASSEGGERO ──────────────────────────
def processo_passeggero(env, pax, checkin, security, orario_volo):

    # genera anticipo — distribuzione normale centrata su 90 min
    # fonte: letteratura aeroportuale per scali medio-piccoli
    anticipo = np.clip(
        stats.norm.rvs(loc=90, scale=20),
        ANTICIPO_MIN, ANTICIPO_MAX
    )

    # orario arrivo in aeroporto in minuti simulati
    orario_arrivo = orario_volo - anticipo
    if orario_arrivo > env.now:
        yield env.timeout(orario_arrivo - env.now)

    # segna inizio percorso
    t_start = env.now

    # ── CAMMINATA INGRESSO → CHECK-IN ───────────
    yield env.timeout(tempo_camminata(pax, "ingresso_checkin"))

    # ── CHECK-IN ────────────────────────────────
    if pax.checkin_online == "online_mano":
        # salta check-in fisico — va diretto alla security
        tempi_checkin.append(0)

    elif pax.checkin_online == "bag_drop":
        # banco veloce — solo consegna bagaglio
        t0 = env.now
        with checkin.request() as req:
            yield req
            tempo = random.uniform(TEMPO_BAG_DROP_MIN, TEMPO_BAG_DROP_MAX)
            if pax.anziano:
                tempo *= 1.3
            yield env.timeout(tempo)
        tempi_checkin.append(env.now - t0)

    else:
        # banco completo o kiosk
        t0 = env.now
        with checkin.request() as req:
            yield req
            # lognormale — tempi brevi frequenti, rari casi lunghi
            tempo = max(TEMPO_CHECKIN_BANCO_MIN,
                        stats.lognorm.rvs(s=0.3, scale=np.exp(1.2)))
            # modificatori per tipo passeggero
            if pax.anziano:
                tempo *= 1.4    # anziano → 40% più lento
            if pax.gruppo == 2:
                tempo *= 1.2    # coppia → +20%
            elif pax.gruppo == 3:
                tempo *= 1.4    # famiglia piccola → +40%
            elif pax.gruppo == 4:
                tempo *= 1.6    # famiglia → +60%
            elif pax.gruppo >= 5:
                tempo *= 1.8    # gruppo grande → +80%
            yield env.timeout(tempo)
        tempi_checkin.append(env.now - t0)

    # ── CAMMINATA CHECK-IN → SECURITY ───────────
    yield env.timeout(tempo_camminata(pax, "checkin_security"))

    # ── SECURITY ────────────────────────────────
    t1 = env.now
    if pax.disabilita or pax.fast_track:
        # fast track SAGAT o percorso assistito disabili
        yield env.timeout(
            random.uniform(TEMPO_FAST_TRACK_MIN, TEMPO_FAST_TRACK_MAX)
        )
    else:
        # nastro standard — aspetta risorsa libera
        with security.request() as req:
            yield req
            # lognormale — P90 calibrato su dato SAGAT 4.5 min
            tempo_sec = max(0.5, stats.lognorm.rvs(s=0.4, scale=np.exp(0.8)))
            if pax.bagaglio_stiva:
                tempo_sec *= 1.2   # bagaglio stiva → controlli più lunghi
            if pax.anziano:
                tempo_sec *= 1.3   # anziano → più lento a togliere oggetti
            yield env.timeout(tempo_sec)
    tempi_security.append(env.now - t1)

    # ── BORDER CONTROL (solo extra-schengen) ────
    if not pax.schengen:
        if pax.egate:
            # e-gate biometrico — 50.99% passeggeri, dato SAGAT 2024
            yield env.timeout(random.uniform(2, 5))
        else:
            # sportello manuale Polizia di Frontiera
            yield env.timeout(random.uniform(
                TEMPO_BORDER_CONTROL_MIN, TEMPO_BORDER_CONTROL_MAX
            ))

    # ── CAMMINATA SECURITY → GATE ───────────────
    yield env.timeout(tempo_camminata(pax, "security_gate"))

    # ── ARRIVO AL GATE ──────────────────────────
    orario_target = orario_volo - GATE_CLOSING
    in_tempo = env.now <= orario_target
    passeggeri_in_tempo.append(in_tempo)

    tempo_totale = env.now - t_start
    if tempo_totale > 0:
        tempi_totali.append(tempo_totale)

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

    # distribuzione tempi totali
    axes[0,0].hist(tempi_totali, bins=30, color="steelblue", edgecolor="black")
    axes[0,0].axvline(x=45, color="red", linestyle="--", label="Target 45 min")
    axes[0,0].set_title("Distribuzione tempi totali")
    axes[0,0].set_xlabel("Minuti")
    axes[0,0].set_ylabel("Passeggeri")
    axes[0,0].legend()

    # distribuzione tempi check-in
    axes[0,1].hist(tempi_checkin, bins=30, color="orange", edgecolor="black")
    axes[0,1].axvline(x=10, color="red", linestyle="--", label="SLA 10 min")
    axes[0,1].set_title("Distribuzione tempi check-in")
    axes[0,1].set_xlabel("Minuti")
    axes[0,1].set_ylabel("Passeggeri")
    axes[0,1].legend()

    # distribuzione tempi security
    axes[1,0].hist(tempi_security, bins=30, color="green", edgecolor="black")
    axes[1,0].axvline(x=4.5, color="red", linestyle="--", label="P90 SAGAT 4.5 min")
    axes[1,0].set_title("Distribuzione tempi security")
    axes[1,0].set_xlabel("Minuti")
    axes[1,0].set_ylabel("Passeggeri")
    axes[1,0].legend()

    # KPI core a barre
    ogar = sum(passeggeri_in_tempo) / len(passeggeri_in_tempo)
    cf = np.mean(tempi_totali) / 45
    of_ = 1.0
    pfpi = ogar / (cf * of_) if cf > 0 else 0
    kpi_values = [ogar, cf, of_, pfpi]
    kpi_labels = ["OGAR", "CF", "OF", "PFPI"]
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

    # trova giorno più trafficato
    voli_per_giorno = df.groupby("giorno").size()
    giorno = voli_per_giorno.idxmax()
    df_giorno = df[df["giorno"] == giorno].copy()
    print(f"Simulo giorno: {giorno} — {len(df_giorno)} voli")

    # calcola durata simulazione
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