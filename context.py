import dataclasses

# TODO: Come metodi di questa classe si possono mettere tutte le funzioni che possono essere utili per calcolare tempi parziali o simili
@dataclasses.dataclass
class SimulationState:
    """Rappresenta lo stato globale della simulazione con i diversi tempi di processo"""
    tempi_totali = []
    tempi_checkin = []
    tempi_security = []
    passeggeri_in_tempo = []
    voli_puntuali = []