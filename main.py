import simpy
import numpy as np
import pandas as pd

from inputdata import (
    prepara_data_simpy,
    BANCHI_CHECKIN_APERTI,
    NASTRI_SECURITY
)

from generators import spawna_voli

from process import (
    tempi_totali,
    tempi_checkin,
    tempi_security,
    passeggeri_in_tempo,
    anticipi,
    attese_checkin,
    attese_security,
    eventi_congestione
)

TARGET_TEMPO = 45


def main():

    # ======================================
    # DATI
    # ======================================

    df = prepara_data_simpy()
    giorni = sorted(df["giorno"].unique())
    print(f"Voli totali anno 2025: {len(df)}")
    print(f"Simulo {len(giorni)} giorni separatamente...\n")

    durata_totale_simulata = 0

    # ======================================
    # LOOP SU TUTTI I GIORNI
    # ======================================

    for idx, giorno in enumerate(giorni):

        df_giorno = df[df["giorno"] == giorno]

        if len(df_giorno) == 0:
            continue

        # durata = ultimo volo del giorno + margine per finire i processi
        ultimo_volo_ora = df_giorno["ora"].max()
        durata = (ultimo_volo_ora + 4) * 60   # +4 ore di margine, in minuti

        env = simpy.Environment()

        checkin = simpy.Resource(env, capacity=BANCHI_CHECKIN_APERTI)
        security = simpy.Resource(env, capacity=NASTRI_SECURITY)

        env.process(
            spawna_voli(env, df_giorno, checkin, security)
        )

        env.run(until=durata)
        durata_totale_simulata += durata

        if (idx + 1) % 30 == 0:
            print(f"  Simulati {idx+1}/{len(giorni)} giorni — "
                  f"{len(tempi_totali)} passeggeri finora")

    print(f"\nSimulazione completa — {len(giorni)} giorni, "
          f"{len(tempi_totali)} passeggeri totali\n")

    # ======================================
    # KPI BASE — calcolati su tutto l'anno
    # ======================================

    pax = len(tempi_totali)

    tempo_totale_medio = np.mean(tempi_totali)

    ogar = sum(passeggeri_in_tempo) / len(passeggeri_in_tempo)

    cf = tempo_totale_medio / TARGET_TEMPO

    throughput = pax / durata_totale_simulata

    load = throughput / (BANCHI_CHECKIN_APERTI + NASTRI_SECURITY)

    dwell = np.mean(anticipi) - tempo_totale_medio

    tempo_attesa_tot = np.sum(attese_checkin) + np.sum(attese_security)

    wti = tempo_attesa_tot / (pax * TARGET_TEMPO)

    bfi = eventi_congestione / durata_totale_simulata

    utilization = (
        (np.sum(tempi_checkin) + np.sum(tempi_security))
        / (durata_totale_simulata * (BANCHI_CHECKIN_APERTI + NASTRI_SECURITY))
    )

    # capacità teorica
    cap_checkin = BANCHI_CHECKIN_APERTI / np.mean(tempi_checkin)
    cap_security = NASTRI_SECURITY / np.mean(tempi_security)
    capacita = min(cap_checkin, cap_security)

    gap = throughput - capacita
    pac = capacita
    saturation = load
    sigma = np.std(tempi_totali)

    # ======================================
    # STAMPA KPI
    # ======================================

    print("\n========== KPI ANNO 2025 ==========\n")
    print(f"PAX TOTALI = {pax}")
    print(f"OGAR = {ogar:.3f}")
    print(f"UTILIZATION = {utilization:.3f}")
    print(f"LOAD = {load:.3f}")
    print(f"GAP = {gap:.3f}")
    print(f"DWELL = {dwell:.3f}")
    print(f"THROUGHPUT = {throughput:.3f}")
    print(f"PAC = {pac:.3f}")
    print(f"CF = {cf:.3f}")
    print(f"WTI = {wti:.3f}")
    print(f"TEMPO TOTALE MEDIO = {tempo_totale_medio:.3f}")
    print(f"BFI = {bfi:.3f}")
    print(f"SATURATION = {saturation:.3f}")
    print(f"SIGMA = {sigma:.3f}")

    # ======================================
    # DATAFRAME EXCEL READY
    # ======================================

    risultati = pd.DataFrame([{
        "PERIODO": "Anno 2025 completo",
        "GIORNI_SIMULATI": len(giorni),
        "PAX_TOTALI": pax,
        "OGAR": ogar,
        "UTILIZATION": utilization,
        "LOAD": load,
        "GAP": gap,
        "DWELL": dwell,
        "THROUGHPUT": throughput,
        "PAC": pac,
        "CF": cf,
        "WTI": wti,
        "TEMPO_TOTALE_MEDIO": tempo_totale_medio,
        "BFI": bfi,
        "SATURATION": saturation,
        "SIGMA": sigma
    }])

    risultati.to_excel("output_kpi_2025.xlsx", index=False)
    print("\nExcel salvato: output_kpi_2025.xlsx")


if __name__ == "__main__":
    main()