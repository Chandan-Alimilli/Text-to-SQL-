-- Drop existing tables if they exist
DROP TABLE IF EXISTS performance;
DROP TABLE IF EXISTS transactions;
DROP TABLE IF EXISTS customers;
DROP TABLE IF EXISTS branches;

-- Create branches table
CREATE TABLE branches (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    location TEXT NOT NULL
);

-- Create customers table
CREATE TABLE customers (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    branch_id INTEGER,
    FOREIGN KEY (branch_id) REFERENCES branches(id)
);

-- Create transactions table
CREATE TABLE transactions (
    id INTEGER PRIMARY KEY,
    customer_id INTEGER,
    amount REAL,
    category TEXT,
    date TEXT,
    FOREIGN KEY (customer_id) REFERENCES customers(id)
);

-- Create performance table
CREATE TABLE performance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    branch_id INTEGER,
    month TEXT,
    new_customers INTEGER,
    revenue REAL,
    staff_count INTEGER,
    FOREIGN KEY (branch_id) REFERENCES branches(id)
);

-- Seed data for branches
INSERT INTO branches (id, name, location) VALUES
(1, 'Chase Manhattan', 'New York, NY'),
(2, 'Chase Downtown', 'Chicago, IL'),
(3, 'Chase Westlake', 'Austin, TX');

-- Seed data for customers
INSERT INTO customers (id, name, email, branch_id) VALUES
(1, 'Alice Johnson', 'alice@chase.com', 1),
(2, 'Bob Smith', 'bob@chase.com', 2),
(3, 'Charlie Brown', 'charlie@chase.com', 1),
(4, 'Diana Prince', 'diana@chase.com', 3);

-- Seed data for transactions
INSERT INTO transactions (id, customer_id, amount, category, date) VALUES
(1, 1, 1200.00, 'Electronics', '2024-05-01'),
(2, 1, 300.00, 'Groceries', '2024-05-02'),
(3, 2, 450.50, 'Travel', '2024-05-03'),
(4, 3, 880.00, 'Entertainment', '2024-05-04'),
(5, 4, 200.00, 'Utilities', '2024-05-05'),
(6, 4, 1500.00, 'Electronics', '2024-05-06');

-- Seed data for performance
INSERT INTO performance (branch_id, month, new_customers, revenue, staff_count) VALUES
(1, '2024-05', 50, 100000.00, 25),
(2, '2024-05', 30, 75000.00, 18),
(3, '2024-05', 45, 98000.00, 22);
