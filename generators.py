from events import Airplane, Passeggero
from inputdata import dettaglio_aereo, genera_passeggeri, compagnie_info


def spawna_voli(state, env, df, checkin, security):

    df = df.sort_values("firstseen")
    t_inizio = df["firstseen"].min()

    from process import processo_passeggero

    for _, row in df.iterrows():

        airline = row["airline"]
        if airline not in compagnie_info:
            continue

        orario_volo = (row["firstseen"] - t_inizio).total_seconds() / 60

        if orario_volo > env.now:
            yield env.timeout(orario_volo - env.now)

        aereo = dettaglio_aereo(airline)
        passeggeri = genera_passeggeri(aereo)

        for pax in passeggeri:
            env.process(processo_passeggero(
                state, env, pax, checkin, security, orario_volo
            ))