from flask import Flask
from flask_restful import Api
from .extensions import db
from .config import Config
from flask_cors import CORS
import logging
from .services.database_service import DatabaseService
from .extensions import make_celery



def create_app():
    # Configure logging first
    Config.configure_logging()
    
    app = Flask(__name__)
    app.config.from_object(Config)
    app.config["CELERY"] = {
        'broker_url': Config.CELERY_BROKER_URL,
        'result_backend': Config.CELERY_RESULT_BACKEND,
        'accept_content': Config.CELERY_ACCEPT_CONTENT,
        'task_serializer': Config.CELERY_TASK_SERIALIZER,
        'result_serializer': Config.CELERY_RESULT_SERIALIZER,
        'timezone': Config.CELERY_TIMEZONE,
        'enable_utc': True,
        'include': ['app.worker.tasks']
    }
    CORS(app, resources={r"/*": {"origins": "*"}})

    make_celery(app)

    # Initialize database
    db.init_app(app)

    # Import routes after db initialization to avoid circular imports
    from .api.routes import initialize_routes
    
    api = Api(app)

    initialize_routes(api)
    DatabaseService(db)

    # Create database tables
    with app.app_context():
        # Import models here to register them with SQLAlchemy
        from .models.document import Document
        from .models.scan_result import ScanResult
        from .models.scan_resource import ScanResource
        from .models.scan_status import ScanStatus
        from .models.user import User
        
        db.create_all()

    # Log application startup
    logger = logging.getLogger(__name__)
    logger.info("PlagCheck application started successfully")
    logger.info(f"Database connected to: {app.config['SQLALCHEMY_DATABASE_URI']}")

    return app
