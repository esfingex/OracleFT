import asyncio
import logging
from main import main

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s:%(levelname)s:%(name)s:%(message)s',
        handlers=[
            logging.FileHandler("logs/launch_instance.log"),
            logging.StreamHandler()
        ]
    )
    # Run in dry_run mode
    asyncio.run(main(dry_run=True))
