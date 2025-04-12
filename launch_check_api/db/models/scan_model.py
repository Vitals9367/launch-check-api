from datetime import datetime
from typing import Optional
from sqlalchemy import String, JSON, DateTime, Enum as SQLAEnum
from sqlalchemy.orm import Mapped, mapped_column
from enum import Enum

from launch_check_api.db.base import Base

class ScanStatus(str, Enum):
    """Enum for scan status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

class ScanModel(Base):
    """Model for storing security scan results."""

    __tablename__ = "scans"

    # Primary key and basic info
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    target_url: Mapped[str] = mapped_column(String(length=2048))  # Long URL support
    
    # Scan metadata
    status: Mapped[ScanStatus] = mapped_column(SQLAEnum(ScanStatus))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Scan configuration
    severity_levels: Mapped[list] = mapped_column(JSON)  # Store as ["low", "medium", "high", etc.]
    rate_limit: Mapped[int] = mapped_column(default=150)
    timeout: Mapped[int] = mapped_column(default=5)
    
    # Results
    total_findings: Mapped[Optional[int]] = mapped_column(nullable=True)
    findings: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # Store full JSON results
    
    # Statistics
    critical_count: Mapped[int] = mapped_column(default=0)
    high_count: Mapped[int] = mapped_column(default=0)
    medium_count: Mapped[int] = mapped_column(default=0)
    low_count: Mapped[int] = mapped_column(default=0)
    info_count: Mapped[int] = mapped_column(default=0)
    
    # Error handling
    error_message: Mapped[Optional[str]] = mapped_column(String(length=1000), nullable=True)
    warnings: Mapped[Optional[str]] = mapped_column(String(length=1000), nullable=True)

    def __repr__(self) -> str:
        """String representation of the scan."""
        return f"<Scan(id={self.id}, target={self.target_url}, status={self.status})>"

    @property
    def duration(self) -> Optional[float]:
        """Calculate scan duration in seconds."""
        if self.completed_at and self.started_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None

    def update_severity_counts(self, results: dict) -> None:
        """Update severity counts based on scan results."""
        severity_count = {
            'critical': 0,
            'high': 0,
            'medium': 0,
            'low': 0,
            'info': 0
        }
        
        for finding in results.get('findings', []):
            severity = finding.get('info', {}).get('severity', '').lower()
            if severity in severity_count:
                severity_count[severity] += 1
        
        self.critical_count = severity_count['critical']
        self.high_count = severity_count['high']
        self.medium_count = severity_count['medium']
        self.low_count = severity_count['low']
        self.info_count = severity_count['info']
        self.total_findings = sum(severity_count.values())
        