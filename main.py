# This is a sample Python script.
from events.events import Passeggero
# Press ⌃R to execute it or replace it with your code.
# Press Double ⇧ to search everywhere for classes, files, tool windows, actions, and settings.
from inputdata import prepara_data_simpy, dettaglio_aereo
import simpy

# SPAwneremo entità passeggero modificandone le caratteristiche tramite delle distribuzioni
def spawna_passeggeri() -> list[Passeggero]:
    # usa distribuzioni per generare istanze della classe passeggero diverse tra di loro

    return .....

def main():
    dati = prepara_data_simpy()
    rayanair = dettaglio_aereo("RYR")
    print(rayanair.load_factor)
    rayanair.dimmiciao()

    # spawn di eventi "Decollo aereo" in base alla distribuzione che ci darà riccardo
    env = simpy.Environment()
    p = simpy.events.Process(env, )

    print(ilmioAereo.name)
    env.run()

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    main()

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
