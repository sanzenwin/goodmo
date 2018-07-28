import settings
from better_exceptions_common import hook


if settings.BetterExceptions.isOpen:
    hook()
