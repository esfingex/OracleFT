import asyncio
import logging
import sys
from pathlib import Path
from core import OCIWorker, notifier

# Configure logging with unbuffered file and console handlers
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s:%(levelname)s:%(name)s:%(message)s',
    handlers=[
        logging.FileHandler("logs/launch_instance.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("OracleFT")

async def main(dry_run: bool = False):
    sentinel = Path(".instance_created")
    if sentinel.exists() and not dry_run:
        logging.info("Instance already created (sentinel file exists). Exiting.")
        return

    worker = OCIWorker()
    try:
        instance = await worker.launch(dry_run=dry_run)
        if instance and not dry_run:
            sentinel.touch()
            details = {
                "Display Name": getattr(instance, 'display_name', 'N/A'),
                "AD": getattr(instance, 'availability_domain', 'N/A'),
                "Shape": getattr(instance, 'shape', 'N/A'),
                "ID": getattr(instance, 'id', 'N/A')
            }
            await notifier.send_notification(
                "OCI Instance Created Successfully!",
                "Your new Oracle Cloud instance is now being provisioned and will be ready shortly.",
                status="success",
                details=details
            )
    except Exception as e:
        logging.error("Main execution failed: %s", e)
        await notifier.send_notification(
            "OCI Instance Creation Failed",
            f"The script encountered an error while trying to create your instance: {e}",
            status="error"
        )
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
