"""Gallica (BnF) extraction of Le Temps daily financial quotations.

The pipeline follows a *locate-with-text, read-from-image* principle:

1. Search the SRU API (CQL) to find the Le Temps issue for a given date and
   filter on the ``ocrquality`` index so only good scans are processed.
2. Fetch the ALTO XML for a page: word-level bounding boxes for every OCR'd token.
3. Locate a target number by its text anchor (e.g. a label or the rente row) and
   read the bounding box of the value token(s).
4. Scale the ALTO coordinates into the IIIF image space and build a crop URL.
5. Extract the value from the cropped image (OCR), rather than trusting the raw
   full-text OCR.

Every network boundary is behind :class:`gallica_le_temps.client.GallicaClient`
so the pure logic (query building, parsing, coordinate math) is unit-testable
against fixtures without touching the network.
"""

from .alto import WordBox, parse_alto
from .config import RunConfig, TargetSpec, load_config
from .iiif import PixelRegion, crop_url, scale_region
from .sru import IssueRecord, build_issue_query, parse_sru_response

__all__ = [
    "WordBox",
    "parse_alto",
    "RunConfig",
    "TargetSpec",
    "load_config",
    "PixelRegion",
    "crop_url",
    "scale_region",
    "IssueRecord",
    "build_issue_query",
    "parse_sru_response",
]

__version__ = "0.1.0"
