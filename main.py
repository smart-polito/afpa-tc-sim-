import simpy
import numpy as np
import pandas as pd

from inputdata import prepara_data_simpy, BANCHI_CHECKIN_APERTI, NASTRI_SECURITY
from generators import spawna_voli
from context import SimulationState
from plotting import grafici


def main():

    state = SimulationState()

    df = prepara_data_simpy()

    giorno = df.groupby("giorno").size().idxmax()
    df = df[df["giorno"] == giorno]

    durata = 600

    env = simpy.Environment()
    checkin = simpy.Resource(env, capacity=BANCHI_CHECKIN_APERTI)
    security = simpy.Resource(env, capacity=NASTRI_SECURITY)

    env.process(spawna_voli(state, env, df, checkin, security))
    env.run(until=durata)

    print("PAX:", len(state.passeggeri_in_tempo))
    print("CHECK-IN:", np.mean(state.tempi_checkin))
    print("SECURITY:", np.mean(state.tempi_security))

    grafici(state)


if __name__ == "__main__":
    main()