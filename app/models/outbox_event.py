from app.extensions import db

class OutboxEvent(db.Model):
    __tablename__ = 'outbox_events'

    id = db.Column(db.BigInteger, primary_key=True)
    aggregate_type = db.Column(db.String(255), nullable=False) # e.g., 'FILE'
    aggregate_id = db.Column(db.BigInteger, nullable=False) # e.g., FILE ID
    event_type = db.Column(db.String(255), nullable=False) # e.g., 'created', 'updated', 'deleted'
    payload = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)
    processed = db.Column(db.Boolean, default=False)
    failed = db.Column(db.Boolean, default=False, nullable=False)
    error_message = db.Column(db.Text, nullable=True)
    retry_count = db.Column(db.Integer, default=0)
    max_retries = db.Column(db.Integer, default=3)

    def to_dict(self):
        return {
            'id': self.id,
            'aggregate_type': self.aggregate_type,
            'aggregate_id': self.aggregate_id,
            'event_type': self.event_type,
            'payload': self.payload,
            'timestamp': self.timestamp.isoformat(),
            'processed': self.processed,
            'failed': self.failed,
            'error_message': self.error_message,
            'retry_count': self.retry_count,
            'max_retries': self.max_retries
        }