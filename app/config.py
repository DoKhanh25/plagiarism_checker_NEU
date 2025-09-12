import os
import logging
from dotenv import load_dotenv
from urllib.parse import quote_plus
load_dotenv()

class Config:
    SORL_URL = os.getenv('SORL_URL', 'http://localhost:8983/solr/solr_core_plagcheck')
    FILE_DIR = os.getenv('FILE_DIR', 'files')
    ORIGINAL_FILE_DIR = os.getenv('ORIGINAL_FILE_DIR', 'original_files')
    EXCEL_SAMPLE_DIR = os.getenv('EXCEL_FILE_UPLOAD_DIR', 'excel_sample')
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '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')
    
    # Database configuration
    MYSQL_HOST = os.getenv('MYSQL_HOST', '127.0.0.1')
    MYSQL_PORT = os.getenv('MYSQL_PORT', '3306')
    MYSQL_USER = os.getenv('MYSQL_USER', 'plagcheck')
    MYSQL_PASSWORD = quote_plus(os.getenv('MYSQL_PASSWORD', '123456a@'))
    MYSQL_DATABASE = os.getenv('MYSQL_DATABASE', 'plagcheck_db')
    
    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }
    
    # Logging configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'app.log')
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    @staticmethod
    def configure_logging():
        """Configure logging for the application"""
        logging.basicConfig(
            level=getattr(logging, Config.LOG_LEVEL.upper()),
            format=Config.LOG_FORMAT,
            handlers=[
                logging.FileHandler(Config.LOG_FILE),
                logging.StreamHandler()
            ]
        )
