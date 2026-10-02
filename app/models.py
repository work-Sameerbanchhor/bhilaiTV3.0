from typing import List, Optional
from pydantic import BaseModel, Field

class ParsedTitleInfo(BaseModel):
    clean_title: str
    year: Optional[str] = None
    season: Optional[str] = None
    audio: Optional[str] = None
    quality: Optional[str] = None
    size: Optional[str] = None
    is_series: bool = False

class ReleaseItem(BaseModel):
    id: int
    raw_title: str
    parsed: ParsedTitleInfo
    date: str
    slug: str
    url: str
    poster_url: Optional[str] = None

class LockerLink(BaseModel):
    provider: str
    url: str
    label: str
    is_primary: bool = False
    badge: str = "DEFAULT"

class ResolutionGroup(BaseModel):
    quality: str
    size: Optional[str] = None
    links: List[LockerLink] = Field(default_factory=list)

class EpisodeGroup(BaseModel):
    episode_num: int
    title: str
    links: List[LockerLink] = Field(default_factory=list)

class SeriesQualitySibling(BaseModel):
    post_id: int
    quality: str
    size: Optional[str] = None
    is_current: bool = False

class ReleaseDetail(BaseModel):
    id: int
    raw_title: str
    parsed: ParsedTitleInfo
    date: str
    slug: str
    url: str
    release_type: str  # "movie" or "series"
    resolutions: List[ResolutionGroup] = Field(default_factory=list)
    episodes: List[EpisodeGroup] = Field(default_factory=list)
    sibling_qualities: List[SeriesQualitySibling] = Field(default_factory=list)
    poster_url: Optional[str] = None
    upstream_url: Optional[str] = None

class SearchResponse(BaseModel):
    results: List[ReleaseItem]
    total_count: int
    total_pages: int
    current_page: int
    query: Optional[str] = None

class CatalogSnapshot(BaseModel):
    generated_at: float
    iso_date: str
    total_count: int
    total_pages: int
    pages_cached: int
    items_per_page: int
    releases: List[ReleaseItem]

class SnapshotStatus(BaseModel):
    ready: bool
    total_items: int = 0
    pages_cached: int = 0
    total_upstream_items: int = 0
    total_upstream_pages: int = 0
    generated_at: Optional[float] = None
    iso_date: Optional[str] = None
    age_seconds: Optional[float] = None
    storage_backend: str = "none"
    is_syncing: bool = False
