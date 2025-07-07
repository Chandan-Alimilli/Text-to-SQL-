-- Drop existing tables
DROP TABLE IF EXISTS performance;
DROP TABLE IF EXISTS transactions;
DROP TABLE IF EXISTS credit_cards;
DROP TABLE IF EXISTS loans;
DROP TABLE IF EXISTS customers;
DROP TABLE IF EXISTS branches;

-- Create branches
CREATE TABLE branches (
    branch_id INTEGER PRIMARY KEY,
    branch_name TEXT NOT NULL,
    branch_location TEXT NOT NULL
);

-- Create customers
CREATE TABLE customers (
    customer_id INTEGER PRIMARY KEY,
    customer_name TEXT NOT NULL,
    customer_email TEXT NOT NULL,
    branch_id INTEGER,
    FOREIGN KEY (branch_id) REFERENCES branches(branch_id)
);

-- Create transactions
CREATE TABLE transactions (
    transaction_id INTEGER PRIMARY KEY,
    customer_id INTEGER,
    transaction_amount REAL,
    transaction_category TEXT,
    transaction_date TEXT,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

-- Create performance
CREATE TABLE performance (
    performance_id SERIAL PRIMARY KEY,

    branch_id INTEGER,
    performance_month TEXT,
    new_customers INTEGER,
    branch_revenue REAL,
    staff_count INTEGER,
    FOREIGN KEY (branch_id) REFERENCES branches(branch_id)
);

-- Create credit cards
CREATE TABLE credit_cards (
    card_id INTEGER PRIMARY KEY,
    customer_id INTEGER,
    card_type TEXT,
    card_limit REAL,
    card_balance REAL,
    issued_date TEXT,
    status TEXT,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

-- Create loans
CREATE TABLE loans (
    loan_id INTEGER PRIMARY KEY,
    customer_id INTEGER,
    loan_type TEXT,
    loan_amount REAL,
    interest_rate REAL,
    issued_date TEXT,
    due_date TEXT,
    status TEXT,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

-- Seed branches
INSERT INTO branches (branch_id, branch_name, branch_location) VALUES
(1, 'Chase Manhattan', 'New York, NY'),
(2, 'Chase Downtown', 'Chicago, IL'),
(3, 'Chase Westlake', 'Austin, TX');

-- Seed customers
INSERT INTO customers (customer_id, customer_name, customer_email, branch_id) VALUES
(1, 'Alice Johnson', 'alice@chase.com', 1),
(2, 'Bob Smith', 'bob@chase.com', 2),
(3, 'Charlie Brown', 'charlie@chase.com', 1),
(4, 'Diana Prince', 'diana@chase.com', 3),
(5, 'Ethan Hunt', 'ethan@chase.com', 1),
(6, 'Fiona Glenanne', 'fiona@chase.com', 3),
(7, 'George Miller', 'george@chase.com', 2);

-- Seed transactions
INSERT INTO transactions (transaction_id, customer_id, transaction_amount, transaction_category, transaction_date) VALUES
(1, 1, 1200.00, 'Electronics', '2024-05-01'),
(2, 1, 300.00, 'Groceries', '2024-05-02'),
(3, 2, 450.50, 'Travel', '2024-05-03'),
(4, 3, 880.00, 'Entertainment', '2024-05-04'),
(5, 4, 200.00, 'Utilities', '2024-05-05'),
(6, 4, 1500.00, 'Electronics', '2024-05-06'),
(7, 5, 640.00, 'Groceries', '2024-05-07'),
(8, 6, 2100.00, 'Travel', '2024-05-08');

-- Seed performance (3 months)
INSERT INTO performance (branch_id, performance_month, new_customers, branch_revenue, staff_count) VALUES
-- April 2024
(1, '2024-04', 42, 92000.00, 25),
(2, '2024-04', 28, 71000.00, 18),
(3, '2024-04', 40, 95000.00, 22),
-- May 2024
(1, '2024-05', 50, 100000.00, 25),
(2, '2024-05', 30, 75000.00, 18),
(3, '2024-05', 45, 98000.00, 22),
-- June 2024
(1, '2024-06', 55, 105000.00, 26),
(2, '2024-06', 35, 78000.00, 19),
(3, '2024-06', 48, 99000.00, 23);

-- Seed credit cards
INSERT INTO credit_cards (card_id, customer_id, card_type, card_limit, card_balance, issued_date, status) VALUES
(1, 1, 'Platinum', 10000, 2300.50, '2023-02-01', 'Active'),
(2, 2, 'Gold', 7000, 1200.00, '2023-04-15', 'Active'),
(3, 3, 'Silver', 5000, 0.00, '2024-01-10', 'Inactive'),
(4, 5, 'Platinum', 12000, 5500.75, '2024-03-01', 'Active');

-- Seed loans
INSERT INTO loans (loan_id, customer_id, loan_type, loan_amount, interest_rate, issued_date, due_date, status) VALUES
(1, 1, 'Home Loan', 250000, 6.5, '2022-06-01', '2032-06-01', 'Ongoing'),
(2, 4, 'Car Loan', 30000, 7.2, '2023-09-15', '2028-09-15', 'Ongoing'),
(3, 6, 'Personal Loan', 15000, 10.0, '2024-01-20', '2026-01-20', 'Closed'),
(4, 5, 'Education Loan', 40000, 5.5, '2024-02-10', '2029-02-10', 'Ongoing');
