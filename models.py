from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

# modules
import e2_queries

@dataclass
class OrderLine:
    code: str
    base_qty: int
    date: str
    site: str

@dataclass
class OrderDay:
    date: str # 10 char ISO 8601
    qty: int
    
@dataclass
class WaitDatabaseLine:
    site: str
    item_code: str
    customer_code: str
    wait_time_days: int
    qty_eaches_sent: int
    date_required: datetime
    date_despatched: datetime
    cda: str
    est_value: float = None
    date_str: str = None
    required_str: str = None
    day: int = None
    month: int = None
    year: int = None
    
    # after init
    def __post_init__(self):
        self.wait_time_days = max(0, self.wait_time_days)
        self.est_value = self.qty_eaches_sent * e2_queries.get_item_costs().get(self.item_code, 0)

@dataclass
class Wait:
    est_value: float
    wait_time_days: int
    
@dataclass
class WaitDate:
    date: str
    waits: List[Wait]
    est_value: Optional[float] = None
    wait_days: Optional[float] = None
    window_size: Optional[int] = None
    mode: str = 'mean'
    
    def total_est_value(self):
        if not self.waits:
            return 0
        if self.window_size and self.window_size > 0:
            return sum([wait.est_value for wait in self.waits]) / self.window_size
        return sum([wait.est_value for wait in self.waits])
    
    def wait_weighted_avg(self):
        if self.total_est_value() == 0:
            return 0
        total = 0
        for wait in self.waits:
            total += wait.est_value * wait.wait_time_days
        return total / self.total_est_value()
    
    def wait_median(self):
        if self.total_est_value() == 0:
            return 0
        waits = sorted([wait.wait_time_days for wait in self.waits])
        if len(waits) % 2 == 1:
            return waits[len(waits) // 2]
        return (waits[len(waits) // 2] + waits[len(waits) // 2 - 1]) / 2
    
    def wait_max(self):
        if self.total_est_value() == 0:
            return 0
        return max([wait.wait_time_days for wait in self.waits])
    
    def wait_min(self):
        if self.total_est_value() == 0:
            return 0
        return min([wait.wait_time_days for wait in self.waits])
    
    def wait_mode(self):
        if self.total_est_value() == 0:
            return 0
        counts = {}
        for wait in self.waits:
            if wait.wait_time_days not in counts:
                counts[wait.wait_time_days] = 0
            counts[wait.wait_time_days] += wait.est_value
        return max(counts, key=counts.get)
       
    
    def __post_init__(self):
        self.est_value = self.total_est_value()
        if self.mode == 'mean':
            self.wait_days = self.wait_weighted_avg()
        if self.mode == 'median':
            self.wait_days = self.wait_median()
        if self.mode == 'max':
            self.wait_days = self.wait_max()
        if self.mode == 'min':
            self.wait_days = self.wait_min()
        if self.mode == 'mode':
            self.wait_days = self.wait_mode()
