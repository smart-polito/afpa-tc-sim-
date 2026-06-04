import os
import numpy as np
import matplotlib.pyplot as plt

def grafici(state):

    os.makedirs("output", exist_ok=True)

    fig, axes = plt.subplots(2, 2, figsize=(12, 8))

    if len(state.tempi_totali) == 0:
        print("No data")
        return

    axes[0,0].hist(state.tempi_totali, bins=30)
    axes[0,0].set_title("Total times")

    axes[0,1].hist(state.tempi_checkin, bins=30)
    axes[0,1].set_title("Check-in")

    axes[1,0].hist(state.tempi_security, bins=30)
    axes[1,0].set_title("Security")

    ogar = np.mean(state.passeggeri_in_tempo)
    cf = np.mean(state.tempi_totali) / 45
    pfpi = ogar / cf if cf > 0 else 0

    axes[1,1].bar(["OGAR","CF","PFPI"], [ogar, cf, pfpi])

    plt.tight_layout()
    plt.savefig("output/kpi.png")
    plt.show()