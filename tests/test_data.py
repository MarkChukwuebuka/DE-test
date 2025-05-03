import pytest
from src.database import database
from src.models import Invoice, LineItem
from typing import List
import pandas as pd


# Fixture to set up test data
@pytest.fixture(scope="module")
def test_data():
    # Load test CSVs
    invoices_df = pd.read_csv('data/invoices_test.csv')
    line_items_df = pd.read_csv('data/invoice_line_items_test.csv')
    return invoices_df, line_items_df


def test_database_connection():
    """Test that database connection works"""
    with database.get_connection() as conn:
        assert not conn.closed
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
            assert cur.fetchone()[0] == 1


def test_table_structures():
    """Verify table schemas match expectations"""
    with database.get_cursor() as cursor:
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'invoices'
        """)
        invoice_columns = {row['column_name']: row['data_type'] for row in cursor.fetchall()}

        expected_invoice_columns = {
            'id': 'integer',
            'date_created': 'timestamp without time zone',
            'invoice_id': 'integer',
            'sale_description': 'text',
            'brand_name': 'text',
            'coach': 'text',
            'invoice_status_str': 'text',
            'total': 'numeric',
            'invoice_date': 'date'
        }
        assert invoice_columns == expected_invoice_columns


def test_invoice_totals_match(test_data):
    """Verify that invoice totals match sum of line items"""
    invoices_df, line_items_df = test_data

    with database.get_cursor() as cursor:
        cursor.execute("""
            SELECT 
                i.invoice_id,
                i.total AS invoice_total,
                SUM(ili.line_rate * ili.line_quantity) AS calculated_total
            FROM 
                invoices i
            JOIN 
                invoice_line_items ili ON i.invoice_id = ili.invoice_id
            GROUP BY 
                i.invoice_id, i.total
        """)
        results = cursor.fetchall()

        discrepancies = []
        for row in results:
            if abs(row['invoice_total'] - row['calculated_total']) > 0.01:  # Allow for floating point rounding
                discrepancies.append({
                    'invoice_id': row['invoice_id'],
                    'invoice_total': row['invoice_total'],
                    'calculated_total': row['calculated_total'],
                    'difference': row['invoice_total'] - row['calculated_total']
                })

        assert len(discrepancies) == 0, f"Found {len(discrepancies)} invoices with mismatched totals: {discrepancies}"


def test_no_null_invoice_ids():
    """Ensure no invoices have null invoice_id"""
    with database.get_cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM invoices WHERE invoice_id IS NULL")
        count = cursor.fetchone()['count']
        assert count == 0, f"Found {count} invoices with null invoice_id"


def test_line_item_categories():
    """Verify all line items have been properly categorized"""
    valid_categories = {'coaching', 'outbound', 'shipping', 'rollover', 'supplement'}

    with database.get_cursor() as cursor:
        cursor.execute("SELECT DISTINCT category FROM invoice_line_items")
        categories = {row['category'] for row in cursor.fetchall()}

        # Check for unexpected categories
        invalid_categories = categories - valid_categories
        assert not invalid_categories, f"Found invalid categories: {invalid_categories}"

        # Check no null categories
        cursor.execute("SELECT COUNT(*) FROM invoice_line_items WHERE category IS NULL")
        null_count = cursor.fetchone()['count']
        assert null_count == 0, f"Found {null_count} line items with null category"


def test_referential_integrity():
    """Verify all line items reference valid invoices"""
    with database.get_cursor() as cursor:
        cursor.execute("""
            SELECT COUNT(*) 
            FROM invoice_line_items ili
            LEFT JOIN invoices i ON ili.invoice_id = i.invoice_id
            WHERE i.invoice_id IS NULL
        """)
        orphaned_count = cursor.fetchone()['count']
        assert orphaned_count == 0, f"Found {orphaned_count} line items referencing non-existent invoices"


def test_date_ranges():
    """Verify date fields contain reasonable values"""
    with database.get_cursor() as cursor:
        # Check invoice dates are not in the future
        cursor.execute("""
            SELECT COUNT(*) 
            FROM invoices 
            WHERE invoice_date > CURRENT_DATE
        """)
        future_dates = cursor.fetchone()['count']
        assert future_dates == 0, f"Found {future_dates} invoices with future dates"

        # Check created_at dates are not in the future
        cursor.execute("""
            SELECT COUNT(*) 
            FROM invoice_line_items 
            WHERE created_at > CURRENT_TIMESTAMP
        """)
        future_created = cursor.fetchone()['count']
        assert future_created == 0, f"Found {future_created} line items with future created_at dates"


def test_positive_values():
    """Verify monetary values are positive"""
    with database.get_cursor() as cursor:
        # Check invoice totals
        cursor.execute("""
            SELECT COUNT(*) 
            FROM invoices 
            WHERE total <= 0
        """)
        non_positive_totals = cursor.fetchone()['count']
        assert non_positive_totals == 0, f"Found {non_positive_totals} invoices with non-positive totals"

        # Check line item rates
        cursor.execute("""
            SELECT COUNT(*) 
            FROM invoice_line_items 
            WHERE line_rate <= 0
        """)
        non_positive_rates = cursor.fetchone()['count']
        assert non_positive_rates == 0, f"Found {non_positive_rates} line items with non-positive rates"

        # Check line item quantities
        cursor.execute("""
            SELECT COUNT(*) 
            FROM invoice_line_items 
            WHERE line_quantity <= 0
        """)
        non_positive_quantities = cursor.fetchone()['count']
        assert non_positive_quantities == 0, f"Found {non_positive_quantities} line items with non-positive quantities"