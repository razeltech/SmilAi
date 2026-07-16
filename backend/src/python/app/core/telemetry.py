import uuid
import json
from datetime import datetime
from sqlite3 import Connection

def log_audit_event(
    db: Connection,
    user_id: str,
    action: str,
    resource: str,
    resource_id: str = None,
    metadata: dict = None,
    ip_address: str = None,
    user_agent: str = None
):
    """
    Safely writes an audit record to the database.
    Does not run commit() to allow embedding inside parent transactions.
    """
    meta_json = json.dumps(metadata) if metadata else None
    db.execute(
        """
        INSERT INTO audit_logs (
            id, user_id, action, resource, resource_id, timestamp, metadata, ip_address, user_agent
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            str(uuid.uuid4()),
            user_id,
            action,
            resource,
            resource_id,
            datetime.utcnow().isoformat(),
            meta_json,
            ip_address,
            user_agent
        )
    )
