from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from substack_api._http import DEFAULT_TIMEOUT, HEADERS, async_get, polite_request_delay

# Add Newsletter import
from .newsletter import Newsletter

async def list_all_categories() -> List[Tuple[str, int]]:
    """
    Get name / id representations of all newsletter categories

    Returns
    -------
    List[Tuple[str, int]]
        List of tuples containing (category_name, category_id)
    """
    endpoint_cat = "https://substack.com/api/v1/categories"
    r = await async_get(endpoint_cat, headers=HEADERS, timeout=DEFAULT_TIMEOUT)
    r.raise_for_status()
    categories = [(i["name"], i["id"]) for i in r.json()]
    return categories


class Category:
    """
    Top-level newsletter category
    """

    def __init__(self, name: Optional[str] = None, id: Optional[int] = None) -> None:
        """
        Initialize a Category object.

        Parameters
        ----------
        name : Optional[str]
            The name of the category
        id : Optional[int]
            The ID of the category

        Raises
        ------
        ValueError
            If neither name nor id is provided, or if the provided name/id is not found
        """
        if name is None and id is None:
            raise ValueError("Either name or id must be provided")

        self.name = name
        self.id = id
        self._newsletters_data = None  # Cache for newsletter data

    def __str__(self) -> str:
        return f"{self.name} ({self.id})"

    def __repr__(self) -> str:
        return f"Category(name={self.name}, id={self.id})"

    @classmethod
    async def create(
        cls, name: Optional[str] = None, id: Optional[int] = None
    ) -> "Category":
        category = cls(name=name, id=id)
        await category._ensure_resolved()
        return category

    async def _ensure_resolved(self) -> None:
        if self.name is not None and self.id is None:
            await self._get_id_from_name()
        elif self.id is not None and self.name is None:
            await self._get_name_from_id()

    async def _get_id_from_name(self) -> None:
        """
        Lookup category ID based on name

        Raises
        ------
        ValueError
            If the category name is not found
        """
        categories = await list_all_categories()
        for name, id in categories:
            if name == self.name:
                self.id = id
                return
        raise ValueError(f"Category name '{self.name}' not found")

    async def _get_name_from_id(self) -> None:
        """
        Lookup category name based on ID

        Raises
        ------
        ValueError
            If the category ID is not found
        """
        categories = await list_all_categories()
        for name, id in categories:
            if id == self.id:
                self.name = name
                return
        raise ValueError(f"Category ID {self.id} not found")

    async def _fetch_newsletters_data(
        self, force_refresh: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Fetch the raw newsletter data from the API and cache it

        Parameters
        ----------
        force_refresh : bool
            Whether to force a refresh of the data, ignoring the cache

        Returns
        -------
        List[Dict[str, Any]]
            Full newsletter metadata
        """
        if self._newsletters_data is not None and not force_refresh:
            return self._newsletters_data

        await self._ensure_resolved()

        endpoint = f"https://substack.com/api/v1/category/public/{self.id}/all?page="

        all_newsletters = []
        page_num = 0
        more = True
        # endpoint doesn't return more than 21 pages
        while more and page_num <= 20:
            full_url = endpoint + str(page_num)
            r = await async_get(full_url, headers=HEADERS, timeout=DEFAULT_TIMEOUT)
            r.raise_for_status()
            await polite_request_delay()

            resp = r.json()
            newsletters = resp["publications"]
            all_newsletters.extend(newsletters)
            page_num += 1
            more = resp["more"]

        self._newsletters_data = all_newsletters
        return all_newsletters

    async def get_newsletter_urls(self) -> List[str]:
        """
        Get only the URLs of newsletters in this category

        Returns
        -------
        List[str]
            List of newsletter URLs
        """
        data = await self._fetch_newsletters_data()

        return [item["base_url"] for item in data]

    async def get_newsletters(self) -> List[Newsletter]:
        """
        Get Newsletter objects for all newsletters in this category

        Returns
        -------
        List[Newsletter]
            List of Newsletter objects
        """
        urls = await self.get_newsletter_urls()
        return [Newsletter(url) for url in urls]

    async def get_newsletter_metadata(self) -> List[Dict[str, Any]]:
        """
        Get full metadata for all newsletters in this category

        Returns
        -------
        List[Dict[str, Any]]
            List of newsletter metadata dictionaries
        """
        return await self._fetch_newsletters_data()

    async def refresh_data(self) -> None:
        """
        Force refresh of the newsletter data cache
        """
        await self._fetch_newsletters_data(force_refresh=True)
