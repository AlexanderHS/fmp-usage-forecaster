from dataclasses import dataclass

@dataclass
class OrderLine:
    code: str
    base_qty: int
    date: str
    site: str

@dataclass
class OrderDay:
    date: str # 10 char ISO 801
    qty: int