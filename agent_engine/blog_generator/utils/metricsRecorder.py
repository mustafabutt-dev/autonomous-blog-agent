"""
Metrics Recorder for Blog Post Generator Agent
Tracks and reports agent performance metrics
"""
import asyncio
import aiohttp
import json
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any, Literal
import logging
import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from config import settings
logger = logging.getLogger(__name__)


class MetricsRecorder:
    """
    Records and reports metrics for blog post generation agent
    """
    
    GOOGLE_SCRIPT_URL_FOR_TEAM = settings.GOOGLE_SCRIPT_URL_FOR_TEAM
    TOKEN_FOR_TEAM = settings.TOKEN_FOR_TEAM

    GOOGLE_SCRIPT_URL_FOR_PROD = settings.GOOGLE_SCRIPT_URL_FOR_PROD
    TOKEN_FOR_PROD = settings.TOKEN_FOR_PROD
    
    def __init__(
        self, 
        agent_name: str = "Blog Post Generator",
        agent_owner: str = "Muhammad Mustafa",
        job_type: str = "Blog Post Generation",
        run_env: Literal["DEV", "PROD"] = None
    ):
        """
        Initialize metrics recorder
        
        Args:
            agent_name: Name of the agent
            agent_owner: Owner of the agent
            job_type: Type of job being performed
            run_env: Environment (DEV or PROD). Auto-detects if None.
        """
        self.agent_name = agent_name
        self.agent_owner = agent_owner
        self.job_type = job_type
        
        # Auto-detect environment if not specified
        if run_env is None:
            # Check common environment variables
            if os.getenv("CI") or os.getenv("GITHUB_ACTIONS"):
                self.run_env = "PROD"
            elif os.getenv("ENVIRONMENT") == "production":
                self.run_env = "PROD"
            else:
                self.run_env = "DEV"
        else:
            self.run_env = run_env
        
        # Generate unique run ID
        self.run_id = str(uuid.uuid4())
        
        # Metrics counters
        self.items_discovered = 0
        self.items_succeeded = 0
        self.items_failed = 0
        
        # Job context
        self.product = None
        self.platform = None
        self.website = None
        self.website_section = "Blog"
        self.item_name = "Blog Posts"
        
        # Timing (in milliseconds)
        self.start_time_ms = None
        self.end_time_ms = None
        self.run_duration_ms = 0
        
        # Status
        self.status = "running"
        
        # Timestamp
        self.timestamp = None
        
        # Error tracking (for logging, not in payload)
        self.errors = []
    
    def start_job(
        self, 
        product: str, 
        platform: str, 
        website: str
    ):
        """
        Start tracking a new job
        
        Args:
            product: Product name (e.g., "Aspose.Slides")
            platform: Platform/language (e.g., "Java")
            website: Website domain (e.g., "aspose.com")
        """
        self.product = product
        self.platform = platform
        self.website = website
        self.start_time_ms = self._get_current_time_ms()
        self.items_discovered += 1
        
        logger.info(f"Started job [{self.run_id}]: {product} - {platform} on {website}")
    
    def record_success(self, details: Optional[str] = None):
        """
        Record a successful operation
        
        Args:
            details: Optional details about the success
        """
        self.items_succeeded += 1
        self.status = "success"
        logger.info(f"Success recorded [{self.run_id}]. Total: {self.items_succeeded}")
        
        if details:
            logger.debug(f"Success details: {details}")
    
    def record_failure(self, error: str):
        """
        Record a failed operation
        
        Args:
            error: Error message or description
        """
        self.items_failed += 1
        self.status = "failed"
        self.errors.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error": error
        })
        logger.error(f"Failure recorded [{self.run_id}]: {error}")
    
    def end_job(self):
        """Mark the job as completed"""
        self.end_time_ms = self._get_current_time_ms()
        self.run_duration_ms = self.end_time_ms - self.start_time_ms
        self.timestamp = datetime.now(timezone.utc).isoformat()
        
        logger.info(f"Job completed [{self.run_id}] in {self.run_duration_ms}ms")
    
    def _get_current_time_ms(self) -> int:
        """Get current time in milliseconds"""
        return int(datetime.now().timestamp() * 1000)
    
    def get_metrics_payload(self) -> Dict[str, Any]:
        """
        Get the current metrics as a payload dictionary
        
        Returns:
            Dictionary containing all metrics in the required format
        """
        payload = {
            "timestamp": self.timestamp or datetime.now(timezone.utc).isoformat(),
            "status": self.status,
            "agent_name": self.agent_name,
            "agent_owner": self.agent_owner,
            "job_type": self.job_type,
            "run_id": self.run_id,
            "product": self.product or "Unknown",
            "platform": self.platform or "Unknown",
            "website": self.website or "Unknown",
            "website_section": self.website_section,
            "item_name": self.item_name,
            "items_discovered": self.items_discovered,
            "items_failed": self.items_failed,
            "items_succeeded": self.items_succeeded,
            "run_duration_ms": self.run_duration_ms,
            "run_env": self.run_env
        }
        
        return payload
    
    async def send_metrics_to_team(self) -> bool:
        """
        Send metrics to Team Google Script endpoint
        
        Returns:
            True if successful, False otherwise
        """
        payload = self.get_metrics_payload()
        print(f"metrix for teams - {payload} - env is {os.getenv('GITHUB_ACTIONS')}")
        logger.debug(
            "Sending team metrics payload:\n%s",
            json.dumps(payload, indent=2)
        )

        # Add token as query parameter
        url_with_token = f"{self.GOOGLE_SCRIPT_URL_FOR_TEAM}?token={self.TOKEN_FOR_TEAM}"

        headers = {
            "Content-Type": "application/json"
        }
     
        timeout = aiohttp.ClientTimeout(total=30)

        try:
            # No need for custom SSL context in GitHub Actions
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    url_with_token,
                    json=payload,
                    headers=headers
                ) as response:

                    response_text = await response.text()

                    if response.status == 200:
                        logger.info(
                            f"✅ Team metrics sent successfully for run_id: {self.run_id}"
                        )
                        logger.debug(f"Response: {response_text}")
                        return True

                    logger.error(
                        f"❌ Failed to send team metrics "
                        f"(HTTP {response.status}) for run_id: {self.run_id}"
                    )
                    logger.error(f"Response: {response_text}")
                    return False

        except asyncio.TimeoutError:
            logger.error(
                f"❌ Timeout while sending team metrics for run_id: {self.run_id}"
            )
            return False

        except Exception:
            logger.exception(
                f"❌ Unexpected error while sending team metrics for run_id: {self.run_id}"
            )
            return False
    
    async def send_metrics_to_prod(self) -> bool:
        """
        Send metrics to Prod Google Script endpoint
        
        Returns:
            True if successful, False otherwise
        """
        payload = self.get_metrics_payload()
        # Remove run_env for prod endpoint if needed
        payload.pop('run_env', None) 
      
        logger.debug(
            "Sending prod metrics payload:\n%s",
            json.dumps(payload, indent=2)
        )

        # Add token as query parameter
        url_with_token = f"{self.GOOGLE_SCRIPT_URL_FOR_PROD}?token={self.TOKEN_FOR_PROD}"

        headers = {
            "Content-Type": "application/json"
        }
     
        timeout = aiohttp.ClientTimeout(total=30)

        try:
            # No need for custom SSL context in GitHub Actions
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    url_with_token,
                    json=payload,
                    headers=headers
                ) as response:

                    response_text = await response.text()

                    if response.status == 200:
                        logger.info(
                            f"✅ Prod metrics sent successfully for run_id: {self.run_id}"
                        )
                        logger.debug(f"Response: {response_text}")
                        return True

                    logger.error(
                        f"❌ Failed to send prod metrics "
                        f"(HTTP {response.status}) for run_id: {self.run_id}"
                    )
                    logger.error(f"Response: {response_text}")
                    return False

        except asyncio.TimeoutError:
            logger.error(
                f"❌ Timeout while sending prod metrics for run_id: {self.run_id}"
            )
            return False

        except Exception:
            logger.exception(
                f"❌ Unexpected error while sending prod metrics for run_id: {self.run_id}"
            )
            return False
        
    def print_summary(self):
        """Print a summary of the metrics"""
        print("\n" + "="*60)
        print("METRICS SUMMARY")
        print("="*60)
        print(f"Run ID:            {self.run_id}")
        print(f"Status:            {self.status}")
        print(f"Agent Name:        {self.agent_name}")
        print(f"Agent Owner:       {self.agent_owner}")
        print(f"Job Type:          {self.job_type}")
        print(f"Product:           {self.product}")
        print(f"Platform:          {self.platform}")
        print(f"Website:           {self.website}")
        print(f"Environment:       {self.run_env}")
        print(f"Items Discovered:  {self.items_discovered}")
        print(f"Items Succeeded:   {self.items_succeeded}")
        print(f"Items Failed:      {self.items_failed}")
        print(f"Duration:          {self.run_duration_ms}ms ({self.run_duration_ms/1000:.2f}s)")
        print(f"Timestamp:         {self.timestamp}")
        
        if self.errors:
            print(f"\nErrors ({len(self.errors)}):")
            for idx, error in enumerate(self.errors, 1):
                print(f"  {idx}. {error['error']}")
        
        print("="*60 + "\n")
    
    def reset(self):
        """Reset all metrics counters and generate new run_id"""
        self.run_id = str(uuid.uuid4())
        self.items_discovered = 0
        self.items_succeeded = 0
        self.items_failed = 0
        self.errors = []
        self.start_time_ms = None
        self.end_time_ms = None
        self.run_duration_ms = 0
        self.status = "running"
        self.timestamp = None
        logger.info(f"Metrics reset with new run_id: {self.run_id}")
