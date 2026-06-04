import random
import numpy as np
from scipy import stats
from inputdata import *

def tempo_camminata(pax, tipo):
    if tipo == "ingresso_checkin":
        if pax.disabilita:
            return random.uniform(7, 12)
        elif pax.anziano:
            return random.uniform(5, 8)
        elif pax.gruppo >= 3:
            return random.uniform(4, 7)
        elif pax.gruppo == 2:
            return random.uniform(3, 5)
        else:
            return random.uniform(2, 4)

    elif tipo == "checkin_security":
        if pax.disabilita:
            return random.uniform(5, 10)
        elif pax.anziano:
            return random.uniform(4, 7)
        elif pax.gruppo >= 3:
            return random.uniform(3, 6)
        elif pax.gruppo == 2:
            return random.uniform(2, 5)
        else:
            return random.uniform(1, 3)

    elif tipo == "security_gate":
        if pax.disabilita:
            return random.uniform(8, 15)
        elif pax.anziano:
            return random.uniform(6, 12)
        elif pax.gruppo >= 3:
            return random.uniform(5, 10)
        elif pax.gruppo == 2:
            return random.uniform(4, 8)
        else:
            return random.uniform(TEMPO_GATE_VICINO, TEMPO_GATE_PIANO2_DISTALE)


def processo_passeggero(state, env, pax, checkin, security, orario_volo):

    anticipo = np.clip(
        stats.norm.rvs(loc=90, scale=20),
        ANTICIPO_MIN, ANTICIPO_MAX
    )

    orario_arrivo = orario_volo - anticipo
    if orario_arrivo > env.now:
        yield env.timeout(orario_arrivo - env.now)

    t_start = env.now

    yield env.timeout(tempo_camminata(pax, "ingresso_checkin"))

    # CHECK-IN
    t0 = env.now
    with checkin.request() as req:
        yield req
        tempo = random.uniform(TEMPO_BAG_DROP_MIN, TEMPO_BAG_DROP_MAX)
        yield env.timeout(tempo)

    state.tempi_checkin.append(env.now - t0)

    yield env.timeout(tempo_camminata(pax, "checkin_security"))

    # SECURITY
    t1 = env.now
    with security.request() as req:
        yield req
        tempo_sec = stats.lognorm.rvs(s=0.4, scale=np.exp(0.8))
        yield env.timeout(max(0.5, tempo_sec))

    state.tempi_security.append(env.now - t1)

    yield env.timeout(tempo_camminata(pax, "security_gate"))

    in_tempo = env.now <= (orario_volo - GATE_CLOSING)

    state.passeggeri_in_tempo.append(in_tempo)
    state.tempi_totali.append(env.now - t_start)

    # Power BI row
    state.records.append({
        "total_time": env.now - t_start,
        "checkin_time": state.tempi_checkin[-1],
        "security_time": state.tempi_security[-1],
        "in_time": in_tempo,
        "airline": pax.volo.name
    })