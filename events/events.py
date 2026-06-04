import dataclasses

@dataclasses.dataclass
class Airplane:
    name: str
    type: str
    capacity: int
    load_factor: float

    def passeggeri_totali(self):
        return int(self.capacity * self.load_factor)

@dataclasses.dataclass
class Passeggero:
    nome: str
    schengen: bool
    anziano: bool
    bagaglio_stiva: bool
    disabilita: bool
    checkin_online: str       # "online_mano", "bag_drop", "banco", "kiosk"
    gruppo: int               # 1=singolo, 2=coppia, 3-4=famiglia, 5+=gruppo grande
    tolleranza_overbooking: bool
    fast_track: bool          # ha acquistato fast track SAGAT
    egate: bool               # usa e-gate biometrico (solo extra-schengen)
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