#!/usr/bin/env python3
"""
Odoo MCP Server for AI Employee
Connects to Odoo 19+ via JSON-RPC API for accounting integration
"""

import sys
import os
import json
from pathlib import Path
from typing import Any, Optional

# MCP imports
from mcp.server.fastmcp import FastMCP

# Odoo RPC imports
import odoorpc

# =============================================================================
# CONFIGURATION
# =============================================================================

# File locations
SCRIPT_DIR = Path(__file__).parent.parent
ENV_FILE = SCRIPT_DIR / '.env'


def _load_env_file():
    """Load environment variables from .env file if not already set."""
    if ENV_FILE.exists():
        with open(ENV_FILE) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    if key.strip() not in os.environ:
                        os.environ[key.strip()] = value.strip()


# Load .env file at module import
_load_env_file()


def print_status(message: str, emoji: str = "✅"):
    """Print status message to stderr (safe for MCP stdio transport)."""
    print(f"{emoji} {message}", file=sys.stderr, flush=True)


# =============================================================================
# ODOO CONNECTION
# =============================================================================

def get_odoo_connection():
    """
    Establish connection to Odoo via JSON-RPC.

    Returns:
        odoorpc.ODOO connection object
    """
    url = os.getenv("ODOO_URL", "http://localhost:8069")
    db = os.getenv("ODOO_DB", "odoo")
    user = os.getenv("ODOO_USER", "admin")
    password = os.getenv("ODOO_PASSWORD", "admin")

    try:
        # Parse URL to get hostname (odoorpc needs hostname, not full URL)
        # Remove http:// or https:// prefix
        hostname = url.replace("http://", "").replace("https://", "")
        # Remove port if present (odoorpc uses separate port parameter)
        hostname = hostname.split(":")[0] if ":" in hostname else hostname

        odoo = odoorpc.ODOO(hostname, port=8069, protocol='jsonrpc')
        odoo.login(db, user, password)
        print_status(f"Connected to Odoo at {url} as {user}", "🔗")
        return odoo
    except Exception as e:
        print_status(f"Failed to connect to Odoo: {e}", "❌")
        raise


# =============================================================================
# MCP SERVER
# =============================================================================

# Initialize FastMCP server
mcp = FastMCP(
    "odoo",
    instructions="Odoo accounting integration: read invoices, payments, revenue; create draft invoices; post approved invoices"
)


# =============================================================================
# MCP TOOLS
# =============================================================================

@mcp.tool()
async def get_invoices(limit: int = 10, state: str = "") -> str:
    """Fetch recent invoices from Odoo.

    Args:
        limit: Maximum number of invoices to return (default: 10)
        state: Filter by state - empty for all, 'draft', 'posted', 'paid'

    Returns:
        List of invoices with details
    """
    print_status(f"Fetching invoices (limit={limit}, state={state})...", "📋")

    try:
        odoo = get_odoo_connection()
        Invoice = odoo.env['account.move']

        # Build domain for search
        domain = [('move_type', '=', 'out_invoice')]  # Customer invoices
        if state:
            domain.append(('state', '=', state))

        # Search for invoices
        invoice_ids = Invoice.search(domain, limit=limit)

        # Read invoice data
        invoices = Invoice.read(invoice_ids, [
            'name', 'partner_id', 'amount_total',
            'invoice_date', 'state', 'payment_state'
        ])

        result = f"Found {len(invoices)} invoice(s):\n\n"
        for inv in invoices:
            partner_name = inv.get('partner_id', [False, ''])[1] if isinstance(inv.get('partner_id'), list) else 'Unknown'
            result += f"""
- {inv['name']}
  Customer: {partner_name}
  Amount: ${inv.get('amount_total', 0):.2f}
  Date: {inv.get('invoice_date', 'N/A')}
  State: {inv.get('state', 'unknown')}
  Payment: {inv.get('payment_state', 'unknown')}
"""

        odoo.logout()
        return result

    except Exception as e:
        error_msg = f"Error fetching invoices: {type(e).__name__}: {e}"
        print_status(error_msg, "❌")
        return error_msg


@mcp.tool()
async def get_revenue(days: int = 30) -> str:
    """Get total revenue for a period.

    Args:
        days: Number of days to look back (default: 30)

    Returns:
        Revenue summary with total and breakdown
    """
    print_status(f"Calculating revenue for last {days} days...", "💰")

    try:
        odoo = get_odoo_connection()
        Invoice = odoo.env['account.move']

        from datetime import datetime, timedelta
        date_from = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

        # Search for posted/paid invoices in date range
        invoice_ids = Invoice.search([
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'posted'),
            ('invoice_date', '>=', date_from)
        ])

        invoices = Invoice.read(invoice_ids, ['name', 'amount_total', 'invoice_date', 'partner_id'])

        total_revenue = sum(inv.get('amount_total', 0) for inv in invoices)

        result = f"""Revenue Summary (Last {days} days)
{'=' * 40}
Total Revenue: ${total_revenue:.2f}
Invoice Count: {len(invoices)}
Period: {date_from} to {datetime.now().strftime('%Y-%m-%d')}

Recent Invoices:
"""
        for inv in invoices[-10:]:  # Last 10
            partner_name = inv.get('partner_id', [False, ''])[1] if isinstance(inv.get('partner_id'), list) else 'Unknown'
            result += f"\n- {inv['name']}: ${inv.get('amount_total', 0):.2f} ({partner_name})"

        odoo.logout()
        return result

    except Exception as e:
        error_msg = f"Error calculating revenue: {type(e).__name__}: {e}"
        print_status(error_msg, "❌")
        return error_msg


@mcp.tool()
async def get_expenses(days: int = 30) -> str:
    """Get total vendor bills/expenses for a period.

    Args:
        days: Number of days to look back (default: 30)

    Returns:
        Expense summary with total and breakdown
    """
    print_status(f"Calculating expenses for last {days} days...", "💸")

    try:
        odoo = get_odoo_connection()
        Invoice = odoo.env['account.move']

        from datetime import datetime, timedelta
        date_from = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

        # Search for vendor bills in date range
        bill_ids = Invoice.search([
            ('move_type', '=', 'in_invoice'),
            ('state', '=', 'posted'),
            ('invoice_date', '>=', date_from)
        ])

        bills = Invoice.read(bill_ids, ['name', 'amount_total', 'invoice_date', 'partner_id'])

        total_expenses = sum(bill.get('amount_total', 0) for bill in bills)

        result = f"""Expense Summary (Last {days} days)
{'=' * 40}
Total Expenses: ${total_expenses:.2f}
Bill Count: {len(bills)}
Period: {date_from} to {datetime.now().strftime('%Y-%m-%d')}

Recent Bills:
"""
        for bill in bills[-10:]:
            partner_name = bill.get('partner_id', [False, ''])[1] if isinstance(bill.get('partner_id'), list) else 'Unknown'
            result += f"\n- {bill['name']}: ${bill.get('amount_total', 0):.2f} ({partner_name})"

        odoo.logout()
        return result

    except Exception as e:
        error_msg = f"Error calculating expenses: {type(e).__name__}: {e}"
        print_status(error_msg, "❌")
        return error_msg


@mcp.tool()
async def get_payments(limit: int = 20, payment_type: str = "") -> str:
    """Fetch payment records from Odoo.

    Args:
        limit: Maximum number of payments to return (default: 20)
        payment_type: Filter by type - empty for all, 'inbound' (received), 'outbound' (sent)

    Returns:
        List of payments with amount, date, state, journal, and linked invoice
    """
    print_status(f"Fetching payments (limit={limit}, type={payment_type})...", "💳")

    try:
        odoo = get_odoo_connection()
        Payment = odoo.env['account.payment']

        # Build domain for search
        domain = []
        if payment_type == "inbound":
            domain.append(('payment_type', '=', 'receive'))
        elif payment_type == "outbound":
            domain.append(('payment_type', '=', 'send'))

        # Search for payments
        payment_ids = Payment.search(domain, order='date desc', limit=limit)

        # Read payment data
        payments = Payment.read(payment_ids, [
            'name', 'amount', 'payment_type', 'state',
            'date', 'journal_id', 'partner_id',
            'reconciled_invoice_ids'
        ])

        result = f"Found {len(payments)} payment(s):\n\n"

        total_inbound = 0.0
        total_outbound = 0.0

        for p in payments:
            ptype = p.get('payment_type', 'unknown')
            ptype_label = "↗️ Inbound" if ptype == 'receive' else "↘️ Outbound" if ptype == 'send' else ptype

            partner_name = p.get('partner_id', [False, ''])[1] if isinstance(p.get('partner_id'), list) else 'Unknown'
            journal_name = p.get('journal_id', [False, ''])[1] if isinstance(p.get('journal_id'), list) else 'Unknown'

            # Track totals
            if ptype == 'receive':
                total_inbound += p.get('amount', 0)
            elif ptype == 'send':
                total_outbound += p.get('amount', 0)

            result += f"""
- {p['name']}
  Type: {ptype_label}
  Amount: ${p.get('amount', 0):.2f}
  Date: {p.get('date', 'N/A')}
  State: {p.get('state', 'unknown')}
  Method: {journal_name}
  From/To: {partner_name}
"""

            # Show linked invoices if any
            invoice_ids = p.get('reconciled_invoice_ids', [])
            if invoice_ids and isinstance(invoice_ids, list) and len(invoice_ids) > 0:
                result += f"  Applied to: {len(invoice_ids)} invoice(s)\n"

        result += f"""
{'=' * 40}
Summary:
  Total Inbound: ${total_inbound:.2f}
  Total Outbound: ${total_outbound:.2f}
  Net Cash Flow: ${total_inbound - total_outbound:.2f}
"""

        odoo.logout()
        return result

    except Exception as e:
        error_msg = f"Error fetching payments: {type(e).__name__}: {e}"
        print_status(error_msg, "❌")
        return error_msg


@mcp.tool()
async def create_draft_invoice(partner_name: str, amount: float, description: str) -> str:
    """Create a draft invoice in Odoo (state: draft, not posted).

    Args:
        partner_name: Customer name
        amount: Invoice amount
        description: Line item description

    Returns:
        JSON string with invoice details (invoice_id, name, amount, customer, state, url)
    """
    print_status(f"Creating draft invoice for {partner_name}: ${amount}", "📝")

    try:
        odoo = get_odoo_connection()
        Partner = odoo.env['res.partner']
        Invoice = odoo.env['account.move']

        # Find or create partner
        partner_ids = Partner.search([('name', 'ilike', partner_name)], limit=1)

        if not partner_ids:
            # Create new partner
            partner_id = Partner.create({'name': partner_name})
            print_status(f"Created new partner: {partner_name}", "👤")
        else:
            partner_id = partner_ids[0]

        # Create draft invoice
        invoice_id = Invoice.create({
            'move_type': 'out_invoice',
            'partner_id': partner_id,
            'invoice_line_ids': [(0, 0, {
                'name': description,
                'quantity': 1,
                'price_unit': amount,
            })]
        })

        invoice = Invoice.read(invoice_id, ['name', 'state', 'amount_total'])[0]

        odoo.logout()

        # Return structured JSON for easy parsing by skills
        result = {
            "invoice_id": invoice_id,
            "name": invoice['name'],  # Will be False for drafts
            "amount": invoice['amount_total'],
            "customer": partner_name,
            "state": invoice['state'],
            "url": f"http://localhost:8069/web#id={invoice_id}&model=account.move"
        }
        return json.dumps(result, indent=2)

    except Exception as e:
        error_msg = f"Error creating draft invoice: {type(e).__name__}: {e}"
        print_status(error_msg, "❌")
        return error_msg


@mcp.tool()
async def post_invoice(invoice_name: Optional[str] = None, invoice_id: Optional[int] = None) -> str:
    """Post a draft invoice (REQUIRES HUMAN APPROVAL).

    Args:
        invoice_name: Invoice name/number (e.g., "INV/2026/0001") - optional if invoice_id provided
        invoice_id: Direct Odoo invoice ID - optional if invoice_name provided

    Returns:
        Confirmation of posted invoice

    Note: At least one of invoice_name or invoice_id must be provided.
          For draft invoices, use invoice_id as names are not assigned yet.
    """
    # Validate inputs
    if not invoice_name and not invoice_id:
        return "Error: Either invoice_name or invoice_id must be provided"

    identifier = f"ID: {invoice_id}" if invoice_id else f"Name: {invoice_name}"
    print_status(f"Posting invoice ({identifier})", "✅")

    try:
        odoo = get_odoo_connection()
        Invoice = odoo.env['account.move']

        # Find invoice by ID or name
        if invoice_id:
            # Direct ID lookup (works for drafts without names)
            invoice_ids = [invoice_id]
        else:
            # Search by name (works for posted invoices)
            invoice_ids = Invoice.search([('name', '=', invoice_name)])

        if not invoice_ids:
            odoo.logout()
            return f"Error: Invoice not found ({identifier})"

        target_id = invoice_ids[0]
        invoice = Invoice.read(target_id, ['name', 'state', 'amount_total'])[0]

        # Check if already posted
        if invoice['state'] != 'draft':
            odoo.logout()
            return f"Invoice {invoice['name'] or target_id} is already posted (state: {invoice['state']})"

        # Post the invoice
        Invoice.action_post([target_id])

        # Read again to get the posted name
        posted_invoice = Invoice.read(target_id, ['name', 'state'])[0]
        final_name = posted_invoice['name']

        odoo.logout()

        result = f"""Invoice Posted Successfully ✅
{'=' * 40}
Invoice: {final_name}
Amount: ${invoice['amount_total']:.2f}
State: posted

The invoice is now confirmed and ready for payment.
"""
        return result

    except Exception as e:
        error_msg = f"Error posting invoice: {type(e).__name__}: {e}"
        print_status(error_msg, "❌")
        return error_msg


@mcp.tool()
async def get_partners(limit: int = 20) -> str:
    """Get list of customers/vendors (partners) from Odoo.

    Args:
        limit: Maximum number of partners to return

    Returns:
        List of partners with email and phone
    """
    print_status(f"Fetching partners...", "👥")

    try:
        odoo = get_odoo_connection()
        Partner = odoo.env['res.partner']

        partner_ids = Partner.search([('is_company', '=', True)], limit=limit)
        partners = Partner.read(partner_ids, ['name', 'email', 'phone'])

        result = f"Partners (Companies):\n\n"

        for p in partners:
            result += f"- {p['name']}\n"
            if p.get('email'):
                result += f"  Email: {p['email']}\n"
            if p.get('phone'):
                result += f"  Phone: {p['phone']}\n"
            result += "\n"

        odoo.logout()
        return result

    except Exception as e:
        error_msg = f"Error fetching partners: {type(e).__name__}: {e}"
        print_status(error_msg, "❌")
        return error_msg


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

def main():
    """Run the Odoo MCP server."""
    print_status("", "")
    print_status("╔════════════════════════════════════════════════════════╗", "📊")
    print_status("║         Odoo MCP Server for AI Employee                 ║", "🤖")
    print_status("╚════════════════════════════════════════════════════════╝", "📊")
    print_status("", "")

    # Verify configuration
    url = os.getenv("ODOO_URL", "http://localhost:8069")
    db = os.getenv("ODOO_DB", "odoo")
    user = os.getenv("ODOO_USER", "")

    print_status(f"Configuration:", "⚙️")
    print_status(f"  URL: {url}", "  ")
    print_status(f"  Database: {db}", "  ")
    print_status(f"  User: {user}", "  ")
    print_status("", "")

    print_status("Starting MCP server...", "🚀")
    print_status("Tools available: get_invoices, get_revenue, get_expenses, get_payments, create_draft_invoice, post_invoice, get_partners", "🛠️")
    print_status("", "")
    print_status("Server is running. Press Ctrl+C to stop.", "⏳")
    print_status("", "")

    try:
        mcp.run(transport="stdio")

    except KeyboardInterrupt:
        print_status("", "")
        print_status("Odoo MCP Server stopped by user", "👋")
    except Exception as e:
        print_status("", "")
        print_status(f"Fatal error: {e}", "❌")
        raise


if __name__ == "__main__":
    main()
