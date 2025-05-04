from dataclasses import dataclass
from datetime import datetime, date

@dataclass
class Invoice:
    id: int
    date_created: datetime
    invoice_id: int
    sale_description: str
    brand_name: str
    coach: str
    invoice_status_str: str
    total: float
    invoice_date: date


@dataclass
class LineItem:
    id: int
    invoice_id: int
    item_name: str
    line_rate: float
    line_quantity: float
    created_at: datetime
    category: str