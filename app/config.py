import os
import logging
from dotenv import load_dotenv
from urllib.parse import quote_plus
load_dotenv()

class Config:
    SOLR_URL = os.getenv('SOLR_URL', 'http://localhost:8983/solr/solr_core_plagcheck')
    FILE_DIR = os.getenv('FILE_DIR', 'files')
    ORIGINAL_FILE_DIR = os.getenv('ORIGINAL_FILE_DIR', 'original_files')
    EXCEL_SAMPLE_DIR = os.getenv('EXCEL_FILE_UPLOAD_DIR', 'excel_sample')

    # Database configuration
    MYSQL_HOST = os.getenv('MYSQL_HOST', '127.0.0.1')
    MYSQL_PORT = os.getenv('MYSQL_PORT', '3306')
    MYSQL_USER = os.getenv('MYSQL_USER', 'plagcheck')
    MYSQL_PASSWORD = quote_plus(os.getenv('MYSQL_PASSWORD', '123456a@'))
    MYSQL_DATABASE = os.getenv('MYSQL_DATABASE', 'plagcheck_db')


    #MySQL configuration
    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }

    #Connection to APACHE SOLR configuration
    POOL_CONNECTIONS = int(os.getenv('POOL_CONNECTIONS', '20'))
    POOL_MAXSIZE = int(os.getenv('POOL_MAXSIZE', '20'))
    SOLR_TIMEOUT = int(os.getenv('SOLR_TIMEOUT', '60'))
    CONNECTION_KEEP_ALIVE_TIMEOUT = int(os.getenv('KEEP_ALIVE_TIMEOUT', '120'))

    #Config time-out for file processing
    SOLR_EXTRACT_TIMEOUT = int(os.getenv('SOLR_EXTRACT_TIMEOUT', '60'))  # 5 minutes for text extraction

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
