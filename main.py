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

    giorno = df.groupby(
        "giorno"
    ).size().idxmax()

    df = df[
        df["giorno"] == giorno
    ]

    durata = 600

    # ======================================
    # SIMPY
    # ======================================

    env = simpy.Environment()

    checkin = simpy.Resource(
        env,
        capacity=BANCHI_CHECKIN_APERTI
    )

    security = simpy.Resource(
        env,
        capacity=NASTRI_SECURITY
    )

    env.process(
        spawna_voli(
            env,
            df,
            checkin,
            security
        )
    )

    env.run(until=durata)

    # ======================================
    # KPI BASE
    # ======================================

    pax = len(tempi_totali)

    tempo_totale_medio = np.mean(
        tempi_totali
    )

    ogar = (
        sum(passeggeri_in_tempo)
        / len(passeggeri_in_tempo)
    )

    cf = (
        tempo_totale_medio
        / TARGET_TEMPO
    )

    throughput = pax / durata

    load = (
        throughput
        /
        (
            BANCHI_CHECKIN_APERTI
            + NASTRI_SECURITY
        )
    )

    dwell = (
        np.mean(anticipi)
        -
        tempo_totale_medio
    )

    tempo_attesa_tot = (
        np.sum(attese_checkin)
        +
        np.sum(attese_security)
    )

    wti = (
        tempo_attesa_tot
        /
        (pax * TARGET_TEMPO)
    )

    bfi = (
        eventi_congestione
        / durata
    )

    utilization = (
        (
            np.sum(tempi_checkin)
            +
            np.sum(tempi_security)
        )
        /
        (
            durata
            *
            (
                BANCHI_CHECKIN_APERTI
                +
                NASTRI_SECURITY
            )
        )
    )

    # capacità teorica

    cap_checkin = (
        BANCHI_CHECKIN_APERTI
        /
        np.mean(tempi_checkin)
    )

    cap_security = (
        NASTRI_SECURITY
        /
        np.mean(tempi_security)
    )

    capacita = min(
        cap_checkin,
        cap_security
    )

    gap = (
        throughput
        -
        capacita
    )

    pac = capacita

    saturation = load

    sigma = np.std(
        tempi_totali
    )

    # ======================================
    # STAMPA KPI
    # ======================================

    print("\n========== KPI ==========\n")

    print(f"PAX = {pax}")

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

        "GIORNO": str(giorno),

        "OGAR": ogar,

        "UTILIZATION": utilization,

        "LOAD": load,

        "GAP": gap,

        "DWELL": dwell,

        "THROUGHPUT": throughput,

        "PAC": pac,

        "CF": cf,

        "WTI": wti,

        "TEMPO TOTALE MEDIO": tempo_totale_medio,

        "BFI": bfi,

        "SATURATION": saturation

    }])

    risultati.to_excel(
        "output_kpi.xlsx",
        index=False
    )

    print(
        "\nExcel salvato: output_kpi.xlsx"
    )



main()

from plotting import grafici
grafici()