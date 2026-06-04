from dataclasses import dataclass, field
from collections import defaultdict
import numpy as np

@dataclass
class SimulationState:
    # KPI raw per giorno
    pax_total: defaultdict = field(default_factory=lambda: defaultdict(int))
    pax_in_time: defaultdict = field(default_factory=lambda: defaultdict(int))

    tempi_totali: defaultdict = field(default_factory=lambda: defaultdict(list))
    tempi_checkin: defaultdict = field(default_factory=lambda: defaultdict(list))
    tempi_security: defaultdict = field(default_factory=lambda: defaultdict(list))

    congestioni: defaultdict = field(default_factory=lambda: defaultdict(int))
    capacity_used: defaultdict = field(default_factory=lambda: defaultdict(int))

    def add_pax(self, day, in_time):
        self.pax_total[day] += 1
        if in_time:
            self.pax_in_time[day] += 1

    def ogar(self, day):
        if self.pax_total[day] == 0:
            return 0
        return self.pax_in_time[day] / self.pax_total[day]

    def tempo_medio(self, day):
        return np.mean(self.tempi_totali[day]) if self.tempi_totali[day] else 0