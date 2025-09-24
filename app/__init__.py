from flask import Flask
from flask_restful import Api
from .database import db
from .config import Config
from flask_cors import CORS
import logging
from .services.database_service import DatabaseService
from celery import Celery, Task



def celery_init_app(app: Flask) -> Celery:
    class FlaskTask(Task):
        def __call__(self, *args: object, **kwargs: object) -> object:
            with app.app_context():
                return self.run(*args, **kwargs)

    celery_app = Celery(app.name)
    celery_app.config_from_object(app.config["CELERY"])
    celery_app.set_default()
    celery_app.Task = FlaskTask
    app.extensions["celery"] = celery_app
    return celery_app

def create_app():
    # Configure logging first
    Config.configure_logging()
    
    app = Flask(__name__)
    app.config.from_object(Config)
    app.config["CELERY"] = {
        'broker_url': Config.CELERY_BROKER_URL,
        'result_backend': Config.CELERY_RESULT_BACKEND
    }
    CORS(app, resources={r"/*": {"origins": "*"}})

    # Initialize Celery
    celery_init_app(app)


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
