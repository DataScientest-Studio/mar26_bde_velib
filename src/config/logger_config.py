import logging
import os
from datetime import datetime, timedelta


def setup_logger(name: str = "app", log_dir: str = "logs") -> logging.Logger:
    """
    Logger avec rotation quotidienne et purge automatique après 7 jours.
    Fichiers générés : logs/app_2026-04-26.log
    """
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)
    os.makedirs(log_dir, exist_ok=True)

    # ─── Nom du fichier avec la date du jour ──────────────────────
    today = datetime.now().strftime("%Y-%m-%d")
    log_file = os.path.join(log_dir, f"{name}_{today}.log")

    # ─── Format ───────────────────────────────────────────────────
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(levelname)-8s - %(filename)s:%(lineno)d - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # ─── Console (INFO+) ──────────────────────────────────────────
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    # ─── Fichier du jour (DEBUG+) ─────────────────────────────────
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    # ─── Fichier erreurs uniquement (ERROR+) ──────────────────────
    error_file = os.path.join(log_dir, f"{name}_errors_{today}.log")
    error_handler = logging.FileHandler(error_file, encoding="utf-8")
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)

    logger.addHandler(error_handler)


    # ─── Purge automatique des logs > 7 jours ─────────────────────
    _purge_old_logs(log_dir, name, max_days=7)

    #logger.info("Logger démarré → %s", log_file)
    return logger


def _purge_old_logs(log_dir: str, name: str, max_days: int = 7) -> None:
    """Supprime les fichiers logs plus vieux que max_days jours."""

    cutoff = datetime.now() - timedelta(days=max_days)

    for filename in os.listdir(log_dir):
        if not filename.startswith(name) or not filename.endswith(".log"):
            continue

        filepath = os.path.join(log_dir, filename)

        try:
            date_str = filename.replace(f"{name}_", "").replace(".log", "")
            file_date = datetime.strptime(date_str, "%Y-%m-%d")

            if file_date < cutoff:
                os.remove(filepath)
                print(f"🗑️  Log supprimé : {filename}")

        except (ValueError, OSError):
            continue