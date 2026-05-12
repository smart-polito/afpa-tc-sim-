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
from plotting import grafici

# TODO: Estrarre tutti i dati globali in un modulo "context.py" per far sì che
# TIP: Utilizzare la classe SimulationState implementata nel file "context.py" e passare ai diversi processi una sua istanza
# nel main, creo un'istanza globale:
# simulation_state = SimulationState()
# la passo ai diversi processi nei parametri
# def processo_fa_qualcosa(env, simulation_state, ...)
# dentro il processo aggiorno i tempi accedendo ai suoi attributi:
# simulation_state.tempi_totali.append(blablabla)

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
    if pax.disabilita:                              # TODO: Estrarre in funzione che calcola il tempo di percorso
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

    elif pax.checkin_online == "bag_drop":          # TODO: Questo può essere estratto in un processo a parte
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
        # TODO: Estrarre in processo a parte
        t0 = env.now
        with checkin.request() as req:
            yield req
            tempo = max(TEMPO_CHECKIN_BANCO_MIN,
                        stats.lognorm.rvs(s=0.3, scale=np.exp(1.2)))
            if pax.anziano:
                tempo *= 1.5            # DOMANDA: Come abbiamo stimato il rallentamento dovuto al fatto che un passeggero sia anziano?
            tempo *= pax.gruppo   # famiglia → più lento        # TODO ERRORE: Il tempo di percorrenza di una famiglia o gruppo NON è il prodotto dei tempi di percorrenza dei singoli partecipanti
                                    # 4 persone a camminare non ci mettono 4 volte il tempo di una persona singola

            yield env.timeout(tempo)
        tempi_checkin.append(env.now - t0)

    # ── CAMMINATA CHECK-IN → SECURITY ───────────────
    # TODO: Estrarre in funzione che calcola il tempo di percorrenza

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
    # TODO: Estrarre in processo a parte "security_checks" che prende in input il passeggero
    t1 = env.now
    if pax.disabilita or random.random() < PCT_FAST_TRACK:      # TODO: Errore il random.random non ha senso
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
                tempo_sec *= 1.2   # bagaglio stiva → più lento         # TODO: Come abbiamo stimato questo numero?
            yield env.timeout(tempo_sec)
    tempi_security.append(env.now - t1)

    # ── BORDER CONTROL (solo extra-schengen) ────      # TODO: Per ora abbiamo deciso di non gestire l'area extra shenghen
    if not pax.schengen:
        if random.random() < PCT_EGATE:         # TODO: random.random non ha senso
            # e-gate biometrico — più veloce
            yield env.timeout(random.uniform(2, 5))         # TODO: Come abbiamo stimato questi numeri?
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
    grafici()       # TODO: Passare parametro stato globale


if __name__ == "__main__":
    main()