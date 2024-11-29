from pathlib import Path
from typing import Optional

from .models import Resource


class ExportManager:
    """
    Handles the export of resources into markdown files suitable for use with
    Obsidian, a personal knowledge management and note-taking software.

    :param vault_path: Path to the Obsidian vault where notes will be saved.
    :param template_path: Path to a template file, if any, used to format the
                          exported notes.
    """

    def __init__(self, vault_path: Optional[str], template_path: Optional[str]):
        self.vault_path = vault_path
        self.template_path = template_path

    def export_to_obsidian(self, resource: Resource) -> tuple[bool, str]:
        """
        :param resource: The resource object containing the information to be exported
          to an Obsidian markdown file. The resource should have `title`, `content`,
          and `url` attributes.
        :return: A tuple where the first element is a boolean indicating success or
          failure, and the second element is a string message providing more details on
          the result of the operation. If successful, the message contains the filename
          where the resource was exported. If unsuccessful, the message contains the
          error message.
        """
        if not self.vault_path:
            return False, "Obsidian vault path not configured"

        try:
            vault_path = Path(self.vault_path)
            file_path = vault_path / f"{resource.title}.md"
            template = self._get_template()

            content = template.format(
                title=resource.title, content=resource.content, url=resource.url
            )

            file_path.write_text(content)
            return True, f"Exported to: {file_path.name}"

        except Exception as e:
            return False, f"Export failed: {str(e)}"

    def _get_template(self) -> str:
        """
        Retrieves the content of a template file specified by `self.template_path`. If
        the file exists, its content is returned as a string. If the file does not
        exist, a default template string is returned.

        :return: The content of the template file if it exists, otherwise a default
          template string.
        """
        if self.template_path and Path(self.template_path).exists():
            return Path(self.template_path).read_text()
        return "# {title}\n\n{content}\n\nSource: {url}"
