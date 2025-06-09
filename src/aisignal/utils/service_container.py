"""
Simple dependency injection container for AI Signal.

This module provides a basic ServiceContainer that allows for registering
and resolving dependencies. It's designed to be simple and lightweight,
focusing on the core functionality needed for the application.
"""

from typing import Any, Dict, Type, TypeVar, cast

T = TypeVar("T")


class ServiceContainer:
    """
    A simple dependency injection container.

    This container allows for registering services by their interface type
    and resolving them when needed. It supports singleton instances and
    factory functions.

    Example:
        container = ServiceContainer()
        container.register(IConfigManager, ConfigManager())
        config_manager = container.resolve(IConfigManager)
    """

    def __init__(self):
        """Initialize an empty service container."""
        self._services: Dict[Type, Any] = {}
        self._factories: Dict[Type, callable] = {}

    def register(self, interface_type: Type[T], implementation: T) -> None:
        """
        Register a service implementation for an interface type.

        Args:
            interface_type: The interface or abstract class type
            implementation: The concrete implementation instance
        """
        self._services[interface_type] = implementation

    def register_factory(self, interface_type: Type[T], factory: callable) -> None:
        """
        Register a factory function that creates instances of a service.

        Args:
            interface_type: The interface or abstract class type
            factory: A callable that returns an instance of the service
        """
        self._factories[interface_type] = factory

    def resolve(self, interface_type: Type[T]) -> T:
        """
        Resolve a service implementation for an interface type.

        Args:
            interface_type: The interface or abstract class type to resolve

        Returns:
            The registered implementation for the interface

        Raises:
            KeyError: If no implementation is registered for the interface
        """
        # Check if we have a direct service registration
        if interface_type in self._services:
            return cast(T, self._services[interface_type])

        # Check if we have a factory registration
        if interface_type in self._factories:
            # Call the factory to create the instance
            instance = self._factories[interface_type]()
            # Cache the instance for future resolves
            self._services[interface_type] = instance
            return cast(T, instance)

        raise KeyError(f"No implementation registered for {interface_type.__name__}")

    def clear(self) -> None:
        """Clear all registered services and factories."""
        self._services.clear()
        self._factories.clear()
