from flask_sqlalchemy import SQLAlchemy
from celery import Celery



# Initialize SQLAlchemy instance
db = SQLAlchemy()



# Initialize Celery instance
celery = Celery(__name__)

def make_celery(app):
    celery.conf.update(
        app.config["CELERY"]
    )

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery
