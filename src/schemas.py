from pydantic import BaseModel
from datetime import datetime, date
from typing import List, Optional

class InvoiceBase(BaseModel):
    date_created: datetime
    invoice_id: int
    sale_description: Optional[str] = None
    brand_name: Optional[str] = None
    coach: Optional[str] = None
    invoice_status_str: str
    total: float
    invoice_date: date

class InvoiceCreate(InvoiceBase):
    pass

class Invoice(InvoiceBase):
    id: int

    class Config:
        orm_mode = True

class LineItemBase(BaseModel):
    invoice_id: int
    item_name: str
    line_rate: float
    line_quantity: float
    created_at: datetime
    category: str


class LineItem(LineItemBase):
    id: int

    class Config:
        orm_mode = True


class CategoryReport(BaseModel):
    category: str
    item_count: int
    total_amount: float

class DiscrepancyReport(BaseModel):
    invoice_id: int
    invoice_total: float
    calculated_total: float
    difference: float