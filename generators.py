# Tutti i generatori di entità metterli qui
import random

from events import Airplane, Passeggero
from inputdata import dettaglio_aereo, PCT_CHECKIN_ONLINE_SOLO_MANO, PCT_CHECKIN_ONLINE_BAG_DROP, \
    PCT_CHECKIN_BANCO_COMPLETO, PCT_SCHENGEN, compagnie_info
from main import processo_passeggero


# ── GENERATORE VOLI ──────────────────────────────
def spawna_voli(env, df, checkin, security):

    # ordina per orario cronologico
    df = df.sort_values("firstseen").reset_index(drop=True)
    t_inizio = df["firstseen"].min()

    for i, row in df.iterrows():
        airline = row["airline"]
        if airline not in compagnie_info:
            continue        # Skippa l'iterazione corrente se il codice dell'aereo non è nella lista di quelli noti

        # converti orario volo in minuti dall'inizio simulazione
        orario_volo = (row["firstseen"] - t_inizio).total_seconds() / 60

        # aspetta fino all'orario del volo
        if orario_volo > env.now:
            yield env.timeout(orario_volo - env.now)

        # crea aereo dalla compagnia
        aereo = dettaglio_aereo(airline)

        # genera tutti i passeggeri del volo
        passeggeri = genera_passeggeri(aereo)

        # lancia processo SimPy per ogni passeggero
        for pax in passeggeri:
            env.process(processo_passeggero(
                env, pax, checkin, security, orario_volo
            ))
        # NON c'è yield qui — passa subito al volo successivo
        # è SimPy che gestisce i passeggeri in parallelo



def genera_passeggeri(volo: Airplane) -> list[Passeggero]:
    """Generatore delle entità Passeggero con diverse caratteristiche, seguendo le statistiche ufficiali, in base allo specifico aereo che devono raggiungere. """
    passeggeri = []
    n = volo.passeggeri_totali()

    for i in range(n):
        r = random.random()                     # TODO: Distribuzione delle diverse tipologie di checkin o percentuali
        if r < PCT_CHECKIN_ONLINE_SOLO_MANO:
            checkin = "online_mano"
        elif r < PCT_CHECKIN_ONLINE_SOLO_MANO + PCT_CHECKIN_ONLINE_BAG_DROP:
            checkin = "bag_drop"
        elif r < PCT_CHECKIN_ONLINE_SOLO_MANO + PCT_CHECKIN_ONLINE_BAG_DROP + PCT_CHECKIN_BANCO_COMPLETO:
            checkin = "banco"
        else:
            checkin = "kiosk"

        p = Passeggero(
            nome=f"PAX_{volo.name}_{i+1}",          # TIP: E' utile estrapolare le funzioni che calcolano degli UUID (Id univoci) in spazi a parte per poterle ri-utilizzare e non sbagliare. Questo diventerebbe: nome=gen_passenger_uuid(volo)
            schengen=random.random() < PCT_SCHENGEN,
            anziano=random.random() < 0.10,         # TODO: Strutturare meglio i numeri con cui generiamo i diversi tipi di passeggero
            bagaglio_stiva=random.random() < 0.60,
            disabilita=random.random() < 0.02,
            checkin_online=checkin,
            gruppo=random.choices([1, 2, 3, 4], weights=[0.50, 0.25, 0.15, 0.10])[0],       # TODO: Così ignoriamo gruppi più grandi di 4 persone
            tolleranza_overbooking=random.random() < 0.30,
            volo=volo
        )
        passeggeri.append(p)

    return passeggeri