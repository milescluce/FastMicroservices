from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from loguru import logger as log

from toomanysessions import SessionedServer
from toomanythreads import ThreadedServer

DEBUG = True
ACCEPTED_TYPES = [ThreadedServer, SessionedServer]

def check_type(self):
    type_matches = 0
    for typ in ACCEPTED_TYPES:
        if not isinstance(self, typ): continue
        type_matches = type_matches + 1
    if type_matches == 0: raise TypeError(f"Inheriting class is not one of the following: {ACCEPTED_TYPES}")

def is_sessioned_server(self: object) -> bool:
    return isinstance(self, SessionedServer)

def are_both_sessioned_server(a: object, b: object) -> bool:
    if is_sessioned_server(a) and is_sessioned_server(b): return True
    else: return False

@dataclass
class PageConfig:
    name: str
    title: str
    type: str
    cwd: Path
    obj: object
    color: Optional[str] = None  # hex color for styling
    icon: Optional[str] = None  # icon class or emoji
    auto_discovered: bool = False  # flag for auto-discovered pages


def extract_title_from_html(html_file: Path) -> Optional[str]:
    """Extract title from HTML file's <title> tag"""
    try:
        content = html_file.read_text(encoding='utf-8')
        import re
        title_match = re.search(r'<title[^>]*>(.*?)</title>', content, re.IGNORECASE | re.DOTALL)
        if title_match:
            title = title_match.group(1).strip()
            log.debug(f"Extracted title '{title}' from {html_file.name}")
            return title
    except Exception as e:
        log.debug(f"Could not extract title from {html_file.name}: {e}")
    return None


def generate_color_from_name(name: str) -> str:
    """Generate a consistent color hex code based on the page name"""
    hash_value = hash(name)
    hue = abs(hash_value) % 360
    saturation = 70
    lightness = 50

    import colorsys
    r, g, b = colorsys.hls_to_rgb(hue / 360, lightness / 100, saturation / 100)
    return f"#{int(r * 255):02x}{int(g * 255):02x}{int(b * 255):02x}"

from .microservice import Microservice
from .macroservice import Macroservice

