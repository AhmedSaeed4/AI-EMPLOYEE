#!/usr/bin/env python3
"""
Deduplication API Server

Runs on Cloud VM, provides real-time coordination between Local and Cloud watchers.
Prevents both watchers from processing the same email.

Endpoints:
- POST /register - Register a processed email ID
- GET /check?id=xxx - Check if email ID has been processed
- GET /health - Health check

Usage:
    python cloud/api_server.py

Or with PM2:
    pm2 start cloud/api_server.py --name ai-employee-api
"""

import os
import sqlite3
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

from flask import Flask, request, jsonify

# =============================================================================
# CONFIGURATION
# =============================================================================

# Get the scripts directory
SCRIPTS_DIR = Path(__file__).parent.parent
CLOUD_DATA_DIR = SCRIPTS_DIR / "cloud_data"
DB_PATH = CLOUD_DATA_DIR / "processed_emails.db"

# API key for authentication (set via environment variable)
API_KEY = os.environ.get('DEDUP_API_KEY', None)

# =============================================================================
# LOGGING SETUP
# =============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [API] - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('dedup_api')

# =============================================================================
# DATABASE
# =============================================================================

def init_db():
    """Initialize SQLite database."""
    CLOUD_DATA_DIR.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute('''
        CREATE TABLE IF NOT EXISTS processed_emails (
            email_id TEXT PRIMARY KEY,
            source TEXT NOT NULL,
            processed_at TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create index for faster lookups
    c.execute('''
        CREATE INDEX IF NOT EXISTS idx_email_id
        ON processed_emails(email_id)
    ''')

    conn.commit()
    conn.close()

    logger.info(f"Database initialized at {DB_PATH}")


def get_db_connection():
    """Get database connection with row factory."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# =============================================================================
# FLASK APP
# =============================================================================

app = Flask(__name__)


def check_api_key() -> Optional[Dict[str, Any]]:
    """Check API key if configured. Returns error dict if invalid."""
    if API_KEY:
        provided_key = request.headers.get('X-API-Key')
        if provided_key != API_KEY:
            return {"error": "Unauthorized", "message": "Invalid API key"}
    return None


@app.before_request
def before_request():
    """Check API key before processing request."""
    # Skip health check from auth
    if request.path == '/health':
        return None

    error = check_api_key()
    if error:
        return jsonify(error), 401

    return None


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({
        "status": "ok",
        "service": "dedup-api",
        "database": str(DB_PATH),
        "timestamp": datetime.now().isoformat()
    })


@app.route('/register', methods=['POST'])
def register():
    """
    Register a processed email ID.

    Request body:
        {
            "email_id": "message_id_here",
            "source": "local" or "cloud"
        }

    Returns:
        {
            "success": true,
            "email_id": "message_id_here",
            "source": "local"
        }
    """
    data = request.get_json()

    if not data:
        return jsonify({"error": "Invalid request", "message": "JSON body required"}), 400

    email_id = data.get('email_id')
    source = data.get('source', 'unknown')

    if not email_id:
        return jsonify({"error": "Invalid request", "message": "email_id required"}), 400

    try:
        conn = get_db_connection()
        c = conn.cursor()

        # Check if already exists
        c.execute('SELECT source, processed_at FROM processed_emails WHERE email_id = ?', (email_id,))
        existing = c.fetchone()

        if existing:
            conn.close()
            logger.info(f"Email {email_id} already registered by {existing['source']}")
            return jsonify({
                "success": True,
                "email_id": email_id,
                "source": existing['source'],
                "processed_at": existing['processed_at'],
                "already_exists": True
            })

        # Insert new record
        processed_at = data.get('processed_at', datetime.now().isoformat())
        c.execute(
            'INSERT INTO processed_emails (email_id, source, processed_at) VALUES (?, ?, ?)',
            (email_id, source, processed_at)
        )
        conn.commit()
        conn.close()

        logger.info(f"Registered email {email_id} from {source}")
        return jsonify({
            "success": True,
            "email_id": email_id,
            "source": source,
            "processed_at": processed_at
        })

    except sqlite3.Error as e:
        logger.error(f"Database error: {e}")
        return jsonify({"error": "Database error", "message": str(e)}), 500


@app.route('/check', methods=['GET'])
def check():
    """
    Check if an email ID has been processed.

    Query params:
        id - The email message ID to check

    Returns:
        {
            "processed": true/false,
            "source": "local" or "cloud",
            "processed_at": "ISO timestamp"
        }
    """
    email_id = request.args.get('id')

    if not email_id:
        return jsonify({"error": "Invalid request", "message": "id parameter required"}), 400

    try:
        conn = get_db_connection()
        c = conn.cursor()

        c.execute('SELECT source, processed_at FROM processed_emails WHERE email_id = ?', (email_id,))
        row = c.fetchone()
        conn.close()

        if row:
            return jsonify({
                "processed": True,
                "email_id": email_id,
                "source": row['source'],
                "processed_at": row['processed_at']
            })
        else:
            return jsonify({
                "processed": False,
                "email_id": email_id
            })

    except sqlite3.Error as e:
        logger.error(f"Database error: {e}")
        return jsonify({"error": "Database error", "message": str(e)}), 500


@app.route('/stats', methods=['GET'])
def stats():
    """Get statistics about processed emails."""
    try:
        conn = get_db_connection()
        c = conn.cursor()

        # Total count
        c.execute('SELECT COUNT(*) as total FROM processed_emails')
        total = c.fetchone()['total']

        # Count by source
        c.execute('SELECT source, COUNT(*) as count FROM processed_emails GROUP BY source')
        by_source = {row['source']: row['count'] for row in c.fetchall()}

        # Recent (last 24 hours)
        yesterday = datetime.now().replace(hour=0, minute=0, second=0).isoformat()
        c.execute('SELECT COUNT(*) as recent FROM processed_emails WHERE processed_at >= ?', (yesterday,))
        recent = c.fetchone()['recent']

        conn.close()

        return jsonify({
            "total": total,
            "by_source": by_source,
            "recent_24h": recent
        })

    except sqlite3.Error as e:
        logger.error(f"Database error: {e}")
        return jsonify({"error": "Database error", "message": str(e)}), 500


@app.route('/list', methods=['GET'])
def list_processed():
    """List recent processed emails (for debugging)."""
    limit = request.args.get('limit', 50, type=int)
    limit = min(limit, 100)  # Cap at 100

    try:
        conn = get_db_connection()
        c = conn.cursor()

        c.execute('''
            SELECT email_id, source, processed_at
            FROM processed_emails
            ORDER BY processed_at DESC
            LIMIT ?
        ''', (limit,))

        rows = c.fetchall()
        conn.close()

        return jsonify({
            "count": len(rows),
            "emails": [
                {
                    "email_id": row['email_id'],
                    "source": row['source'],
                    "processed_at": row['processed_at']
                }
                for row in rows
            ]
        })

    except sqlite3.Error as e:
        logger.error(f"Database error: {e}")
        return jsonify({"error": "Database error", "message": str(e)}), 500


# =============================================================================
# MAIN
# =============================================================================

if __name__ == '__main__':
    # Initialize database
    init_db()

    # Get port from environment or default to 5000
    port = int(os.environ.get('DEDUP_API_PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'

    logger.info(f"Starting Dedup API on port {port}")
    logger.info(f"Database: {DB_PATH}")
    logger.info(f"API Key required: {'Yes' if API_KEY else 'No'}")

    app.run(host='0.0.0.0', port=port, debug=debug)