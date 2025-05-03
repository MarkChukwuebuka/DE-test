CREATE TABLE IF NOT EXISTS invoices (
    id SERIAL PRIMARY KEY,
    date_created TIMESTAMP,
    invoice_id INTEGER UNIQUE,
    sale_description TEXT,
    brand_name TEXT,
    coach TEXT,
    invoice_status_str TEXT,
    total DECIMAL(10, 2),
    invoice_date DATE
);

CREATE TABLE IF NOT EXISTS invoice_line_items (
    id SERIAL PRIMARY KEY,
    invoice_id INTEGER REFERENCES invoices(invoice_id),
    item_name TEXT,
    line_rate DECIMAL(10, 2),
    line_quantity DECIMAL(10, 2),
    created_at TIMESTAMP,
    category TEXT
);


-- First drop existing constraints if they exist
ALTER TABLE IF EXISTS invoice_line_items
DROP CONSTRAINT IF EXISTS invoice_line_items_invoice_id_fkey;

-- Then recreate with proper ON DELETE behavior
ALTER TABLE invoice_line_items
ADD CONSTRAINT invoice_line_items_invoice_id_fkey
FOREIGN KEY (invoice_id) REFERENCES invoices(invoice_id)
ON DELETE CASCADE;