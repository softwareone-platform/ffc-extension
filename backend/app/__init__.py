from importlib.metadata import PackageNotFoundError, version

from app.conf import Settings

settings = Settings()

try:
    __version__ = version("ffc-extension")
except PackageNotFoundError:  # pragma: no cover
    __version__ = "0.0.0.dev0"
