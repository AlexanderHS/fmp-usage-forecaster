from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

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
    date_str: str = None
    
    # after init
    def __post_init__(self):
        self.wait_time_days = max(0, self.wait_time_days)

@dataclass
class Wait:
    qty: int
    wait_time_days: int
    
@dataclass
class WaitDate:
    date: str
    waits: List[Wait]
    qty: Optional[int] = None
    wait_days: Optional[float] = None
    
    def total_qty(self):
        return sum([wait.qty for wait in self.waits])
    
    def wait_weighted_avg(self):
        if self.total_qty() == 0:
            return 0
        total = 0
        for wait in self.waits:
            total += wait.qty * wait.wait_time_days
        return total / self.total_qty()
    
    def __post_init__(self):
        self.qty = self.total_qty()
        self.wait_days = self.wait_weighted_avg()
