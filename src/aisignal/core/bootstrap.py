"""
Bootstrap module for AI Signal service registration.

This module provides functions to configure and initialize all services
in the dependency injection container.
"""

import logging
from pathlib import Path
from typing import Optional

from aisignal.core.events import EventBus, get_event_bus, set_event_bus
from aisignal.core.interfaces import (
    IConfigManager,
    IContentService,
    ICoreService,
    IStorageService,
)
from aisignal.core.services import (
    ConfigService,
    ContentService,
    CoreService,
    StorageService,
)
from aisignal.core.token_tracker import TokenTracker
from aisignal.utils.service_container import ServiceContainer

logger = logging.getLogger(__name__)

# Default paths
DEFAULT_CONFIG_PATH = Path.home() / ".config" / "aisignal" / "config.yaml"
DEFAULT_DB_PATH = Path.home() / ".config" / "aisignal" / "storage.db"


def create_container(
    config_path: Optional[Path] = None,
    db_path: Optional[Path] = None,
) -> ServiceContainer:
    """
    Create and configure a service container with all dependencies.

    This is the main entry point for bootstrapping the application.
    It creates all services and wires them together in the container.

    Args:
        config_path: Optional path to configuration file (uses default if None)
        db_path: Optional path to database file (uses default if None)

    Returns:
        Configured ServiceContainer with all services registered
    """
    container = ServiceContainer()

    # Resolve paths
    config_file = config_path or DEFAULT_CONFIG_PATH
    database_file = db_path or DEFAULT_DB_PATH

    logger.info(f"Bootstrapping services with config: {config_file}")

    # Register event bus first (used by other services)
    _register_event_bus(container)

    # Register services using factories for lazy initialization
    _register_config_service(container, config_file)
    _register_storage_service(container, database_file)
    _register_content_service(container, database_file)
    _register_core_service(container)

    logger.info("Service container configured successfully")
    return container


def _register_config_service(container: ServiceContainer, config_path: Path) -> None:
    """Register the configuration service."""

    def create_config():
        logger.debug(f"Creating ConfigService with path: {config_path}")
        return ConfigService(config_path=str(config_path))

    container.register_factory(IConfigManager, create_config)


def _register_storage_service(container: ServiceContainer, db_path: Path) -> None:
    """Register the storage service."""

    def create_storage():
        logger.debug(f"Creating StorageService with db: {db_path}")
        return StorageService(db_path=str(db_path))

    container.register_factory(IStorageService, create_storage)


def _register_content_service(container: ServiceContainer, db_path: Path) -> None:
    """Register the content service."""

    def create_content():
        # ContentService needs config for API keys and storage
        config = container.resolve(IConfigManager)
        storage = container.resolve(IStorageService)

        # Create token tracker with same db path
        token_tracker = TokenTracker(db_path=str(db_path))

        logger.debug("Creating ContentService")
        return ContentService(
            jina_api_key=config.jina_api_key,
            openai_api_key=config.openai_api_key,
            categories=config.categories,
            storage_service=storage,
            token_tracker=token_tracker,
            min_threshold=config.min_threshold,
            max_threshold=config.max_threshold,
        )

    container.register_factory(IContentService, create_content)


def _register_event_bus(container: ServiceContainer) -> EventBus:
    """Register and return the event bus."""
    event_bus = EventBus()
    set_event_bus(event_bus)  # Set as global default
    container.register(EventBus, event_bus)
    logger.debug("EventBus registered")
    return event_bus


def _register_core_service(container: ServiceContainer) -> None:
    """Register the core orchestrator service."""

    def create_core():
        storage = container.resolve(IStorageService)
        config = container.resolve(IConfigManager)
        content = container.resolve(IContentService)
        event_bus = container.resolve(EventBus)

        logger.debug("Creating CoreService")
        return CoreService(
            storage_service=storage,
            config_service=config,
            content_service=content,
            event_bus=event_bus,
        )

    container.register_factory(ICoreService, create_core)


def create_minimal_container(
    config_path: Optional[Path] = None,
    db_path: Optional[Path] = None,
) -> ServiceContainer:
    """
    Create a minimal container without content service.

    Useful for CLI operations that don't need AI features.

    Args:
        config_path: Optional path to configuration file
        db_path: Optional path to database file

    Returns:
        Configured ServiceContainer with minimal services
    """
    container = ServiceContainer()

    config_file = config_path or DEFAULT_CONFIG_PATH
    database_file = db_path or DEFAULT_DB_PATH

    # Register event bus first
    _register_event_bus(container)

    _register_config_service(container, config_file)
    _register_storage_service(container, database_file)

    # Register CoreService without content service
    def create_core():
        storage = container.resolve(IStorageService)
        config = container.resolve(IConfigManager)
        event_bus = container.resolve(EventBus)
        return CoreService(
            storage_service=storage,
            config_service=config,
            content_service=None,
            event_bus=event_bus,
        )

    container.register_factory(ICoreService, create_core)

    return container
