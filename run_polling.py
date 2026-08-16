import asyncio
import logging

from src.config import Settings
from src.runtime import run

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    try:
        asyncio.run(run(Settings()))
    except KeyboardInterrupt:
        pass
