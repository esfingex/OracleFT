import logging
import oci
import paramiko
import itertools
import asyncio
import time
from pathlib import Path
from .config import config

class OCIWorker:
    ARM_SHAPE = "VM.Standard.A1.Flex"
    E2_MICRO_SHAPE = "VM.Standard.E2.1.Micro"

    def __init__(self):
        self._setup_logging()
        self._load_oci_clients()

    def _setup_logging(self):
        # Already set up in manager or globally, but ensuring local logger
        self.launch_logger = logging.getLogger("launch_instance")

    def _load_oci_clients(self):
        oci_config_path = config.get("OCI_CONFIG", "~/.oci/config")
        oci_config = oci.config.from_file(oci_config_path)
        self.iam_client = oci.identity.IdentityClient(oci_config)
        self.network_client = oci.core.VirtualNetworkClient(oci_config)
        self.compute_client = oci.core.ComputeClient(oci_config)
        self.user_id = oci_config.get('user')

    async def _execute_oci(self, client, method: str, *args, **kwargs):
        """Wraps blocking OCI SDK calls in a thread for async compatibility."""
        retry_count = 0
        while True:
            try:
                # Run the blocking SDK call in a separate thread
                fn = getattr(client, method)
                response = await asyncio.to_thread(fn, *args, **kwargs)
                return response.data if hasattr(response, "data") else response
            except oci.exceptions.ServiceError as srv_err:
                data = {"status": srv_err.status, "code": srv_err.code, "message": srv_err.message}
                if await self._handle_errors(method, data, retry_count):
                    retry_count += 1
                    continue
                raise Exception(f"OCI Service Error: {data}")

    async def _handle_errors(self, command: str, data: dict, retry_count: int = 0) -> bool:
        base_wait = int(config.get("REQUEST_WAIT_TIME_SECS", "60"))
        wait_time = min(3600, base_wait * (2 ** retry_count))
        
        should_retry = False
        if "code" in data:
            if data["code"] in ("TooManyRequests", "Out of host capacity.", "InternalError", "NotAuthorizedOrNotFound") or \
               data.get("message") in ("Out of host capacity.", "Bad Gateway"):
                should_retry = True
        elif data.get("status") in (500, 502, 503, 504):
            should_retry = True

        if should_retry:
            self.launch_logger.info("Command: %s -- Output: %s. Retry %s in %ss", 
                                     command, data.get("code") or data.get("status"), retry_count + 1, wait_time)
            await asyncio.sleep(wait_time)
            return True
        return False

    def _generate_ssh_key_pair(self, public_key_file: Path, private_key_file: Path):
        key = paramiko.RSAKey.generate(2048)
        private_key_file.parent.mkdir(parents=True, exist_ok=True)
        key.write_private_key_file(str(private_key_file))
        private_key_file.chmod(0o600)
        
        public_key_file.write_text(f"ssh-rsa {key.get_base64()} oracle_auto_generated")

    def _get_or_create_ssh_key(self) -> str:
        pub_path = Path(config.get("SSH_AUTHORIZED_KEYS_FILE", "id_rsa.pub"))
        if not pub_path.exists():
            priv_path = pub_path.with_name(f"{pub_path.stem}_private")
            self._generate_ssh_key_pair(pub_path, priv_path)
        return pub_path.read_text().strip()

    async def _prepare_context(self):
        """Gathers all necessary IDs for launch."""
        user_info = await self._execute_oci(self.iam_client, "get_user", self.user_id)
        tenancy_id = user_info.compartment_id

        # ADs
        ads = await self._execute_oci(self.iam_client, "list_availability_domains", compartment_id=tenancy_id)
        selected_ads = config.get("OCT_FREE_AD", "AD-1").split(",")
        oci_ads = [ad.name for ad in ads if any(ad.name.endswith(s) for s in selected_ads)]
        
        # Subnet
        subnet_id = config.get("OCI_SUBNET_ID")
        if not subnet_id:
            subnets = await self._execute_oci(self.network_client, "list_subnets", compartment_id=tenancy_id)
            subnet_id = subnets[0].id

        # Image
        image_id = config.get("OCI_IMAGE_ID")
        if not image_id:
            os_name = config.get("OPERATING_SYSTEM", "Canonical Ubuntu")
            os_ver = config.get("OS_VERSION", "22.04")
            shape = config.get("OCI_COMPUTE_SHAPE", self.ARM_SHAPE)
            images = await self._execute_oci(self.compute_client, "list_images", compartment_id=tenancy_id, shape=shape)
            image_id = next(img.id for img in images if img.operating_system == os_name and img.operating_system_version == os_ver)

        return {
            "tenancy_id": tenancy_id,
            "ad_cycle": itertools.cycle(oci_ads),
            "subnet_id": subnet_id,
            "image_id": image_id
        }

    async def launch(self, dry_run: bool = False):
        ctx = await self._prepare_context()
        ssh_key = self._get_or_create_ssh_key()
        shape = config.get("OCI_COMPUTE_SHAPE", self.ARM_SHAPE)
        display_name = config.get("DISPLAY_NAME", "OracleFreeInstance")
        public_ip = config.get("ASSIGN_PUBLIC_IP", "false").lower() == "true"
        boot_size = max(50, int(config.get("BOOT_VOLUME_SIZE", "50")))

        # Configurable specs
        ocpus = int(config.get("OCI_ARM_OCPUS", "4")) if shape == self.ARM_SHAPE else 1
        memory = int(config.get("OCI_ARM_MEMORY_GB", "24")) if shape == self.ARM_SHAPE else 1
        shape_config = oci.core.models.LaunchInstanceShapeConfigDetails(ocpus=ocpus, memory_in_gbs=memory)

        if dry_run:
            self.launch_logger.info("🧪 [DRY RUN] Simulating instance launch...")
            await asyncio.sleep(2) # Simulate network delay
            class MockResponse:
                def __init__(self): self.id = "ocid1.instance.oc1.phx.dry_run_mock_id"
                @property
                def display_name(self): return display_name
                @property
                def availability_domain(self): return "MOCK-AD"
                @property
                def shape(self): return shape

            self.launch_logger.info("✅ [DRY RUN] Connection to Oracle Cloud successful! (Simulation)")
            return MockResponse()

        while True:
            try:
                response = await self._execute_oci(
                    self.compute_client, "launch_instance",
                    launch_instance_details=oci.core.models.LaunchInstanceDetails(
                        availability_domain=next(ctx["ad_cycle"]),
                        compartment_id=ctx["tenancy_id"],
                        display_name=display_name,
                        shape=shape,
                        shape_config=shape_config,
                        create_vnic_details=oci.core.models.CreateVnicDetails(
                            assign_public_ip=public_ip,
                            subnet_id=ctx["subnet_id"],
                            display_name=display_name
                        ),
                        source_details=oci.core.models.InstanceSourceViaImageDetails(
                            source_type="image",
                            image_id=ctx["image_id"],
                            boot_volume_size_in_gbs=boot_size
                        ),
                        metadata={"ssh_authorized_keys": ssh_key}
                    )
                )
                self.launch_logger.info("Instance launched successfully: %s", response.id)
                return response
            except Exception as e:
                self.launch_logger.error("Launch attempt failed: %s", e)
                raise
