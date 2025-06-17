"""
Migration helper utilities for AI Signal Core architecture migration.

This module provides utilities to assist in the migration from legacy
monolithic architecture to the new Core architecture.
"""

import ast
import inspect
from pathlib import Path
from typing import Dict, List, Type

from aisignal.core.interfaces import IConfigManager, IContentService, IResourceManager


class MigrationAnalyzer:
    """
    Analyzer for tracking migration progress and finding legacy dependencies.
    """

    def __init__(self, project_root: Path = None):
        """
        Initialize migration analyzer.

        Args:
            project_root: Root directory of the project (defaults to src/aisignal)
        """
        self.project_root = (
            project_root or Path(__file__).parent.parent / "src" / "aisignal"
        )
        self.legacy_classes = {
            "ConfigManager": "aisignal.core.config",
            "ResourceManager": "aisignal.core.resource_manager",
            "ContentService": "aisignal.core.services.content_service",
        }

    def scan_legacy_dependencies(self) -> Dict[str, List[str]]:
        """
        Scan codebase for files that import legacy classes directly.

        Returns:
            Dictionary mapping legacy class names to files that import them
        """
        dependencies = {cls: [] for cls in self.legacy_classes.keys()}

        for py_file in self.project_root.rglob("*.py"):
            try:
                with open(py_file, "r", encoding="utf-8") as f:
                    content = f.read()

                tree = ast.parse(content)

                for node in ast.walk(tree):
                    if isinstance(node, ast.ImportFrom):
                        if node.module in self.legacy_classes.values():
                            # Check which classes are imported
                            for alias in node.names:
                                if alias.name in self.legacy_classes:
                                    relative_path = py_file.relative_to(
                                        self.project_root
                                    )
                                    dependencies[alias.name].append(str(relative_path))

                    elif isinstance(node, ast.Import):
                        for alias in node.names:
                            for legacy_class, module in self.legacy_classes.items():
                                if module in alias.name:
                                    relative_path = py_file.relative_to(
                                        self.project_root
                                    )
                                    dependencies[legacy_class].append(
                                        str(relative_path)
                                    )

            except (SyntaxError, UnicodeDecodeError):
                # Skip files that can't be parsed
                continue

        return dependencies

    def analyze_interface_compliance(self) -> Dict[str, Dict[str, bool]]:
        """
        Analyze which services properly implement Core interfaces.

        Returns:
            Dictionary showing compliance status for each service
        """
        from aisignal.core.adapters.config_adapter import ConfigManagerAdapter
        from aisignal.core.adapters.content_adapter import ContentServiceAdapter
        from aisignal.core.adapters.resource_adapter import ResourceManagerAdapter

        adapters = {
            "ConfigManagerAdapter": (ConfigManagerAdapter, IConfigManager),
            "ResourceManagerAdapter": (ResourceManagerAdapter, IResourceManager),
            "ContentServiceAdapter": (ContentServiceAdapter, IContentService),
        }

        compliance = {}

        for adapter_name, (adapter_class, interface_class) in adapters.items():
            compliance[adapter_name] = self._check_interface_compliance(
                adapter_class, interface_class
            )

        return compliance

    def _check_interface_compliance(
        self, impl_class: Type, interface_class: Type
    ) -> Dict[str, bool]:
        """
        Check if implementation class properly implements interface.

        Args:
            impl_class: Implementation class to check
            interface_class: Interface class to check against

        Returns:
            Dictionary showing compliance details
        """
        compliance = {
            "implements_interface": False,
            "has_all_methods": False,
            "method_signatures_match": False,
            "missing_methods": [],
            "signature_mismatches": [],
        }

        # Check if class implements interface
        try:
            compliance["implements_interface"] = issubclass(impl_class, interface_class)
        except TypeError:
            compliance["implements_interface"] = False

        # Get interface methods
        interface_methods = {
            name: method
            for name, method in inspect.getmembers(interface_class)
            if inspect.isfunction(method) or inspect.ismethod(method)
        }

        # Get implementation methods
        impl_methods = {
            name: method
            for name, method in inspect.getmembers(impl_class)
            if inspect.isfunction(method) or inspect.ismethod(method)
        }

        # Check for missing methods
        missing = set(interface_methods.keys()) - set(impl_methods.keys())
        compliance["missing_methods"] = list(missing)
        compliance["has_all_methods"] = len(missing) == 0

        # Check method signatures (simplified check)
        signature_mismatches = []
        for method_name in interface_methods:
            if method_name in impl_methods:
                try:
                    interface_sig = inspect.signature(interface_methods[method_name])
                    impl_sig = inspect.signature(impl_methods[method_name])

                    if interface_sig != impl_sig:
                        signature_mismatches.append(method_name)
                except (ValueError, TypeError):
                    # Skip methods that can't be introspected
                    pass

        compliance["signature_mismatches"] = signature_mismatches
        compliance["method_signatures_match"] = len(signature_mismatches) == 0

        return compliance

    def generate_migration_report(self) -> str:
        """
        Generate comprehensive migration status report.

        Returns:
            Formatted migration report as string
        """
        dependencies = self.scan_legacy_dependencies()
        compliance = self.analyze_interface_compliance()

        report = []
        report.append("=" * 60)
        report.append("AI SIGNAL MIGRATION STATUS REPORT")
        report.append("=" * 60)

        # Legacy Dependencies Section
        report.append("\n📊 LEGACY DEPENDENCIES ANALYSIS")
        report.append("-" * 40)

        total_files_with_deps = sum(len(files) for files in dependencies.values())

        if total_files_with_deps == 0:
            report.append("✅ No direct legacy dependencies found!")
        else:
            report.append(
                f"⚠️  Found {total_files_with_deps} files with legacy dependencies:"
            )

            for legacy_class, files in dependencies.items():
                if files:
                    report.append(f"\n📁 {legacy_class} ({len(files)} files):")
                    for file in files:
                        report.append(f"   - {file}")

        # Interface Compliance Section
        report.append("\n🔍 INTERFACE COMPLIANCE ANALYSIS")
        report.append("-" * 40)

        for adapter_name, compliance_info in compliance.items():
            report.append(f"\n🔧 {adapter_name}:")

            status_icon = "✅" if compliance_info["implements_interface"] else "❌"
            report.append(
                f"   {status_icon} Implements interface:"
                f"{compliance_info['implements_interface']}"
            )

            status_icon = "✅" if compliance_info["has_all_methods"] else "❌"
            report.append(
                f"   {status_icon} Has all methods: "
                f"{compliance_info['has_all_methods']}"
            )

            if compliance_info["missing_methods"]:
                report.append(
                    "   ❌ Missing methods: "
                    f"{', '.join(compliance_info['missing_methods'])}"
                )

            status_icon = "✅" if compliance_info["method_signatures_match"] else "⚠️"
            report.append(
                f"   {status_icon} Method signatures match: "
                f"{compliance_info['method_signatures_match']}"
            )

            if compliance_info["signature_mismatches"]:
                report.append(
                    "   ⚠️  Signature mismatches: "
                    f"{', '.join(compliance_info['signature_mismatches'])}"
                )

        # Migration Progress Summary
        report.append("\n📈 MIGRATION PROGRESS SUMMARY")
        report.append("-" * 40)

        # Calculate progress metrics
        total_adapters = len(compliance)
        compliant_adapters = sum(
            1
            for info in compliance.values()
            if info["implements_interface"] and info["has_all_methods"]
        )

        adapter_progress = (
            (compliant_adapters / total_adapters * 100) if total_adapters > 0 else 0
        )

        dependency_progress = 100 if total_files_with_deps == 0 else 0

        overall_progress = (adapter_progress + dependency_progress) / 2

        report.append(
            f"🎯 Adapter Compliance: {adapter_progress:.1f}% "
            f"({compliant_adapters}/{total_adapters})"
        )
        report.append(f"🧹 Dependency Cleanup: {dependency_progress:.1f}%")
        report.append(f"📊 Overall Progress: {overall_progress:.1f}%")

        # Next Steps
        report.append("\n🚀 NEXT STEPS")
        report.append("-" * 40)

        if total_files_with_deps > 0:
            report.append("1. ❗ Fix legacy dependencies in UI files")
            report.append("2. 🔄 Refactor direct imports to use DI container")

        if compliant_adapters < total_adapters:
            report.append("3. 🔧 Fix adapter interface compliance issues")

        if overall_progress < 100:
            report.append("4. ✅ Complete Week 1 foundation tasks")
            report.append("5. 🏗️  Begin Week 2 Core service implementation")
        else:
            report.append("🎉 Week 1 foundation complete - ready for Week 2!")

        report.append("\n" + "=" * 60)

        return "\n".join(report)


class InterfaceValidator:
    """
    Utility for validating interface implementations.
    """

    @staticmethod
    def validate_service_registration(container, interface_class: Type) -> bool:
        """
        Validate that a service is properly registered and resolvable.

        Args:
            container: ServiceContainer instance
            interface_class: Interface class to validate

        Returns:
            True if service is properly registered and resolvable
        """
        try:
            service = container.get(interface_class)
            return service is not None and isinstance(service, interface_class)
        except Exception:
            return False

    @staticmethod
    def validate_all_core_services(container) -> Dict[str, bool]:
        """
        Validate all core services are properly registered.

        Args:
            container: ServiceContainer instance

        Returns:
            Dictionary mapping service names to validation status
        """
        core_interfaces = {
            "IConfigManager": IConfigManager,
            "IResourceManager": IResourceManager,
            "IContentService": IContentService,
        }

        results = {}
        for name, interface in core_interfaces.items():
            results[name] = InterfaceValidator.validate_service_registration(
                container, interface
            )

        return results


def print_migration_report():
    """Command-line utility to print migration report."""
    analyzer = MigrationAnalyzer()
    report = analyzer.generate_migration_report()
    print(report)


if __name__ == "__main__":
    print_migration_report()
