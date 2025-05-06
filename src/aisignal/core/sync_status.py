from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pprint import pformat
from typing import Dict, List, Optional

from textual import log


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

    PHASE_FETCH = 0.33
    PHASE_ANALYZE = 0.66
    PHASE_PROCESS = 1.0

    sources: Dict[str, SourceProgress] = field(default_factory=dict)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    analyzing: bool = False
    processing: bool = False

    def start_analysis(self):
        """Mark entering analysis phase"""
        self.analyzing = True
        self.processing = False
        log.debug("start_analysis called.")

    def start_processing(self):
        """Mark entering processing phase"""
        self.analyzing = False
        self.processing = True
        log.debug("start_processing called.")

    @property
    def overall_progress(self) -> float:
        """Calculate overall progress percentage including phase weights"""
        if self.total_sources == 0:
            return 0.0

        # Calculate progress based on current phase
        if not any(s.status != SyncStatus.PENDING for s in self.sources.values()):
            # Still in setup
            return 0.0

        completed = self.completed_sources
        failed = self.failed_sources

        if self.analyzing:  # New flag to track analysis phase
            base = self.PHASE_FETCH * 100
            analysis_progress = (completed + failed) / self.total_sources
            log.debug(f"base: {base}, progress: {analysis_progress}")
            return (
                base + (self.PHASE_ANALYZE - self.PHASE_FETCH) * analysis_progress * 100
            )
        elif self.processing:  # New flag to track processing phase
            base = self.PHASE_ANALYZE * 100
            process_progress = (completed + failed) / self.total_sources
            log.debug(f"base: {base}, progress: {process_progress}")
            return (
                base
                + (self.PHASE_PROCESS - self.PHASE_ANALYZE) * process_progress * 100
            )
        else:
            # In fetch phase
            fetch_progress = (completed + failed) / self.total_sources
            log.debug(f"base: 0, progress: {fetch_progress}")
            return self.PHASE_FETCH * fetch_progress * 100

    def start_sync(self, urls: List[str]):
        """Initialize sync for a list of sources"""
        self.sources = {url: SourceProgress(url=url) for url in urls}
        self.start_time = datetime.now()
        self.end_time = None
        log.debug(f"start_sync called with sources:\n{pformat(self.sources.values())}.")

    def start_source(self, url: str):
        """Mark a source as starting sync"""
        log.debug(f"start_source called with url: {url}.")
        if url in self.sources:
            self.sources[url].status = SyncStatus.IN_PROGRESS
            self.sources[url].start_time = datetime.now()

    def complete_source(self, url: str, items_found: int, new_items: int):
        """Mark a source as completed with results"""
        log.debug(f"complete_source called with url: {url}.")
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
        log.debug(f"fail_source called with url: {url}.")

    def update_progress(self, url: str, items_processed: int):
        """Update processing progress for a source"""
        if url in self.sources:
            self.sources[url].items_processed = items_processed
        log.debug(f"update_progress called with url: {url}.")

    def complete_sync(self):
        """Mark overall sync as complete"""
        self.end_time = datetime.now()
        log.debug("complete_sync called.")

    @property
    def total_sources(self) -> int:
        """Total number of sources to sync"""
        n_sources = len(self.sources)
        log.debug(f"total_sources called => {n_sources}.")
        return n_sources

    @property
    def completed_sources(self) -> int:
        """Number of sources that completed sync"""
        n_completed_sources = sum(
            1 for s in self.sources.values() if s.status == SyncStatus.COMPLETED
        )
        log.debug(f"completed_sources called => {n_completed_sources}.")
        return n_completed_sources

    @property
    def failed_sources(self) -> int:
        """Number of sources that failed sync"""
        n_failed_sources = sum(
            1 for s in self.sources.values() if s.status == SyncStatus.FAILED
        )
        log.debug(f"failed_sources called => {n_failed_sources}.")
        return n_failed_sources

    @property
    def in_progress_sources(self) -> int:
        """Number of sources currently syncing"""
        n_in_progress_sources = sum(
            1 for s in self.sources.values() if s.status == SyncStatus.IN_PROGRESS
        )
        log.debug(f"in_progress_sources called => {n_in_progress_sources}.")
        return n_in_progress_sources

    @property
    def total_items_found(self) -> int:
        """Total items found across all sources"""
        n_total_items_fount = sum(s.items_found for s in self.sources.values())
        log.debug(f"total_items_found called => {n_total_items_fount}.")
        return n_total_items_fount

    @property
    def total_new_items(self) -> int:
        """Total new items found across all sources"""
        n_total_new_items = sum(s.new_items for s in self.sources.values())
        log.debug(f"total_new_items called => {n_total_new_items}.")
        return n_total_new_items
