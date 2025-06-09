"""
Advanced dependency injection container for AI Signal.

This module provides a comprehensive ServiceContainer
that supports automatic dependency resolution, multiple service lifetimes,
scoped instances, and circular dependency detection.
"""

import inspect
import logging
from abc import ABC
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")

# =============================================================================
# Service Lifetime and Registration
# =============================================================================


class ServiceScope:
    """Service lifecycle scopes"""

    SINGLETON = "singleton"
    TRANSIENT = "transient"
    SCOPED = "scoped"


@dataclass
class ServiceRegistration:
    """Service registration metadata"""

    interface: Type
    implementation: Type
    scope: str = ServiceScope.SINGLETON
    factory: Optional[Callable] = None
    instance: Optional[Any] = None
    dependencies: List[Type] = field(default_factory=list)


# =============================================================================
# Advanced Service Container
# =============================================================================


class ServiceContainer:
    """
    Advanced dependency injection container for AI Signal.

    Features:
    - Automatic dependency resolution through constructor inspection
    - Multiple service lifetimes (singleton, transient, scoped)
    - Circular dependency detection
    - Scoped instance management
    - Registration validation

    Example:
        container = ServiceContainer()
        container.register_singleton(IStorageService, SQLiteStorageService)
        container.register_transient(IFetchService, JinaFetchService)

        # Automatic dependency injection
        storage = container.get(IStorageService)
    """

    def __init__(self):
        """Initialize an empty service container."""
        self._registrations: Dict[Type, ServiceRegistration] = {}
        self._instances: Dict[Type, Any] = {}
        self._resolution_stack: List[Type] = []
        self._scoped_instances: Dict[str, Dict[Type, Any]] = {}
        self._current_scope: Optional[str] = None

    # =========================================================================
    # Registration Methods
    # =========================================================================

    def register_singleton(
        self,
        interface: Type[T],
        implementation: Type[T],
        factory: Optional[Callable[[], T]] = None,
    ) -> "ServiceContainer":
        """
        Register a singleton service (one instance for entire application lifetime).

        Args:
            interface: The interface or abstract class type
            implementation: The concrete implementation class
            factory: Optional factory function to create the instance

        Returns:
            Self for method chaining
        """
        dependencies = self._get_constructor_dependencies(implementation)

        self._registrations[interface] = ServiceRegistration(
            interface=interface,
            implementation=implementation,
            scope=ServiceScope.SINGLETON,
            factory=factory,
            dependencies=dependencies,
        )
        return self

    def register_transient(
        self,
        interface: Type[T],
        implementation: Type[T],
        factory: Optional[Callable[[], T]] = None,
    ) -> "ServiceContainer":
        """
        Register a transient service (new instance each time).

        Args:
            interface: The interface or abstract class type
            implementation: The concrete implementation class
            factory: Optional factory function to create the instance

        Returns:
            Self for method chaining
        """
        dependencies = self._get_constructor_dependencies(implementation)

        self._registrations[interface] = ServiceRegistration(
            interface=interface,
            implementation=implementation,
            scope=ServiceScope.TRANSIENT,
            factory=factory,
            dependencies=dependencies,
        )
        return self

    def register_scoped(
        self,
        interface: Type[T],
        implementation: Type[T],
        factory: Optional[Callable[[], T]] = None,
    ) -> "ServiceContainer":
        """
        Register a scoped service (one instance per scope).

        Args:
            interface: The interface or abstract class type
            implementation: The concrete implementation class
            factory: Optional factory function to create the instance

        Returns:
            Self for method chaining
        """
        dependencies = self._get_constructor_dependencies(implementation)

        self._registrations[interface] = ServiceRegistration(
            interface=interface,
            implementation=implementation,
            scope=ServiceScope.SCOPED,
            factory=factory,
            dependencies=dependencies,
        )
        return self

    def register_instance(self, interface: Type[T], instance: T) -> "ServiceContainer":
        """
        Register a specific instance as a singleton.

        Args:
            interface: The interface or abstract class type
            instance: The pre-created instance

        Returns:
            Self for method chaining
        """
        self._registrations[interface] = ServiceRegistration(
            interface=interface,
            implementation=type(instance),
            scope=ServiceScope.SINGLETON,
            instance=instance,
        )
        self._instances[interface] = instance
        return self

    # Legacy methods for backward compatibility (deprecated)
    def register(self, interface_type: Type[T], implementation: T) -> None:
        """
        Legacy method: Register a service instance (deprecated).
        Use register_instance() instead.
        """
        logger.warning(
            "register() method is deprecated. Use register_instance() instead."
        )
        self.register_instance(interface_type, implementation)

    def register_factory(self, interface_type: Type[T], factory: callable) -> None:
        """
        Legacy method: Register a factory function (deprecated).
        Use register_singleton() with factory parameter instead.
        """
        logger.warning(
            "register_factory() method is deprecated. "
            "Use register_singleton() with factory parameter instead."
        )
        self.register_singleton(interface_type, object, factory=factory)

    # =========================================================================
    # Resolution Methods
    # =========================================================================

    def get(self, interface: Type[T]) -> T:
        """
        Get service instance with automatic dependency resolution.

        Args:
            interface: The interface or abstract class type to resolve

        Returns:
            The resolved service instance

        Raises:
            ValueError: If service not registered or circular dependency detected
        """
        if interface not in self._registrations:
            raise ValueError(f"Service {interface.__name__} not registered")

        # Check for circular dependencies
        if interface in self._resolution_stack:
            cycle = " -> ".join(cls.__name__ for cls in self._resolution_stack)
            cycle += f" -> {interface.__name__}"
            raise ValueError(f"Circular dependency detected: {cycle}")

        registration = self._registrations[interface]

        # Return existing instance if singleton
        if registration.scope == ServiceScope.SINGLETON:
            if interface in self._instances:
                return self._instances[interface]

        # Return scoped instance
        elif registration.scope == ServiceScope.SCOPED:
            if self._current_scope:
                scoped_instances = self._scoped_instances.get(self._current_scope, {})
                if interface in scoped_instances:
                    return scoped_instances[interface]

        # Create new instance
        self._resolution_stack.append(interface)
        try:
            instance = self._create_instance(registration)

            # Store instance based on scope
            if registration.scope == ServiceScope.SINGLETON:
                self._instances[interface] = instance
            elif registration.scope == ServiceScope.SCOPED and self._current_scope:
                if self._current_scope not in self._scoped_instances:
                    self._scoped_instances[self._current_scope] = {}
                self._scoped_instances[self._current_scope][interface] = instance

            return instance

        finally:
            self._resolution_stack.pop()

    # Legacy method for backward compatibility (deprecated)
    def resolve(self, interface_type: Type[T]) -> T:
        """
        Legacy method: Resolve a service (deprecated).
        Use get() instead.
        """
        logger.warning("resolve() method is deprecated. Use get() instead.")
        return self.get(interface_type)

    # =========================================================================
    # Scope Management
    # =========================================================================

    @asynccontextmanager
    async def scope(self, scope_name: str):
        """
        Create a new dependency resolution scope.

        Args:
            scope_name: Unique name for the scope

        Usage:
            async with container.scope("request_123"):
                service = container.get(IScopedService)
                # service will be the same instance within this scope
        """
        old_scope = self._current_scope
        self._current_scope = scope_name
        try:
            yield
        finally:
            # Cleanup scoped instances
            if scope_name in self._scoped_instances:
                del self._scoped_instances[scope_name]
            self._current_scope = old_scope

    # =========================================================================
    # Private Implementation Methods
    # =========================================================================

    def _create_instance(self, registration: ServiceRegistration) -> Any:
        """
        Create service instance with automatic dependency injection.

        Args:
            registration: Service registration metadata

        Returns:
            New service instance with dependencies injected

        Raises:
            ValueError: If instance cannot be created
        """
        if registration.instance:
            return registration.instance

        if registration.factory:
            return registration.factory()

        # Resolve constructor dependencies
        dependencies = {}
        for dep_type in registration.dependencies:
            # Create parameter name from interface name
            # IStorageService -> storage_service
            param_name = self._interface_to_param_name(dep_type)
            dependencies[param_name] = self.get(dep_type)

        # Create instance with injected dependencies
        try:
            return registration.implementation(**dependencies)
        except TypeError as e:
            # Fallback: try creating with no arguments
            try:
                return registration.implementation()
            except TypeError:
                raise ValueError(
                    f"Cannot create instance of "
                    f"{registration.implementation.__name__}: {e}. "
                    f"Constructor dependencies: "
                    f"{[dep.__name__ for dep in registration.dependencies]}"
                )

    def _get_constructor_dependencies(self, implementation: Type) -> List[Type]:
        """
        Extract constructor dependencies from type hints.

        Args:
            implementation: The implementation class to inspect

        Returns:
            List of interface types that are constructor dependencies
        """
        dependencies = []

        try:
            sig = inspect.signature(implementation.__init__)
            for param_name, param in sig.parameters.items():
                if param_name == "self":
                    continue

                if param.annotation and param.annotation != inspect.Parameter.empty:
                    # Check if it's an interface (ABC subclass)
                    if (
                        hasattr(param.annotation, "__bases__")
                        and ABC in param.annotation.__bases__
                    ):
                        dependencies.append(param.annotation)

        except (ValueError, TypeError):
            # No signature available or invalid signature
            pass

        return dependencies

    def _interface_to_param_name(self, interface_type: Type) -> str:
        """
        Convert interface type name to constructor parameter name.

        Examples:
            IStorageService -> storage_service
            IConfigService -> config_service

        Args:
            interface_type: The interface type

        Returns:
            Parameter name for dependency injection
        """
        name = interface_type.__name__
        # Remove leading 'I' if present
        if name.startswith("I") and len(name) > 1 and name[1].isupper():
            name = name[1:]

        # Convert CamelCase to snake_case
        import re

        name = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
        name = re.sub("([a-z0-9])([A-Z])", r"\1_\2", name).lower()

        return name

    # =========================================================================
    # Validation and Diagnostics
    # =========================================================================

    def validate_registrations(self) -> List[str]:
        """
        Validate all service registrations for missing dependencies.

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        for interface, registration in self._registrations.items():
            # Check if all dependencies can be resolved
            for dep in registration.dependencies:
                if dep not in self._registrations:
                    errors.append(
                        f"Service {interface.__name__} "
                        f"depends on unregistered service {dep.__name__}"
                    )

        return errors

    def get_registration_info(self) -> Dict[str, Dict[str, Any]]:
        """
        Get diagnostic information about all registered services.

        Returns:
            Dictionary with service registration details
        """
        info = {}

        for interface, registration in self._registrations.items():
            info[interface.__name__] = {
                "implementation": registration.implementation.__name__,
                "scope": registration.scope,
                "dependencies": [dep.__name__ for dep in registration.dependencies],
                "has_instance": interface in self._instances,
                "has_factory": registration.factory is not None,
            }

        return info

    def clear(self) -> None:
        """Clear all registered services, instances, and scopes."""
        self._registrations.clear()
        self._instances.clear()
        self._scoped_instances.clear()
        self._resolution_stack.clear()
        self._current_scope = None


# =============================================================================
# Factory Functions
# =============================================================================


def create_container() -> ServiceContainer:
    """
    Create a new empty service container.

    Returns:
        Empty ServiceContainer ready for registrations
    """
    return ServiceContainer()


def create_production_container() -> ServiceContainer:
    """
    Create service container with production service registrations.

    Note: Service implementations will be registered here in later sprints.

    Returns:
        ServiceContainer configured for production use
    """
    container = ServiceContainer()

    # Register production services in later migration sprints
    # container.register_singleton(IStorageService, SQLiteStorageService)
    # container.register_singleton(IConfigService, FileConfigService)
    # container.register_singleton(IFetchService, JinaFetchService)
    # container.register_singleton(IAnalysisService, OpenAIAnalysisService)
    # container.register_singleton(IUserService, DefaultUserService)
    # container.register_singleton(IEventBus, AsyncEventBus)
    # container.register_singleton(ICoreService, CoreService)

    return container
