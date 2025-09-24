from celery import Celery
from app.config import Config
from app import create_app
import os

def make_celery(app):
    celery_app = Celery(
        'plagcheck_worker',
        broker=Config.CELERY_BROKER_URL,
        backend=Config.CELERY_RESULT_BACKEND
    )

    celery_app.conf.update(
        task_serializer=Config.CELERY_RESULT_SERIALIZER,
        accept_content=Config.CELERY_ACCEPT_CONTENT,
        result_serializer=Config.CELERY_RESULT_SERIALIZER,
        timezone=Config.CELERY_TIMEZONE,
        enable_utc=True
    )

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery


flask_app = create_app()
celery = make_celery(flask_app)