import re
import logging
from urllib.parse import urlparse
from typing import List, Optional, Set

logger = logging.getLogger("bhilaitv.domain_registry")

DEFAULT_HUBCLOUD_DOMAINS = [
    "hubcloud.ist",
    "hubcloud.fans",
    "hubcloud.club",
    "hubcloud.cx",
    "hubcloud.lol",
    "hubcloud.vip"
]

DEFAULT_GDFLIX_DOMAINS = [
    "gdflix.dev",
    "new4.gdflix.io",
    "new5.gdflix.io",
    "new3.gdflix.io",
    "gdflix.io",
    "gdflix.cfd"
]

HUBCLOUD_PATTERN = re.compile(r"https?://(?:[a-zA-Z0-9-]+\.)*hubcloud\.[a-z]+", re.IGNORECASE)
HUBCLOUD_ID_PATTERN = re.compile(r"/(?:drive|tg|file)/([a-zA-Z0-9_-]+)", re.IGNORECASE)

GDFLIX_PATTERN = re.compile(r"https?://(?:[a-zA-Z0-9-]+\.)*gdflix\.[a-z]+", re.IGNORECASE)
GDFLIX_ID_PATTERN = re.compile(r"/file/([a-zA-Z0-9_-]+)", re.IGNORECASE)

TELEGRAM_PATTERN = re.compile(r"https?://(?:t\.me|telegram\.me|(?:[a-zA-Z0-9-]+\.)*hubcloud\.[a-z]+/tg)", re.IGNORECASE)

class DomainRegistry:
    """
    Dynamically tracks, discovers, and auto-heals domains for HubCloud, GDFlix,
    and CDN mirrors. When upstream releases publish new domain patterns or when
    existing mirrors go down, the registry dynamically prioritizes working domains
    and fails over seamlessly.
    """

    def __init__(self):
        self._hubcloud_domains: List[str] = list(DEFAULT_HUBCLOUD_DOMAINS)
        self._gdflix_domains: List[str] = list(DEFAULT_GDFLIX_DOMAINS)
        self._active_hubcloud_domain: str = self._hubcloud_domains[0]
        self._active_gdflix_domain: str = self._gdflix_domains[0]
        self._failed_domains: Set[str] = set()

    def is_hubcloud(self, url: str) -> bool:
        if not url:
            return False
        return bool(HUBCLOUD_PATTERN.search(url))

    def is_gdflix(self, url: str) -> bool:
        if not url:
            return False
        return bool(GDFLIX_PATTERN.search(url))

    def is_telegram(self, url: str) -> bool:
        if not url:
            return False
        return bool(TELEGRAM_PATTERN.search(url))

    def extract_hubcloud_id(self, url: str) -> Optional[str]:
        if not url:
            return None
        m = HUBCLOUD_ID_PATTERN.search(url)
        return m.group(1) if m else None

    def extract_gdflix_id(self, url: str) -> Optional[str]:
        if not url:
            return None
        m = GDFLIX_ID_PATTERN.search(url)
        return m.group(1) if m else None

    def _extract_host(self, url: str) -> Optional[str]:
        try:
            if not url.startswith("http"):
                url = "https://" + url
            parsed = urlparse(url)
            return parsed.netloc.lower().split(":")[0]
        except Exception:
            return None

    def learn_url(self, url: str) -> None:
        """
        Dynamically inspects URLs encountered in upstream posts/pages and registers
        new working domains into the active candidate list in real-time.
        """
        if not url:
            return

        host = self._extract_host(url)
        if not host:
            return

        if self.is_hubcloud(url):
            if host not in self._hubcloud_domains:
                logger.info(f"Discovered new HubCloud domain pattern: {host}")
                self._hubcloud_domains.insert(0, host)
            self._active_hubcloud_domain = host
            self._failed_domains.discard(host)

        elif self.is_gdflix(url):
            if host not in self._gdflix_domains:
                logger.info(f"Discovered new GDFlix domain pattern: {host}")
                self._gdflix_domains.insert(0, host)
            self._active_gdflix_domain = host
            self._failed_domains.discard(host)

    def mark_hubcloud_success(self, url_or_domain: str) -> None:
        """Promotes the successful domain to primary rank."""
        host = self._extract_host(url_or_domain) or url_or_domain
        self._failed_domains.discard(host)
        if host in self._hubcloud_domains:
            self._hubcloud_domains.remove(host)
        self._hubcloud_domains.insert(0, host)
        self._active_hubcloud_domain = host
        logger.info(f"HubCloud active primary domain confirmed: {host}")

    def mark_gdflix_success(self, url_or_domain: str) -> None:
        """Promotes the successful GDFlix domain to primary rank."""
        host = self._extract_host(url_or_domain) or url_or_domain
        self._failed_domains.discard(host)
        if host in self._gdflix_domains:
            self._gdflix_domains.remove(host)
        self._gdflix_domains.insert(0, host)
        self._active_gdflix_domain = host
        logger.info(f"GDFlix active primary domain confirmed: {host}")

    def mark_domain_failed(self, domain_or_url: str) -> None:
        """Records a domain failure and deprioritizes it."""
        host = self._extract_host(domain_or_url) or domain_or_url
        self._failed_domains.add(host)
        if host in self._hubcloud_domains and len(self._hubcloud_domains) > 1:
            self._hubcloud_domains.remove(host)
            self._hubcloud_domains.append(host)
            if self._active_hubcloud_domain == host:
                self._active_hubcloud_domain = self._hubcloud_domains[0]
            logger.warning(f"Deprioritized dead HubCloud domain {host}. New active: {self._active_hubcloud_domain}")

        if host in self._gdflix_domains and len(self._gdflix_domains) > 1:
            self._gdflix_domains.remove(host)
            self._gdflix_domains.append(host)
            if self._active_gdflix_domain == host:
                self._active_gdflix_domain = self._gdflix_domains[0]
            logger.warning(f"Deprioritized dead GDFlix domain {host}. New active: {self._active_gdflix_domain}")

    def get_hubcloud_candidate_urls(self, input_url: str) -> List[str]:
        """
        Builds an ordered list of candidate URLs for a HubCloud resource.
        Tries unfailed candidates first, with input URL prioritized if not failed.
        """
        drive_id = self.extract_hubcloud_id(input_url)
        input_host = self._extract_host(input_url)

        candidates = []
        seen_urls = set()

        # 1. If input host has not failed, try it first
        if input_host and input_host not in self._failed_domains:
            candidates.append(input_url)
            seen_urls.add(input_url)

        # 2. Add candidates synthesized from known domain pool
        if drive_id:
            for domain in self._hubcloud_domains:
                candidate_url = f"https://{domain}/drive/{drive_id}"
                if candidate_url not in seen_urls:
                    candidates.append(candidate_url)
                    seen_urls.add(candidate_url)

        # 3. If input host was failed, ensure it's still available as last resort
        if input_url not in seen_urls:
            candidates.append(input_url)
            seen_urls.add(input_url)

        return candidates

    def get_gdflix_candidate_urls(self, input_url: str) -> List[str]:
        """
        Builds an ordered list of candidate URLs for a GDFlix resource.
        Tries unfailed candidates first, with input URL prioritized if not failed.
        """
        file_id = self.extract_gdflix_id(input_url)
        input_host = self._extract_host(input_url)

        candidates = []
        seen_urls = set()

        # 1. If input host has not failed, try it first
        if input_host and input_host not in self._failed_domains:
            candidates.append(input_url)
            seen_urls.add(input_url)

        # 2. Add candidates synthesized from known domain pool
        if file_id:
            for domain in self._gdflix_domains:
                candidate_url = f"https://{domain}/file/{file_id}"
                if candidate_url not in seen_urls:
                    candidates.append(candidate_url)
                    seen_urls.add(candidate_url)

        # 3. If input host was failed, still append as last resort
        if input_url not in seen_urls:
            candidates.append(input_url)
            seen_urls.add(input_url)

        return candidates

# Global singleton
domain_registry = DomainRegistry()
