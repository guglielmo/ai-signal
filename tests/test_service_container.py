"""
Test cases for the AI Signal Service Container.

This module contains comprehensive tests for the dependency injection
container functionality, including registration, resolution, lifecycle
management, and validation.
"""

from abc import ABC, abstractmethod

import pytest

from aisignal.core.interfaces import (
    IConfigManager,
    ICoreService,
    IStorageService,
    OperationResult,
    UserContext,
)
from aisignal.core.models import OperationStatus
from aisignal.utils.advanced_service_container import ServiceContainer, ServiceScope


# Test interfaces and implementations for DI testing
class ITestService(ABC):
    """Test interface for dependency injection testing"""

    @abstractmethod
    def get_name(self) -> str:
        pass


class ITestDependency(ABC):
    """Test dependency interface"""

    @abstractmethod
    def get_value(self) -> str:
        pass


class TestDependency(ITestDependency):
    """Simple test dependency implementation"""

    def get_value(self) -> str:
        return "test_dependency"


class DependentServiceImpl(ITestService):
    """Test service with dependency injection"""

    def __init__(self, test_dependency: ITestDependency):
        self.dependency = test_dependency

    def get_name(self) -> str:
        return f"test_service_with_{self.dependency.get_value()}"


class SimpleTestService(ITestService):
    """Simple test service without dependencies"""

    def __init__(self):
        self.name = "simple_test_service"

    def get_name(self) -> str:
        return self.name


class TestServiceContainer:
    """Test cases for the ServiceContainer class"""

    def test_singleton_registration_and_resolution(self):
        """Test singleton service registration and resolution"""
        container = ServiceContainer()

        # Register a singleton service
        container.register_singleton(ITestService, SimpleTestService)

        # Get the service twice
        service1 = container.get(ITestService)
        service2 = container.get(ITestService)

        # Should be the same instance
        assert service1 is service2
        assert isinstance(service1, SimpleTestService)
        assert service1.get_name() == "simple_test_service"

    def test_transient_registration_and_resolution(self):
        """Test transient service registration and resolution"""
        container = ServiceContainer()

        # Register a transient service
        container.register_transient(ITestService, SimpleTestService)

        # Get the service twice
        service1 = container.get(ITestService)
        service2 = container.get(ITestService)

        # Should be different instances
        assert service1 is not service2
        assert isinstance(service1, SimpleTestService)
        assert isinstance(service2, SimpleTestService)
        assert service1.get_name() == service2.get_name()

    def test_instance_registration(self):
        """Test registering a specific instance"""
        container = ServiceContainer()

        # Create and register a specific instance
        instance = SimpleTestService()
        instance.name = "custom_instance"
        container.register_instance(ITestService, instance)

        # Get the service
        retrieved = container.get(ITestService)

        # Should be the exact same instance
        assert retrieved is instance
        assert retrieved.get_name() == "custom_instance"

    def test_automatic_dependency_injection(self):
        """Test automatic dependency injection via constructor"""
        container = ServiceContainer()

        # Register dependency first
        container.register_singleton(ITestDependency, TestDependency)

        # Register service that depends on the dependency
        container.register_singleton(ITestService, DependentServiceImpl)

        # Get the service - dependency should be automatically injected
        service = container.get(ITestService)

        assert isinstance(service, DependentServiceImpl)
        assert isinstance(service.dependency, TestDependency)
        assert service.get_name() == "test_service_with_test_dependency"

    def test_factory_function_registration(self):
        """Test registration with factory function"""
        container = ServiceContainer()

        # Register with factory function
        def create_service():
            _service = SimpleTestService()
            _service.name = "factory_created"
            return _service

        container.register_singleton(
            ITestService, SimpleTestService, factory=create_service
        )

        # Get the service
        service = container.get(ITestService)

        assert isinstance(service, SimpleTestService)
        assert service.get_name() == "factory_created"

    def test_circular_dependency_detection(self):
        """Test detection of circular dependencies"""
        container = ServiceContainer()

        # Create circular dependency scenario
        class IServiceA(ABC):
            pass

        class IServiceB(ABC):
            pass

        class ServiceA:
            def __init__(self, service_b: IServiceB):
                self.service_b = service_b

        class ServiceB:
            def __init__(self, service_a: IServiceA):
                self.service_a = service_a

        container.register_singleton(IServiceA, ServiceA)
        container.register_singleton(IServiceB, ServiceB)

        # Should raise ValueError for circular dependency
        with pytest.raises(ValueError, match="Circular dependency detected"):
            container.get(IServiceA)

    def test_unregistered_service_error(self):
        """Test error when requesting unregistered service"""
        container = ServiceContainer()

        # Should raise ValueError for unregistered service
        with pytest.raises(ValueError, match="Service ITestService not registered"):
            container.get(ITestService)

    @pytest.mark.asyncio
    async def test_scoped_services(self):
        """Test scoped service lifecycle"""
        container = ServiceContainer()

        # Register scoped service
        container.register_scoped(ITestService, SimpleTestService)

        # Test within a scope
        async with container.scope("test_scope"):
            service1 = container.get(ITestService)
            service2 = container.get(ITestService)

            # Should be same instance within scope
            assert service1 is service2

        # Test in different scope
        async with container.scope("different_scope"):
            service3 = container.get(ITestService)

            # Should be different instance in different scope
            assert service1 is not service3

    def test_registration_validation(self):
        """Test service registration validation"""
        container = ServiceContainer()

        # Register services with dependencies
        container.register_singleton(
            ITestService, DependentServiceImpl
        )  # Depends on ITestDependency
        # Don't register ITestDependency

        # Validate registrations
        errors = container.validate_registrations()

        assert len(errors) == 1
        assert "depends on unregistered service" in errors[0]
        assert "ITestDependency" in errors[0]

    def test_registration_info(self):
        """Test getting registration information"""
        container = ServiceContainer()

        # Register some services
        container.register_singleton(ITestDependency, TestDependency)
        container.register_transient(ITestService, DependentServiceImpl)

        # Get registration info
        info = container.get_registration_info()

        assert "ITestDependency" in info
        assert info["ITestDependency"]["scope"] == ServiceScope.SINGLETON
        assert info["ITestDependency"]["implementation"] == "TestDependency"

        assert "ITestService" in info
        assert info["ITestService"]["scope"] == ServiceScope.TRANSIENT
        assert info["ITestService"]["implementation"] == "DependentServiceImpl"
        assert "ITestDependency" in info["ITestService"]["dependencies"]

    def test_container_clear(self):
        """Test clearing all container data"""
        container = ServiceContainer()

        # Register services
        container.register_singleton(ITestService, SimpleTestService)
        container.register_instance(ITestDependency, TestDependency())

        # Verify they exist
        assert len(container._registrations) > 0
        _ = container.get(ITestService)
        assert len(container._instances) > 0

        # Clear container
        container.clear()

        # Verify everything is cleared
        assert len(container._registrations) == 0
        assert len(container._instances) == 0
        assert len(container._scoped_instances) == 0
        assert container._current_scope is None

    def test_interface_name_to_parameter_conversion(self):
        """Test automatic conversion of interface names to parameter names"""
        container = ServiceContainer()

        # Test the private method for name conversion
        assert container._interface_to_param_name(ITestService) == "test_service"
        assert container._interface_to_param_name(ITestDependency) == "test_dependency"
        assert container._interface_to_param_name(IStorageService) == "storage_service"
        assert container._interface_to_param_name(IConfigManager) == "config_manager"

    def test_legacy_method_compatibility(self):
        """Test backward compatibility with legacy methods"""
        container = ServiceContainer()

        # Test legacy register method (should work but log warning)
        instance = SimpleTestService()
        container.register(ITestService, instance)

        # Test legacy resolve method (should work but log warning)
        service = container.resolve(ITestService)

        assert service is instance

    def test_method_chaining(self):
        """Test fluent interface with method chaining"""
        container = ServiceContainer()

        # Should be able to chain registration methods
        result = container.register_singleton(
            ITestDependency, TestDependency
        ).register_transient(ITestService, DependentServiceImpl)

        assert result is container

        # Verify both services are registered
        dependency = container.get(ITestDependency)
        service = container.get(ITestService)

        assert isinstance(dependency, TestDependency)
        assert isinstance(service, DependentServiceImpl)
        assert service.dependency is dependency


class TestServiceContainerIntegration:
    """Integration tests using real AI Signal interfaces"""

    def test_mock_services_integration(self):
        """Test integration with AI Signal mock services"""
        from tests.mocks import create_test_container

        container = create_test_container()

        # Test that all required services are registered
        storage = container.get(IStorageService)
        config = container.get(IConfigManager)
        core = container.get(ICoreService)

        assert storage is not None
        assert config is not None
        assert core is not None

        # Test that services are properly typed
        from tests.mocks import MockConfigManager, MockCoreService, MockStorageService

        assert isinstance(storage, MockStorageService)
        assert isinstance(config, MockConfigManager)
        assert isinstance(core, MockCoreService)

    @pytest.mark.asyncio
    async def test_mock_service_functionality(self):
        """Test that mock services work correctly"""
        from tests.mocks import create_test_container

        container = create_test_container()
        storage = container.get(IStorageService)

        # Create test user context
        user_context = UserContext(
            user_id="test_user",
        )

        # Test storage operations
        resources = await storage.get_resources(user_context)
        assert isinstance(resources, list)

        # Test operation result
        result = await storage.store_resources(user_context, [])
        assert isinstance(result, OperationResult)
        assert result.status == OperationStatus.SUCCESS


class TestContainerPerformance:
    """Performance tests for the service container"""

    def test_resolution_performance(self):
        """Test service resolution performance"""
        container = ServiceContainer()

        # Register many services
        for i in range(100):
            class_name = f"TestService{i}"
            interface_name = f"ITestService{i}"

            # Create dynamic interface and implementation
            interface = type(
                interface_name,
                (ABC,),
                {"__abstractmethod__": abstractmethod(lambda self: None)},
            )
            implementation = type(
                class_name,
                (),
                {
                    "__init__": lambda self: None,
                    "test_method": lambda self: f"service_{i}",
                },
            )

            container.register_singleton(interface, implementation)

        # Test resolution time (should be fast)
        import time

        start_time = time.time()

        for interface in container._registrations.keys():
            container.get(interface)

        end_time = time.time()
        resolution_time = end_time - start_time

        # Should resolve 100 services quickly (less than 1 second)
        assert resolution_time < 1.0


# Test fixtures for pytest
@pytest.fixture
def empty_container():
    """Provide an empty service container"""
    return ServiceContainer()


@pytest.fixture
def configured_container():
    """Provide a service container with test services"""
    container = ServiceContainer()
    container.register_singleton(ITestDependency, TestDependency)
    container.register_singleton(ITestService, DependentServiceImpl)
    return container


@pytest.fixture
def user_context():
    """Provide a test user context"""
    return UserContext(
        user_id="test_user",
    )


# Pytest test functions using fixtures
def test_container_with_fixture(empty_container):
    """Test using container fixture"""
    container = empty_container

    container.register_singleton(ITestService, SimpleTestService)
    service = container.get(ITestService)

    assert isinstance(service, SimpleTestService)


def test_configured_container_fixture(configured_container):
    """Test using pre-configured container fixture"""
    container = configured_container

    service = container.get(ITestService)
    assert isinstance(service, DependentServiceImpl)
    assert service.get_name() == "test_service_with_test_dependency"


@pytest.mark.asyncio
async def test_async_scope_functionality(empty_container):
    """Test async scope functionality with fixture"""
    container = empty_container
    container.register_scoped(ITestService, SimpleTestService)

    async with container.scope("test"):
        service1 = container.get(ITestService)
        service2 = container.get(ITestService)
        assert service1 is service2
