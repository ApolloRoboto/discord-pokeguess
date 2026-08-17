from pathlib import Path
from pkgutil import iter_modules
from importlib import import_module
import inspect
import logging
from discord.ext.commands import Bot

log = logging.getLogger(__name__)


async def add_cogs(bot: Bot):
    """
    Function to dynamically load all controller class to the bot.

    Controllers needs to be directly under the controller package, have a
    module and a class that ends with `Controller`.
    """

    # Get this init file's package directory
    package_dir = Path(__file__).resolve().parent

    for _, module_name, _ in iter_modules([str(package_dir)]):
        # filter out modules that does not ends with `Controller``
        if not module_name.endswith("_controller"):
            continue

        # Import the module
        module = import_module(f"{__name__}.{module_name}")

        # Find the class that ends with `Controller`
        for key, value in module.__dict__.items():
            if key.endswith("Controller") and inspect.isclass(value):
                # Add controller to the bot
                log.info(f"Loading controller {value.__name__}")
                await bot.add_cog(value(bot))
