import logging
import sys

from colorama import Fore, Style
from discord.ext.prometheus import PrometheusLoggingHandler


class PackageLoggingFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        return (
            record.name.startswith("pokeguess")
            or record.name
            in [
                # "discord",
                # "discord.http",
            ]
        )


class CustomLoggingFormatter(logging.Formatter):
    def __init__(self):
        super().__init__(datefmt="%Y-%m-%d %H:%M:%S")

    def format(self, record: logging.LogRecord) -> str:
        time_color = Fore.BLACK + Style.BRIGHT
        name_color = Fore.BLACK + Style.BRIGHT
        level_color = {
            logging.ERROR: Fore.RED,
            logging.WARNING: Fore.YELLOW,
            logging.INFO: Fore.GREEN,
            logging.DEBUG: Fore.BLUE,
            logging.CRITICAL: Fore.MAGENTA + Style.BRIGHT,
        }.get(record.levelno, "")

        timestamp = self.formatTime(record, self.datefmt)

        record_name = record.name.removeprefix("pokeguess.")

        return (
            f"{time_color}{timestamp}{Style.RESET_ALL} "
            f"{level_color}{record.levelname:<7}{Style.RESET_ALL} "
            f"{name_color}{record_name:<20}{Style.RESET_ALL} "
            f"{record.getMessage()} "
        )


def prepare_logger():
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    root.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(CustomLoggingFormatter())
    handler.addFilter(PackageLoggingFilter())

    root.addHandler(handler)
    root.addHandler(PrometheusLoggingHandler())
