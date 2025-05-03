from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .services import InvoiceService, ReportService
from .schemas import Invoice, LineItem, CategoryReport, DiscrepancyReport
from typing import List

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/invoices", response_model=List[Invoice])
def get_invoices():
    return InvoiceService.get_all_invoices()


@app.get("/invoices/{invoice_id}/line-items", response_model=List[LineItem])
def get_line_items(invoice_id: int):
    return InvoiceService.get_invoice_line_items(invoice_id)


@app.get("/reports/categories", response_model=List[CategoryReport])
def get_category_report():
    return ReportService.get_category_report()


@app.get("/reports/discrepancies", response_model=List[DiscrepancyReport])
def get_discrepancies():
    return ReportService.get_discrepancies()