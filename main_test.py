import asyncio
import logging
from main import main

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    # Run in dry_run mode
    asyncio.run(main(dry_run=True))
