"""
Double-entry accounting system
"""
from datetime import datetime
from database import get_connection, get_account_by_code

def create_journal_entry(entry_date, description, lines, reference=None):
    """
    Create a journal entry with multiple lines (double-entry)
    lines = [{'account_id': 1, 'debit': 100, 'credit': 0}, ...]
    Total debits must equal total credits
    """
    total_debit = sum(line.get('debit', 0) for line in lines)
    total_credit = sum(line.get('credit', 0) for line in lines)

    if abs(total_debit - total_credit) > 0.01:
        raise ValueError(f"Debits ({total_debit}) must equal Credits ({total_credit})")

    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO journal_entries (entry_date, reference, description)
            VALUES (?, ?, ?)
        ''', (entry_date, reference, description))
        entry_id = cursor.lastrowid

        for line in lines:
            cursor.execute('''
                INSERT INTO journal_lines (entry_id, account_id, debit, credit)
                VALUES (?, ?, ?, ?)
            ''', (entry_id, line['account_id'], line.get('debit', 0), line.get('credit', 0)))

            # Update account balance
            debit = line.get('debit', 0)
            credit = line.get('credit', 0)
            cursor.execute('SELECT account_type FROM accounts WHERE id = ?', (line['account_id'],))
            acc = cursor.fetchone()
            if acc:
                acc_type = acc[0]
                if acc_type in ('asset', 'expense'):
                    balance_change = debit - credit
                else:
                    balance_change = credit - debit
                cursor.execute('UPDATE accounts SET balance = balance + ? WHERE id = ?',
                             (balance_change, line['account_id']))

        conn.commit()
        return entry_id

def record_sale(sale_id, total_amount, cost_of_goods, payment_amount=0):
    """Record accounting entries for a sale"""
    cash_acc = get_account_by_code('1100')
    ar_acc = get_account_by_code('1300')
    inventory_acc = get_account_by_code('1400')
    sales_acc = get_account_by_code('4100')
    cogs_acc = get_account_by_code('5100')

    lines = []
    if payment_amount > 0:
        lines.append({'account_id': cash_acc['id'], 'debit': payment_amount, 'credit': 0})
    if payment_amount < total_amount:
        lines.append({'account_id': ar_acc['id'], 'debit': total_amount - payment_amount, 'credit': 0})
    lines.append({'account_id': sales_acc['id'], 'debit': 0, 'credit': total_amount})

    entry_id = create_journal_entry(
        datetime.now().date(),
        f'Sale Invoice #{sale_id}',
        lines,
        f'SALE-{sale_id}'
    )

    if cost_of_goods > 0:
        cogs_lines = [
            {'account_id': cogs_acc['id'], 'debit': cost_of_goods, 'credit': 0},
            {'account_id': inventory_acc['id'], 'debit': 0, 'credit': cost_of_goods}
        ]
        create_journal_entry(
            datetime.now().date(),
            f'COGS for Sale #{sale_id}',
            cogs_lines,
            f'COGS-{sale_id}'
        )

    return entry_id

def record_purchase(purchase_id, total_amount, payment_amount=0):
    """Record accounting entries for a purchase"""
    cash_acc = get_account_by_code('1100')
    ap_acc = get_account_by_code('2100')
    inventory_acc = get_account_by_code('1400')

    lines = [
        {'account_id': inventory_acc['id'], 'debit': total_amount, 'credit': 0}
    ]
    if payment_amount > 0:
        lines.append({'account_id': cash_acc['id'], 'debit': 0, 'credit': payment_amount})
    if payment_amount < total_amount:
        lines.append({'account_id': ap_acc['id'], 'debit': 0, 'credit': total_amount - payment_amount})

    return create_journal_entry(
        datetime.now().date(),
        f'Purchase Invoice #{purchase_id}',
        lines,
        f'PUR-{purchase_id}'
    )

def record_payment_received(customer_id, amount, reference=None):
    """Record payment received from customer"""
    cash_acc = get_account_by_code('1100')
    ar_acc = get_account_by_code('1300')

    lines = [
        {'account_id': cash_acc['id'], 'debit': amount, 'credit': 0},
        {'account_id': ar_acc['id'], 'debit': 0, 'credit': amount}
    ]

    return create_journal_entry(
        datetime.now().date(),
        f'Payment received - Customer #{customer_id}',
        lines,
        reference
    )

def record_payment_made(supplier_id, amount, reference=None):
    """Record payment made to supplier"""
    cash_acc = get_account_by_code('1100')
    ap_acc = get_account_by_code('2100')

    lines = [
        {'account_id': ap_acc['id'], 'debit': amount, 'credit': 0},
        {'account_id': cash_acc['id'], 'debit': 0, 'credit': amount}
    ]

    return create_journal_entry(
        datetime.now().date(),
        f'Payment made - Supplier #{supplier_id}',
        lines,
        reference
    )

def get_journal_entries(start_date=None, end_date=None):
    """Get journal entries with optional date filter"""
    with get_connection() as conn:
        cursor = conn.cursor()
        query = '''
            SELECT je.*,
                   GROUP_CONCAT(a.name || ':D' || jl.debit || ':C' || jl.credit, '|') as lines
            FROM journal_entries je
            JOIN journal_lines jl ON je.id = jl.entry_id
            JOIN accounts a ON jl.account_id = a.id
        '''
        params = []
        if start_date and end_date:
            query += ' WHERE je.entry_date BETWEEN ? AND ?'
            params = [start_date, end_date]
        query += ' GROUP BY je.id ORDER BY je.entry_date DESC, je.id DESC'
        cursor.execute(query, params)
        return cursor.fetchall()

def get_trial_balance():
    """Get trial balance report"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT code, name, account_type, balance FROM accounts
            WHERE balance != 0
            ORDER BY code
        ''')
        return cursor.fetchall()

def get_income_statement(start_date=None, end_date=None):
    """Get income statement"""
    with get_connection() as conn:
        cursor = conn.cursor()

        # Revenue
        cursor.execute('''
            SELECT SUM(balance) FROM accounts WHERE account_type = 'revenue'
        ''')
        revenue = cursor.fetchone()[0] or 0

        # Expenses
        cursor.execute('''
            SELECT SUM(balance) FROM accounts WHERE account_type = 'expense'
        ''')
        expenses = cursor.fetchone()[0] or 0

        return {
            'revenue': revenue,
            'expenses': expenses,
            'net_income': revenue - expenses
        }

def get_balance_sheet():
    """Get balance sheet"""
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute('SELECT SUM(balance) FROM accounts WHERE account_type = "asset"')
        assets = cursor.fetchone()[0] or 0

        cursor.execute('SELECT SUM(balance) FROM accounts WHERE account_type = "liability"')
        liabilities = cursor.fetchone()[0] or 0

        cursor.execute('SELECT SUM(balance) FROM accounts WHERE account_type = "equity"')
        equity = cursor.fetchone()[0] or 0

        income = get_income_statement()

        return {
            'assets': assets,
            'liabilities': liabilities,
            'equity': equity + income['net_income'],
            'total_liab_equity': liabilities + equity + income['net_income']
        }
