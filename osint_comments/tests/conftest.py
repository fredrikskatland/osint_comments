# tests/conftest.py
import logging
from rich.logging import RichHandler

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="[%X]",
    handlers=[RichHandler()]
)
