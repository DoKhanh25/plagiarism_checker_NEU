from datetime import datetime
from ..database import db

class ScanResult(db.Model):
    __tablename__ = 'scan_results'
    
    id = db.Column(db.BigInteger, primary_key=True)
    status_id = db.Column(db.BigInteger, db.ForeignKey('scan_status.id'), nullable=False)

    chars_doctotal = db.Column(db.Integer, default=0)
    chars_scanned = db.Column(db.Integer, default=0)
    chars_copied = db.Column(db.Integer, default=0)
    chars_original = db.Column(db.Integer, default=0)
    chars_original_ratio = db.Column(db.Float, default=0.0)
    
    words_doctotal = db.Column(db.Integer, default=0)
    words_scanned = db.Column(db.Integer, default=0)
    words_copied = db.Column(db.Integer, default=0)
    words_original = db.Column(db.Integer, default=0)
    words_original_ratio = db.Column(db.Float, default=0.0)
    
    samples_scanned = db.Column(db.Integer, default=0)
    samples_copied = db.Column(db.Integer, default=0)
    samples_original = db.Column(db.Integer, default=0)
    samples_original_ratio = db.Column(db.Float, default=0.0)
    
    # Scan parameters
    exp_min = db.Column(db.Integer, default=3)
    exp_max = db.Column(db.Integer, default=5)
    multi_source = db.Column(db.Boolean, default=False)

    # Results
    output_data = db.Column(db.JSON)  # Store the formatted output

    # Relationships
    scan_resources = db.relationship('ScanResource', backref='scan_result', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'status_id': self.status_id,
            'metrics': {
                'chars_doctotal': self.chars_doctotal,
                'chars_scanned': self.chars_scanned,
                'chars_copied': self.chars_copied,
                'chars_original': self.chars_original,
                'chars_original_ratio': self.chars_original_ratio,
                'words_doctotal': self.words_doctotal,
                'words_scanned': self.words_scanned,
                'words_copied': self.words_copied,
                'words_original': self.words_original,
                'words_original_ratio': self.words_original_ratio,
                'samples_scanned': self.samples_scanned,
                'samples_copied': self.samples_copied,
                'samples_original': self.samples_original,
                'samples_original_ratio': self.samples_original_ratio
            },
            'parameters': {
                'exp_min': self.exp_min,
                'exp_max': self.exp_max,
                'multi_source': self.multi_source
            },
            'output_data': self.output_data
        }
