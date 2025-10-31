"""
Interfaces for AI Signal Core
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Set, Union

from aisignal.core.models import OperationResult, Resource, UserContext

# =============================================================================
# RESOURCE MANAGER INTERFACE
# =============================================================================


class IResourceManager(ABC):
    """
    Interface for the ResourceManager component that manages
    a collection of Resource objects.

    Allows for adding, accessing by row key, and filtering
    based on categories or sources.
    """

    @abstractmethod
    def add_resources(self, resources: List[Resource]) -> None:
        """
        Adds new resources to the existing collection, preserving current resources.

        Args:
            resources: List of Resource objects to be added.
        """
        pass

    @abstractmethod
    def clear_row_keys(self) -> None:
        """
        Clears all entries from the row key map.
        """
        pass

    @abstractmethod
    def add_row_key(self, row_key: str, resource_index: int) -> None:
        """
        Adds a mapping between a row key and a resource index.

        Args:
            row_key: A string representing the key for a particular row.
            resource_index: An integer representing the index of the resource.
        """
        pass

    @abstractmethod
    def __getitem__(self, row_key: str) -> Resource:
        """
        Retrieves the Resource associated with the given row_key.

        Args:
            row_key: The key identifying the row whose
            associated Resource needs to be fetched.

        Returns:
            The Resource object associated with the specified row_key.

        Raises:
            KeyError: If the row_key does not exist in the row_key_map.
        """
        pass

    @abstractmethod
    def remove_resource(self, resource_id: str) -> None:
        """
        Remove resource from the list by marking it as removed.

        Args:
            resource_id: The ID of the resource to remove.
        """
        pass

    @abstractmethod
    def get_filtered_resources(
        self,
        categories: Set[str] = None,
        sources: Set[str] = None,
        sort_by_datetime: bool = False,
    ) -> List[Resource]:
        """
        Filters resources based on specified categories and sources,
        and optionally sorts them.

        Args:
            categories: A set of category names to filter resources by.
            sources: A set of source names to filter resources by.
            sort_by_datetime: If True, sort by datetime in descending order.
                             If False, sort by ranking, then datetime.

        Returns:
            A list of filtered and possibly sorted Resource objects.
        """
        pass


# =============================================================================
# CONFIG MANAGER INTERFACE
# =============================================================================


class IConfigManager(ABC):
    """
    Interface for the ConfigManager component that manages application configuration.

    Handles loading from and saving to a configuration file, specifically managing
    paths, API keys, and other application settings.
    """

    @property
    @abstractmethod
    def categories(self) -> List[str]:
        """
        Gets the list of categories from the configuration.

        Returns:
            A list of category names as strings.
        """
        pass

    @property
    @abstractmethod
    def sources(self) -> List[str]:
        """
        Retrieves the list of source strings from the configuration.

        Returns:
            A list containing the source strings as specified in the configuration.
        """
        pass

    @property
    @abstractmethod
    def content_extraction_prompt(self) -> str:
        """
        Retrieves the content extraction prompt from the configuration.

        Returns:
            The content extraction prompt as a string.
        """
        pass

    @property
    @abstractmethod
    def obsidian_vault_path(self) -> str:
        """
        Retrieves the path to the Obsidian vault as specified in the configuration.

        Returns:
            The file path to the Obsidian vault as a string.
        """
        pass

    @property
    @abstractmethod
    def obsidian_template_path(self) -> str:
        """
        Retrieves the file path for the Obsidian template.

        Returns:
            The Obsidian template path as a string.
        """
        pass

    @property
    @abstractmethod
    def openai_api_key(self) -> str:
        """
        Retrieves the OpenAI API key from the configuration.

        Returns:
            The OpenAI API key as a string.
        """
        pass

    @property
    @abstractmethod
    def jina_api_key(self) -> str:
        """
        Retrieves the Jina API key from the configuration.

        Returns:
            Jina API key as a string.
        """
        pass

    @property
    @abstractmethod
    def min_threshold(self) -> float:
        """
        Returns the minimum threshold value set in the current configuration.

        Returns:
            The minimum threshold as a float.
        """
        pass

    @property
    @abstractmethod
    def max_threshold(self) -> float:
        """
        Gets the maximum threshold value from the current configuration.

        Returns:
            The maximum threshold value as a float.
        """
        pass

    @property
    @abstractmethod
    def sync_interval(self) -> int:
        """
        Gets the sync interval value from the current configuration.

        Returns:
            The sync interval in hours as an integer.
        """
        pass

    @abstractmethod
    def save(self, new_config: dict) -> None:
        """
        Saves a new configuration by merging it with the existing configuration.

        Args:
            new_config: The new configuration values to be merged
            with the existing configuration.
        """
        pass


# =============================================================================
# CONTENT SERVICE INTERFACE
# =============================================================================


class IContentService(ABC):
    """
    Interface for the ContentService component that provides methods for fetching
    and analyzing content from URLs.
    """

    @abstractmethod
    async def fetch_content(self, url: str) -> Optional[Dict]:
        """
        Fetch content from URL and compare with stored version.

        Args:
            url: The URL to fetch content from.

        Returns:
            A dictionary containing url, title, content, and diff information.
            Returns None if fetch fails.
        """
        pass

    @abstractmethod
    async def fetch_full_content(self, url: str) -> Optional[str]:
        """
        Fetches the full content of a URL and converts it to markdown.

        Args:
            url: The URL of the content to fetch.

        Returns:
            Markdown content if successful, None otherwise.
        """
        pass

    @abstractmethod
    async def analyze_content(
        self,
        content_results: Union[Dict, List[Dict]],
        prompt_template: str,
        batch_size: int = 3500,
    ) -> Dict[str, List[Dict]]:
        """
        Analyzes content from one or multiple URLs, optimizing
        API calls through batching.

        Args:
            content_results: Single content result or list of content results
              from fetch_content.
            prompt_template: Template for the analysis prompt.
            batch_size: Maximum size of each batch in tokens.

        Returns:
            Dictionary mapping URLs to their analyzed items.
        """
        pass


# =============================================================================
# STORAGE SERVICE INTERFACE
# =============================================================================


class IStorageService(ABC):
    """
    Interfaccia per il servizio di storage di AI Signal.

    Definisce TUTTE le operazioni sui dati senza specificare COME sono implementate.
    Questo permette di cambiare da SQLite a PostgreSQL o altro senza toccare il Core.
    """

    @abstractmethod
    async def get_resources(
        self,
        user_context: UserContext,
        categories: Optional[Set[str]] = None,
        sources: Optional[Set[str]] = None,
        sort_by: str = "ranking",  # ✅ AGGIUNGI QUESTO
        sort_desc: bool = True,  # ✅ E QUESTO
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> List[Resource]:
        """
        Recupera risorse filtrate per un utente.

        Args:
            user_context: Contesto dell'utente
            categories: Set di categorie per filtrare (None = tutte)
            sources: Set di sorgenti per filtrare (None = tutte)
            sort_by: Campo per ordinamento ("ranking", "datetime", etc.)
            sort_desc: True per ordinare in descendente, False per ascendente
            limit: Numero massimo di risultati (None = illimitato)
            offset: Offset per paginazione

        Returns:
            Lista di risorse che soddisfano i filtri
        """
        pass

    @abstractmethod
    async def get_resource_by_id(
        self, user_context: UserContext, resource_id: str
    ) -> Optional[Resource]:
        """
        Recupera una risorsa specifica per ID.

        Args:
            user_context: Contesto dell'utente
            resource_id: ID univoco della risorsa

        Returns:
            Resource se trovata, None altrimenti
        """
        pass

    @abstractmethod
    async def store_resources(
        self, user_context: UserContext, resources: List[Resource]
    ) -> OperationResult:
        """
        Salva una lista di nuove risorse.

        Args:
            user_context: Contesto dell'utente
            resources: Lista di risorse da salvare

        Returns:
            OperationResult con info sul salvataggio
        """
        pass

    @abstractmethod
    async def update_resource(
        self, user_context: UserContext, resource_id: str, updates: Dict[str, Any]
    ) -> OperationResult:
        """
        Aggiorna una risorsa esistente.

        Args:
            user_context: Contesto dell'utente
            resource_id: ID della risorsa da aggiornare
            updates: Dizionario con i campi da aggiornare

        Returns:
            OperationResult con la risorsa aggiornata
        """
        pass

    @abstractmethod
    async def mark_resource_removed(
        self, user_context: UserContext, resource_id: str
    ) -> OperationResult:
        """
        Marca una risorsa come rimossa (soft delete).

        Args:
            user_context: Contesto dell'utente
            resource_id: ID della risorsa da rimuovere

        Returns:
            OperationResult con conferma rimozione
        """
        pass

    @abstractmethod
    async def get_sources_content(
        self, user_context: UserContext, url: str
    ) -> Optional[str]:
        """
        Recupera il contenuto markdown salvato per una sorgente.

        Args:
            user_context: Contesto dell'utente
            url: URL della sorgente

        Returns:
            Contenuto markdown se presente, None altrimenti
        """
        pass

    @abstractmethod
    async def store_source_content(
        self, user_context: UserContext, url: str, content: str
    ) -> OperationResult:
        """
        Salva contenuto markdown per una sorgente.

        Args:
            user_context: Contesto dell'utente
            url: URL della sorgente
            content: Contenuto markdown da salvare

        Returns:
            OperationResult con conferma salvataggio
        """
        pass

    @abstractmethod
    async def get_user_statistics(self, user_context: UserContext) -> Dict[str, Any]:
        """
        Recupera statistiche per un utente.

        Args:
            user_context: Contesto dell'utente

        Returns:
            Dizionario con statistiche utente
        """
        pass


# =============================================================================
# INTERFACCIA CORE SERVICE (semplificata)
# =============================================================================


class ICoreService(ABC):
    """
    Interfaccia per il servizio Core di AI Signal.

    Orchestratore principale che coordina tutte le operazioni di business logic.
    """

    @abstractmethod
    async def get_resources(
        self,
        user_context: UserContext,
        filters: Optional[Dict[str, Any]] = None,
        sort_by: str = "ranking",
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> List[Resource]:
        """
        Recupera risorse con filtri e ordinamento.

        Args:
            user_context: Contesto dell'utente
            filters: Filtri da applicare (categories, sources, etc.)
            sort_by: Campo per ordinamento ("ranking", "datetime", etc.)
            limit: Numero massimo risultati
            offset: Offset per paginazione

        Returns:
            Lista di risorse filtrate e ordinate
        """
        pass

    @abstractmethod
    async def get_resource_detail(
        self, user_context: UserContext, resource_id: str
    ) -> Optional[Resource]:
        """
        Recupera dettagli completi di una risorsa.

        Args:
            user_context: Contesto dell'utente
            resource_id: ID della risorsa

        Returns:
            Resource con tutti i dettagli
        """
        pass

    @abstractmethod
    async def update_resource(
        self, user_context: UserContext, resource_id: str, updates: Dict[str, Any]
    ) -> OperationResult:
        """
        Aggiorna una risorsa.

        Args:
            user_context: Contesto dell'utente
            resource_id: ID della risorsa
            updates: Aggiornamenti da applicare

        Returns:
            OperationResult con risultato
        """
        pass

    @abstractmethod
    async def remove_resource(
        self, user_context: UserContext, resource_id: str
    ) -> OperationResult:
        """
        Rimuove una risorsa.

        Args:
            user_context: Contesto dell'utente
            resource_id: ID della risorsa da rimuovere

        Returns:
            OperationResult con risultato
        """
        pass

    @abstractmethod
    async def get_statistics(self, user_context: UserContext) -> Dict[str, Any]:
        """
        Recupera statistiche per l'utente.

        Args:
            user_context: Contesto dell'utente

        Returns:
            Statistiche utente
        """
        pass
