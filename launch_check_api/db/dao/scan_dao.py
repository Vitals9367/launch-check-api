from datetime import datetime
from typing import List, Optional, Dict, Any

from fastapi import Depends
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from launch_check_api.db.dependencies import get_db_session
from launch_check_api.db.models.scan_model import ScanModel, ScanStatus


class ScanDAO:
    """Data Access Object for scan operations."""

    def __init__(self, session: AsyncSession = Depends(get_db_session)) -> None:
        self.session = session

    async def create_scan(
        self,
        target_url: str,
        severity_levels: List[str],
        rate_limit: int = 150,
        timeout: int = 5,
    ) -> ScanModel:
        """
        Create a new scan record.

        Args:
            target_url: URL to be scanned
            severity_levels: List of severity levels to scan for
            rate_limit: Rate limit for the scan
            timeout: Timeout in minutes
        """
        scan = ScanModel(
            target_url=target_url,
            status=ScanStatus.PENDING,
            started_at=datetime.utcnow(),
            severity_levels=severity_levels,
            rate_limit=rate_limit,
            timeout=timeout,
        )
        self.session.add(scan)
        await self.session.commit()
        await self.session.refresh(scan)
        return scan

    async def get_scan_by_id(self, scan_id: int) -> Optional[ScanModel]:
        """
        Get a specific scan by ID.

        Args:
            scan_id: ID of the scan to retrieve
        """
        query = select(ScanModel).where(ScanModel.id == scan_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def update_scan(
        self,
        scan_id: int,
        update_data: Dict[str, Any],
    ) -> Optional[ScanModel]:
        """
        Update a scan record with new data.

        Args:
            scan_id: ID of the scan to update
            update_data: Dictionary containing fields to update
        """
        scan = await self.get_scan_by_id(scan_id)
        if not scan:
            return None

        for key, value in update_data.items():
            if hasattr(scan, key):
                setattr(scan, key, value)

        await self.session.commit()
        await self.session.refresh(scan)
        return scan

    async def get_scans(
        self,
        limit: int = 10,
        offset: int = 0,
        status: Optional[ScanStatus] = None,
        target_url: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[ScanModel]:
        """
        Get scans with filtering and pagination.

        Args:
            limit: Maximum number of scans to return
            offset: Number of scans to skip
            status: Filter by scan status
            target_url: Filter by target URL
            start_date: Filter scans after this date
            end_date: Filter scans before this date
        """
        query = select(ScanModel).order_by(desc(ScanModel.started_at))

        if status:
            query = query.where(ScanModel.status == status)
        if target_url:
            query = query.where(ScanModel.target_url.ilike(f"%{target_url}%"))
        if start_date:
            query = query.where(ScanModel.started_at >= start_date)
        if end_date:
            query = query.where(ScanModel.started_at <= end_date)

        query = query.limit(limit).offset(offset)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def delete_scan(self, scan_id: int) -> bool:
        """
        Delete a scan record.

        Args:
            scan_id: ID of the scan to delete

        Returns:
            bool: True if scan was deleted, False if not found
        """
        scan = await self.get_scan_by_id(scan_id)
        if not scan:
            return False

        await self.session.delete(scan)
        await self.session.commit()
        return True
