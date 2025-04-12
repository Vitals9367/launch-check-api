import asyncio
import json
import logging
import shutil
from datetime import datetime
from typing import Dict, List, Optional, Union

logger = logging.getLogger(__name__)

class NucleiError(Exception):
    """Custom exception for Nuclei-related errors"""

class NucleiService:
    def __init__(self):
        self.nuclei_path = shutil.which("nuclei")
        if not self.nuclei_path:
            raise NucleiError("Nuclei binary not found in system PATH")

    async def _run_command(self, command: List[str]) -> tuple[str, str]:
        """
        Execute a command asynchronously and return stdout and stderr
        """
        try:
            process = await asyncio.create_subprocess_exec(
                *command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await process.communicate()
            return stdout.decode(), stderr.decode()
        except Exception as e:
            raise NucleiError(f"Failed to execute Nuclei command: {e!s}")

    async def scan_target(
        self,
        target: str,
        severity: Optional[List[str]] = None,
        templates: Optional[List[str]] = None,
        output_file: Optional[str] = None,
        rate_limit: int = 150,
        timeout: int = 5,
    ) -> Dict[str, Union[str, List[Dict]]]:
        """
        Scan a target URL using Nuclei

        Args:
            target: URL to scan
            severity: List of severities to scan for (info, low, medium, high, critical)
            templates: List of specific template paths to use
            output_file: Path to save JSON results
            rate_limit: Number of requests per second
            timeout: Timeout for each template execution in minutes

        Returns:
            Dict containing scan results and metadata
        """
        if not target.startswith(("http://", "https://")):
            raise NucleiError("Target URL must start with http:// or https://")

        command = [
            self.nuclei_path,
            "-target",
            target,
            "-j",
            "-rate-limit",
            str(rate_limit),
            "-timeout",
            str(timeout),
        ]

        if severity:
            command.extend(["-severity", ",".join(severity)])

        if templates:
            command.extend(["-t", ",".join(templates)])

        if output_file:
            command.extend(["-output", output_file])

        try:
            stdout, stderr = await self._run_command(command)

            results = []
            print(stdout)
            for line in stdout.splitlines():
                if line.strip():
                    try:
                        result = json.loads(line)
                        results.append(result)
                    except json.JSONDecodeError:
                        logger.warning(f"Failed to parse Nuclei output line: {line}")

            scan_results = {
                "timestamp": datetime.utcnow().isoformat(),
                "target": target,
                "status": "completed",
                "total_findings": len(results),
                "findings": results,
            }

            if stderr:
                scan_results["warnings"] = stderr

            return scan_results

        except Exception as e:
            raise NucleiError(f"Scan failed: {e!s}")

    async def update_templates(self) -> bool:
        """
        Update Nuclei templates to the latest version

        Returns:
            bool: True if update was successful
        """
        try:
            stdout, stderr = await self._run_command(
                [self.nuclei_path, "-update-templates"],
            )
            return "Successfully updated nuclei-templates" in stdout
        except Exception as e:
            raise NucleiError(f"Failed to update templates: {e!s}")

    @staticmethod
    def get_severity_count(results: Dict) -> Dict[str, int]:
        """
        Count findings by severity level

        Args:
            results: Scan results dictionary

        Returns:
            Dict containing count of findings by severity
        """
        severity_count = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}

        for finding in results.get("findings", []):
            severity = finding.get("info", {}).get("severity", "").lower()
            if severity in severity_count:
                severity_count[severity] += 1

        return severity_count
