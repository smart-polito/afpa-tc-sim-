import os
import numpy as np
import matplotlib.pyplot as plt

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


def grafici():

    os.makedirs("output", exist_ok=True)

    if len(tempi_totali) == 0:
        print("❌ Nessun dato disponibile per i grafici")
        return

    fig, axes = plt.subplots(2, 2, figsize=(14, 9))
    fig.suptitle("Simulazione Aeroporto - KPI Dashboard", fontsize=16)

    # ==================================================
    # 1. TEMPI TOTALI
    # ==================================================
    axes[0, 0].hist(
        tempi_totali,
        bins=40,
        edgecolor="black",
        alpha=0.75
    )
    axes[0, 0].axvline(
        45,
        color="red",
        linestyle="--",
        label="Target 45 min"
    )
    axes[0, 0].set_title("Distribuzione Tempi Totali")
    axes[0, 0].set_xlabel("Minuti")
    axes[0, 0].set_ylabel("Passeggeri")
    axes[0, 0].legend()

    # ==================================================
    # 2. CHECK-IN
    # ==================================================
    axes[0, 1].hist(
        tempi_checkin,
        bins=40,
        edgecolor="black",
        alpha=0.75,
        color="orange"
    )
    axes[0, 1].set_title("Distribuzione Check-in")
    axes[0, 1].set_xlabel("Minuti")
    axes[0, 1].set_ylabel("Passeggeri")

    # ==================================================
    # 3. SECURITY
    # ==================================================
    axes[1, 0].hist(
        tempi_security,
        bins=40,
        edgecolor="black",
        alpha=0.75,
        color="green"
    )
    axes[1, 0].axvline(
        4.5,
        color="red",
        linestyle="--",
        label="P90 Security"
    )
    axes[1, 0].set_title("Distribuzione Security")
    axes[1, 0].set_xlabel("Minuti")
    axes[1, 0].set_ylabel("Passeggeri")
    axes[1, 0].legend()

    # ==================================================
    # 4. KPI MULTIPLI (quello che vuoi tu)
    # ==================================================

    # protezione divisioni
    pax = len(tempi_totali) if len(tempi_totali) > 0 else 1

    ogar = sum(passeggeri_in_tempo) / pax
    cf = np.mean(tempi_totali) / 45 if len(tempi_totali) > 0 else 0
    utilization = (
        (np.sum(tempi_checkin) + np.sum(tempi_security))
        / (pax * 10)
    ) if pax > 0 else 0

    throughput = pax / 600
    load = throughput / 30 if pax > 0 else 0
    wti = (np.sum(attese_checkin) + np.sum(attese_security)) / (pax * 45) if pax > 0 else 0
    bfi = eventi_congestione / 600 if 600 > 0 else 0
    dwell = np.mean(anticipi) - np.mean(tempi_totali) if len(anticipi) > 0 else 0
    saturation = load

    kpi_labels = [
        "OGAR",
        "CF",
        "UTIL",
        "LOAD",
        "THR",
        "WTI",
        "BFI",
        "DWELL",
        "SAT"
    ]

    kpi_values = [
        ogar,
        cf,
        utilization,
        load,
        throughput,
        wti,
        bfi,
        dwell,
        saturation
    ]

    colors = [
        "green" if v >= 0.8 else "orange" if v >= 0.5 else "red"
        for v in kpi_values
    ]

    axes[1, 1].bar(
        kpi_labels,
        kpi_values,
        color=colors,
        edgecolor="black"
    )

    axes[1, 1].set_title("KPI Overview")
    axes[1, 1].tick_params(axis="x", rotation=45)

    plt.tight_layout()
    plt.savefig("output/kpi_dashboard.png", dpi=150)
    plt.show()

    print("✅ Dashboard salvata in output/kpi_dashboard.png")