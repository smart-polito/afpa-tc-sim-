import random
import numpy as np
from scipy import stats

from inputdata import (
    TEMPO_CHECKIN_BANCO_MIN,
    TEMPO_BAG_DROP_MIN,
    TEMPO_BAG_DROP_MAX,
    TEMPO_FAST_TRACK_MIN,
    TEMPO_FAST_TRACK_MAX,
    TEMPO_BORDER_CONTROL_MIN,
    TEMPO_BORDER_CONTROL_MAX,
    TEMPO_GATE_VICINO,
    TEMPO_GATE_PIANO2_DISTALE,
    ANTICIPO_MIN,
    ANTICIPO_MAX,
    GATE_CLOSING
)

# ==================================================
# KPI COLLECTION
# ==================================================

tempi_totali = []
tempi_checkin = []
tempi_security = []

passeggeri_in_tempo = []

# anticipo di arrivo in aeroporto
anticipi = []

# attese pure in coda
attese_checkin = []
attese_security = []

# conteggio eventi congestione
eventi_congestione = 0

def tempo_camminata(pax, tipo):

    # =========================================
    # CAMMINATA → CHECK-IN
    # =========================================
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

    # =========================================
    # CHECK-IN → SECURITY
    # =========================================
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

    # =========================================
    # SECURITY → GATE
    # =========================================
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
            return random.uniform(
                TEMPO_GATE_VICINO,
                TEMPO_GATE_PIANO2_DISTALE
            )

    # fallback (sicurezza)
    return random.uniform(2, 5)


def processo_passeggero(env, pax, checkin, security, orario_volo):

    global eventi_congestione

    # ==========================================
    # ARRIVO IN AEROPORTO
    # ==========================================

    anticipo = np.clip(
        stats.norm.rvs(loc=90, scale=20),
        ANTICIPO_MIN,
        ANTICIPO_MAX
    )

    anticipi.append(anticipo)

    orario_arrivo = orario_volo - anticipo

    if orario_arrivo > env.now:
        yield env.timeout(orario_arrivo - env.now)

    t_start = env.now

    # ==========================================
    # CAMMINATA INGRESSO → CHECK-IN
    # ==========================================

    yield env.timeout(
        tempo_camminata(pax, "ingresso_checkin")
    )

    # ==========================================
    # CHECK-IN
    # ==========================================

    if pax.checkin_online == "online_mano":

        tempi_checkin.append(0)
        attese_checkin.append(0)

    else:

        t_coda = env.now

        if len(checkin.queue) > 10:
            eventi_congestione += 1

        with checkin.request() as req:

            yield req

            attesa = env.now - t_coda
            attese_checkin.append(attesa)

            tempo_servizio = random.uniform(
                TEMPO_BAG_DROP_MIN,
                TEMPO_BAG_DROP_MAX
            )

            yield env.timeout(tempo_servizio)

        tempi_checkin.append(
            env.now - t_coda
        )

    # ==========================================
    # CAMMINATA CHECK-IN → SECURITY
    # ==========================================

    yield env.timeout(
        tempo_camminata(pax, "checkin_security")
    )

    # ==========================================
    # SECURITY
    # ==========================================

    t_sec = env.now

    if len(security.queue) > 10:
        eventi_congestione += 1

    with security.request() as req:

        yield req

        attesa_sec = env.now - t_sec
        attese_security.append(attesa_sec)

        tempo_security = stats.lognorm.rvs(
            s=0.4,
            scale=np.exp(0.8)
        )

        yield env.timeout(
            max(0.5, tempo_security)
        )

    tempi_security.append(
        env.now - t_sec
    )

    # ==========================================
    # CAMMINATA SECURITY → GATE
    # ==========================================

    yield env.timeout(
        tempo_camminata(pax, "security_gate")
    )

    # ==========================================
    # KPI FINALI PASSEGGERO
    # ==========================================

    tempo_totale = env.now - t_start

    tempi_totali.append(
        tempo_totale
    )

    in_tempo = (
        env.now <= (orario_volo - GATE_CLOSING)
    )

    passeggeri_in_tempo.append(
        in_tempo
    )