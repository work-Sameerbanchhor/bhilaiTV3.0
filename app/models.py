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
    upstream_url: Optional[str] = None

class SearchResponse(BaseModel):
    results: List[ReleaseItem]
    total_count: int
    total_pages: int
    current_page: int
    query: Optional[str] = None
