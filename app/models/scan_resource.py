from ..database import db

class ScanResource(db.Model):
    __tablename__ = 'scan_resources'

    id = db.Column(db.BigInteger, primary_key=True)
    scan_result_id = db.Column(db.BigInteger, db.ForeignKey('scan_results.id'), nullable=False)
    source_id = db.Column(db.String(255), nullable=False)
    color = db.Column(db.String(20), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    words = db.Column(db.Integer, default=0)
    samples = db.Column(db.Integer, default=0)

    def to_dict(self):
        return {
            'id': self.id,
            'scan_result_id': self.scan_result_id,
            'source_id': self.source_id,
            'color': self.color,
            'name': self.name,
            'description': self.description,
            'words': self.words,
            'samples': self.samples
        }