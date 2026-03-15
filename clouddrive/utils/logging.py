import logging
import os
from logging.handlers import RotatingFileHandler
from functools import wraps


def setup_logging(app, log_level=None):
    if log_level is None:
        log_level = os.environ.get('LOG_LEVEL', 'INFO')
    
    level = getattr(logging, log_level.upper(), logging.INFO)
    
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    file_handler = RotatingFileHandler(
        'logs/clouddrive.log',
        maxBytes=10485760,
        backupCount=5
    )
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [%(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(level)
    
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s'
    ))
    console_handler.setLevel(level)
    
    app.logger.addHandler(file_handler)
    app.logger.addHandler(console_handler)
    app.logger.setLevel(level)
    
    return app.logger


def log_request(logger):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            from flask import request
            logger.info(f"REQUEST: {request.method} {request.path} - {request.remote_addr}")
            try:
                result = f(*args, **kwargs)
                logger.info(f"RESPONSE: {request.method} {request.path} - OK")
                return result
            except Exception as e:
                logger.error(f"ERROR: {request.method} {request.path} - {str(e)}")
                raise
        return wrapper
    return decorator
