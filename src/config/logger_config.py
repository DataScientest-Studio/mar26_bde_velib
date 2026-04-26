import logging
import os
from logging.handlers import RotatingFileHandler

def setup_logger(name: str = "app", log_file: str = "logs/app.log") -> logging.Logger:
    """Configure un logger avec sortie console + fichier."""

    # Créer le dossier logs s'il n'existe pas
    os.makedirs(os.path.dirname(log_file), exist_ok=True)

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # Éviter les doublons si appelé plusieurs fois
    if logger.handlers:
        return logger

    # Format des messages
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # 📺 Handler console (INFO et plus)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    # 📁 Handler fichier avec rotation (10 Mo max, 5 fichiers archivés)
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10 Mo
        backupCount=5,
        encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    # 📁 Handler fichier erreurs uniquement
    error_handler = RotatingFileHandler(
        "logs/errors.log",
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8"
    )
    error_handler.setLevel(logging.ERROR)  # ERROR et CRITICAL uniquement
    error_handler.setFormatter(formatter)

    logger.addHandler(error_handler)

    return logger
