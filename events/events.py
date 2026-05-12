import dataclasses

# Rappresenta un generico aereo nell'aereoporto
import dataclasses

@dataclasses.dataclass
class Airplane:
    name: str
    type: str
    capacity: int
    load_factor: float

    def passeggeri_totali(self):
        """Restituisce il numero di passeggeri totali del volo come prodotto della capacità massima per il load_factor"""
        return int(self.capacity * self.load_factor)

@dataclasses.dataclass
class Passeggero:
    nome: str
    schengen: bool
    anziano: bool
    bagaglio_stiva: bool
    disabilita: bool
    checkin_online: str    # "online_mano", "bag_drop", "banco", "kiosk"
    gruppo: int            # 1 = singolo, 2+ = famiglia
    tolleranza_overbooking: bool
    volo: Airplane

# Creare un evento "Decollo aereo" legato al tipo di aereo
# Evento arrivo passeggero in aereoporto --> Accade quando un certo passeggero arriva in aereoporto, contiene le info specifiche sotto forma di istanza della classe Passeggero
# Incanalamento dei passeggeri guardando la frequenza di decollo delle diverse compagnie

# Creare una classe passeggero che rappresenta un pass. che transita nell'aereoporto
# shenghen o extra shenghen
# anzianità o velocità di movimento
# bagaglio o meno --> Da stiva o bagaglio a mano
# disabilità
# caratteristiche del biglietto (online o meno)
# Tolleranza all'overbooking
# Gruppi di passeggeri (famiglie, singoli)