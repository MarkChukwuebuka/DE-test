import psycopg2
from psycopg2.extras import execute_batch
from typing import Dict, Any
from database import database
import numpy as np
import pandas as pd
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def classify_item(item_name: str) -> str:
    """
    Classify line items into categories based on item_name content
    Args:
        item_name: The name of the line item to classify
    Returns:
        str: The classified category
    """
    if pd.isna(item_name):
        return 'supplement'

    item_lower = str(item_name).lower()

    if any(keyword in item_lower for keyword in ['coaching', 'program', 'training']):
        return 'coaching'
    elif any(keyword in item_lower for keyword in ['opportunity', 'offer', 'scholarship']):
        return 'outbound'
    elif any(keyword in item_lower for keyword in ['shipping', 'delivery', 'freight']):
        return 'shipping'
    elif any(keyword in item_lower for keyword in ['rollover', 'carryover', 'transfer']):
        return 'rollover'
    else:
        return 'supplement'


def convert_datetime_to_python(dt):
    """Convert numpy datetime64 to Python datetime"""
    if pd.isna(dt):
        return None
    if isinstance(dt, np.datetime64):
        return pd.Timestamp(dt).to_pydatetime()
    return dt


def clean_invoice_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and transform invoice data before loading
    """
    # Convert date columns with proper type handling
    df['date_created'] = pd.to_datetime(
        df['date_created'],
        format='ISO8601',
        errors='coerce'
    ).apply(convert_datetime_to_python)

    df['invoice_date'] = pd.to_datetime(
        df['invoice_date'],
        format='ISO8601',
        errors='coerce'
    ).dt.date

    # Handle missing values
    df['sale_description'] = df['sale_description'].fillna('')
    df['brand_name'] = df['brand_name'].fillna('')
    df['coach'] = df['coach'].fillna('Not assigned')

    # Ensure numeric field
    df['total'] = pd.to_numeric(df['total'], errors='coerce')

    return df


def clean_line_item_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and transform line item data before loading
    """
    # Convert date column with proper type handling
    df['created_at'] = pd.to_datetime(
        df['created_at'],
        format='ISO8601',
        errors='coerce',
        utc=True
    ).apply(convert_datetime_to_python)

    # Handle missing values
    df['item_name'] = df['item_name'].fillna('')

    # Ensure numeric fields
    df['line_rate'] = pd.to_numeric(df['line_rate'], errors='coerce')
    df['line_quantity'] = pd.to_numeric(df['line_quantity'], errors='coerce')

    # Classify items
    df['category'] = df['item_name'].apply(classify_item)

    return df


def load_invoices(invoice_data: pd.DataFrame) -> int:
    """
    Load invoice data into database with proper type conversion
    """
    insert_query = """
        INSERT INTO invoices (
            date_created, invoice_id, sale_description, 
            brand_name, coach, invoice_status_str, 
            total, invoice_date
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (invoice_id) DO NOTHING
    """

    # Convert DataFrame to list of tuples with proper types
    records = [
        (
            row['date_created'],
            int(row['invoice_id']),
            str(row['sale_description']),
            str(row['brand_name']),
            str(row['coach']),
            str(row['invoice_status_str']),
            float(row['total']),
            row['invoice_date']
        )
        for _, row in invoice_data.iterrows()
    ]

    with database.get_cursor() as cursor:
        execute_batch(cursor, insert_query, records)
        return cursor.rowcount


def load_line_items(line_item_data: pd.DataFrame) -> int:
    """
    Load line item data into database with proper type conversion
    """
    insert_query = """
        INSERT INTO invoice_line_items (
            invoice_id, item_name, line_rate, 
            line_quantity, created_at, category
        ) VALUES (%s, %s, %s, %s, %s, %s)
    """

    # Convert DataFrame to list of tuples with proper types
    records = [
        (
            int(row['invoice_id']),
            str(row['item_name']),
            float(row['line_rate']),
            float(row['line_quantity']),
            row['created_at'],
            str(row['category'])
        )
        for _, row in line_item_data.iterrows()
    ]

    with database.get_cursor() as cursor:
        execute_batch(cursor, insert_query, records)
        return cursor.rowcount


def validate_data(invoice_df: pd.DataFrame, line_item_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Perform comprehensive data validation before loading
    """
    validation_results = {}

    # Get valid invoice IDs
    valid_invoice_ids = set(invoice_df['invoice_id'])

    # Check for line items referencing missing invoices
    missing_refs = line_item_df[~line_item_df['invoice_id'].isin(valid_invoice_ids)]
    if not missing_refs.empty:
        validation_results['missing_invoice_ids'] = len(missing_refs)
        logger.warning(
            f"Found {len(missing_refs)} line items referencing missing invoices. "
            f"Example missing invoice IDs: {missing_refs['invoice_id'].unique()[:5]}"
        )

    # Other validations remain the same
    validation_results.update({
        'negative_totals': invoice_df[invoice_df['total'] <= 0].shape[0],
        'negative_rates': line_item_df[line_item_df['line_rate'] <= 0].shape[0],
        'negative_quantities': line_item_df[line_item_df['line_quantity'] <= 0].shape[0],
        'future_dates': invoice_df[pd.to_datetime(invoice_df['invoice_date']) > pd.Timestamp.now()].shape[0],
    })

    return {k: v for k, v in validation_results.items() if v > 0}


def main():
    """Main data loading function with referential integrity checks"""
    try:
        logger.info("Starting data loading process")

        # Load CSV files
        invoice_df = pd.read_csv('data/invoices_test.csv')
        line_item_df = pd.read_csv('data/invoice_line_items_test.csv')

        # Clean data
        clean_invoices = clean_invoice_data(invoice_df)
        clean_line_items = clean_line_item_data(line_item_df)

        # Validate data
        validation_results = validate_data(clean_invoices, clean_line_items)
        if validation_results:
            logger.warning(f"Data validation issues found: {validation_results}")

        # Filter out line items with missing invoices
        valid_invoice_ids = set(clean_invoices['invoice_id'])
        clean_line_items = clean_line_items[clean_line_items['invoice_id'].isin(valid_invoice_ids)]

        # Report on filtered line items
        original_count = len(line_item_df)
        filtered_count = len(clean_line_items)
        if filtered_count < original_count:
            logger.warning(
                f"Filtered out {original_count - filtered_count} line items "
                f"with missing invoices ({filtered_count}/{original_count} kept)"
            )

        # Load data into database
        start_time = datetime.now()
        invoice_count = load_invoices(clean_invoices)
        line_item_count = load_line_items(clean_line_items)

        logger.info(f"""
            Data loading completed in {(datetime.now() - start_time).total_seconds():.2f} seconds
            Invoices loaded: {invoice_count}
            Line items loaded: {line_item_count}
        """)

    except Exception as e:
        logger.error(f"Data loading failed: {str(e)}")
        raise


if __name__ == "__main__":
    main()