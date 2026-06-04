from process import processo_passeggero
from inputdata import dettaglio_aereo, genera_passeggeri, compagnie_info


def spawna_voli(env, df, checkin, security):

    df = df.sort_values("firstseen")
    start = df["firstseen"].min()

    for _, row in df.iterrows():

        if row["airline"] not in compagnie_info:
            continue

        t = (row["firstseen"] - start).total_seconds() / 60

        if t > env.now:
            yield env.timeout(t - env.now)

        volo = dettaglio_aereo(row["airline"])
        pax_list = genera_passeggeri(volo)

        for pax in pax_list:
            env.process(processo_passeggero(
                env, pax, checkin, security, t
            ))