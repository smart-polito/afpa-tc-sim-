# Modulo per la generazione di tutti i grafici
import os
import matplotlib.pyplot as plt

from context import SimulationState

# ── GRAFICI ──────────────────────────────────────
# TODO: Questa funzione prenderà in input lo stato globale come istanza della classe SimulationState e realizzerà i diversi grafici.
# Verrà chiamata nel main
# TODO: Completare migrazione al parametro
def grafici(state: SimulationState):
    os.makedirs("output", exist_ok=True)

    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    fig.suptitle("Simulazione Aeroporto Torino Caselle 2025", fontsize=14)

    # grafico 1 — distribuzione tempi totali
    # Esempio di utilizzo dello stato globale come istanza di una classe
    axes[0,0].hist(state.tempi_totali, bins=30, color="steelblue", edgecolor="black")
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