from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional


class SyncStatus(Enum):
    """Represents the status of a sync operation"""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class SourceProgress:
    """Tracks sync progress for a single source"""

    url: str
    status: SyncStatus = SyncStatus.PENDING
    error: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    items_found: int = 0
    items_processed: int = 0
    new_items: int = 0


@dataclass
class SyncProgress:
    """Tracks overall sync progress across all sources"""

    sources: Dict[str, SourceProgress] = field(default_factory=dict)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

    def start_sync(self, urls: List[str]):
        """Initialize sync for a list of sources"""
        self.sources = {url: SourceProgress(url=url) for url in urls}
        self.start_time = datetime.now()
        self.end_time = None

    def start_source(self, url: str):
        """Mark a source as starting sync"""
        if url in self.sources:
            self.sources[url].status = SyncStatus.IN_PROGRESS
            self.sources[url].start_time = datetime.now()

    def complete_source(self, url: str, items_found: int, new_items: int):
        """Mark a source as completed with results"""
        if url in self.sources:
            source = self.sources[url]
            source.status = SyncStatus.COMPLETED
            source.end_time = datetime.now()
            source.items_found = items_found
            source.new_items = new_items

    def fail_source(self, url: str, error: str):
        """Mark a source as failed with error details"""
        if url in self.sources:
            source = self.sources[url]
            source.status = SyncStatus.FAILED
            source.end_time = datetime.now()
            source.error = error

    def update_progress(self, url: str, items_processed: int):
        """Update processing progress for a source"""
        if url in self.sources:
            self.sources[url].items_processed = items_processed

    def complete_sync(self):
        """Mark overall sync as complete"""
        self.end_time = datetime.now()

    @property
    def total_sources(self) -> int:
        """Total number of sources to sync"""
        return len(self.sources)

    @property
    def completed_sources(self) -> int:
        """Number of sources that completed sync"""
        return sum(1 for s in self.sources.values() if s.status == SyncStatus.COMPLETED)

    @property
    def failed_sources(self) -> int:
        """Number of sources that failed sync"""
        return sum(1 for s in self.sources.values() if s.status == SyncStatus.FAILED)

    @property
    def in_progress_sources(self) -> int:
        """Number of sources currently syncing"""
        return sum(
            1 for s in self.sources.values() if s.status == SyncStatus.IN_PROGRESS
        )

    @property
    def total_items_found(self) -> int:
        """Total items found across all sources"""
        return sum(s.items_found for s in self.sources.values())

    @property
    def total_new_items(self) -> int:
        """Total new items found across all sources"""
        return sum(s.new_items for s in self.sources.values())
