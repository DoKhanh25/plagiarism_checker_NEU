from datetime import datetime
from app.extensions import db

class Document(db.Model):
    __tablename__ = 'documents'

    id = db.Column(db.BigInteger, primary_key=True)
    research_name = db.Column(db.String(255), nullable=False)
    file_name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    file_hash = db.Column(db.String(70), unique=True, nullable=False)
    file_path = db.Column(db.String(500))
    mimetype = db.Column(db.String(100))
    file_size = db.Column(db.BigInteger)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    author = db.Column(db.String(100), nullable=True)
    is_enable = db.Column(db.Boolean, default=True)
    is_included_in_solr = db.Column(db.Boolean, default=False)
    # user_uploaded = db.Column(db.BigInteger, db.ForeignKey('users.id'), nullable=False)

    # Relationships
    scan_statuses = db.relationship('ScanStatus', backref='document', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'researchName': self.research_name,
            'fileName': self.file_name,
            'description': self.description,
            'fileHash': self.file_hash,
            'filePath': self.file_path,
            'mimetype': self.mimetype,
            'fileSize': self.file_size,
            'uploadDate': self.upload_date.isoformat() if self.upload_date else None,
            'author': self.author,
            'isEnable': self.is_enable,
            'isIncludedInSolr': self.is_included_in_solr
        }
