from pathlib import Path
from typing import Optional
from .models import Resource


class ExportManager:
    """
    ExportManager manages the export of resources to an Obsidian vault.

    :param vault_path: Optional path to the Obsidian vault.
    :param template_path: Optional path to the template file.

    export_to_obsidian exports a given resource to the Obsidian vault.

    :param resource: The Resource object containing the title, content, and URL to be exported.
    :return: A tuple where the first element is a boolean indicating success and the second element is a message.

    _get_template retrieves the template for exporting resources.

    :return: The template string from the provided template path or a default template.
    """
    def __init__(self, vault_path: Optional[str], template_path: Optional[str]):
        self.vault_path = vault_path
        self.template_path = template_path

    def export_to_obsidian(self, resource: Resource) -> tuple[bool, str]:
        """
        :param resource: The Resource object containing the title, content, and URL to be exported.
        :return: A tuple where the first element is a boolean indicating success and the second element is a message.
        """
        if not self.vault_path:
            return False, "Obsidian vault path not configured"

        try:
            vault_path = Path(self.vault_path)
            file_path = vault_path / f"{resource.title}.md"
            template = self._get_template()

            content = template.format(
                title=resource.title,
                content=resource.content,
                url=resource.url
            )

            file_path.write_text(content)
            return True, f"Exported to: {file_path.name}"

        except Exception as e:
            return False, f"Export failed: {str(e)}"

    def _get_template(self) -> str:
        """
        :return: A string containing the template text from the specified template path,
                 or a default template string with placeholders for title, content, and URL if the template path does not exist.
        """
        if self.template_path and Path(self.template_path).exists():
            return Path(self.template_path).read_text()
        return "# {title}\n\n{content}\n\nSource: {url}"