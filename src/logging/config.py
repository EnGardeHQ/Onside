import logging
from logging.handlers import RotatingFileHandler
import os

def setup_logging():
    log_dir = os.path.join(os.getcwd(), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            RotatingFileHandler(
                os.path.join(log_dir, 'onside_content.log'),
                maxBytes=10*1024*1024,
                backupCount=5
            ),
            logging.StreamHandler()
        ]
    )

    return {
        'auth': logging.getLogger('auth'),
        'database': logging.getLogger('database'),
        'api': logging.getLogger('api')
    }
