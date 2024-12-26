class SyncError(Exception):
    """Base exception for sync-related errors"""

    pass


class ContentFetchError(SyncError):
    """Error fetching content from source"""

    def __init__(self, url: str, reason: str):
        self.url = url
        self.reason = reason
        super().__init__(f"Failed to fetch content from {url}: {reason}")


class APIError(SyncError):
    """Error communicating with external APIs"""

    def __init__(self, service: str, status_code: int, message: str):
        self.service = service
        self.status_code = status_code
        self.message = message
        super().__init__(f"{service} API error ({status_code}): {message}")


class ContentAnalysisError(SyncError):
    """Error analyzing content"""

    def __init__(self, url: str, reason: str):
        self.url = url
        self.reason = reason
        super().__init__(f"Failed to analyze content from {url}: {reason}")


class StorageError(SyncError):
    """Error storing content or items"""

    def __init__(self, operation: str, reason: str):
        self.operation = operation
        self.reason = reason
        super().__init__(f"Storage error during {operation}: {reason}")
