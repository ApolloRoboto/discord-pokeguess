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

        message = (
            f"{time_color}{timestamp}{Style.RESET_ALL} "
            f"{level_color}{record.levelname:<7}{Style.RESET_ALL} "
            f"{name_color}{record_name:<24}{Style.RESET_ALL} "
            f"{record.getMessage()} "
        )

        if record.exc_info and not record.exc_text:
            record.exc_text = self.formatException(record.exc_info)
        if record.exc_text:
            message += f"\n{Fore.RED}{record.exc_text}{Style.RESET_ALL}"
        if record.stack_info:
            message += (
                f"\n{Fore.RED}{self.formatStack(record.stack_info)}{Style.RESET_ALL}"
            )

        return message


def prepare_logger():
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    root.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(CustomLoggingFormatter())
    handler.addFilter(PackageLoggingFilter())
    root.addHandler(handler)

    handler = PrometheusLoggingHandler()
    handler.addFilter(PackageLoggingFilter())
    root.addHandler(handler)
