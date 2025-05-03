from .database import database
from .models import Invoice, LineItem
from typing import List

class InvoiceService:
    @staticmethod
    def get_all_invoices() -> List[Invoice]:
        with database.get_cursor() as cursor:
            cursor.execute("SELECT * FROM invoices")
            return [Invoice(**row) for row in cursor.fetchall()]

    @staticmethod
    def get_invoice_line_items(invoice_id: int) -> List[LineItem]:
        with database.get_cursor() as cursor:
            cursor.execute(
                "SELECT * FROM invoice_line_items WHERE invoice_id = %s",
                (invoice_id,)
            )
            return [LineItem(**row) for row in cursor.fetchall()]

class ReportService:
    @staticmethod
    def get_category_report() -> List[dict]:
        with database.get_cursor() as cursor:
            cursor.execute("""
                SELECT 
                    category,
                    COUNT(*) as item_count,
                    SUM(line_rate * line_quantity) as total_amount
                FROM invoice_line_items
                GROUP BY category
            """)
            return cursor.fetchall()

    @staticmethod
    def get_discrepancies() -> List[dict]:
        with database.get_cursor() as cursor:
            cursor.execute("""
                SELECT 
                    i.invoice_id,
                    i.total AS invoice_total,
                    SUM(ili.line_rate * ili.line_quantity) AS calculated_total,
                    i.total - SUM(ili.line_rate * ili.line_quantity) AS difference
                FROM 
                    invoices i
                JOIN 
                    invoice_line_items ili ON i.invoice_id = ili.invoice_id
                GROUP BY 
                    i.invoice_id, i.total
                HAVING
                    ABS(i.total - SUM(ili.line_rate * ili.line_quantity)) > 0.01
            """)
            return cursor.fetchall()