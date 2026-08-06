"""Namespace-agnostic ElementTree helpers.

Gallica serves ALTO in a couple of namespace variants (ALTO v2 with the
``ns-v2#`` default namespace, occasionally no namespace at all) and SRU with the
SRW/Dublin-Core namespaces. Rather than hard-code prefixes we match on the local
tag name, which is stable across those variants.
"""

from __future__ import annotations

from typing import Iterator
from xml.etree import ElementTree as ET


def local_name(tag: str) -> str:
    """Return the tag name without its ``{namespace}`` prefix."""
    if "}" in tag:
        return tag.rsplit("}", 1)[1]
    return tag


def iter_local(elem: ET.Element, name: str) -> Iterator[ET.Element]:
    """Yield descendants (at any depth) whose local tag name equals ``name``."""
    for child in elem.iter():
        if local_name(child.tag) == name:
            yield child


def find_local(elem: ET.Element, name: str) -> "ET.Element | None":
    """Return the first descendant with local tag ``name``, or ``None``."""
    for match in iter_local(elem, name):
        return match
    return None


def first_child_local(elem: ET.Element, name: str) -> "ET.Element | None":
    """Return the first *direct* child with local tag ``name``, or ``None``."""
    for child in list(elem):
        if local_name(child.tag) == name:
            return child
    return None
