# ═══════════════════════════════════════════════════════════════════════════════
# RepoGraph AI - Vision Service
# ═══════════════════════════════════════════════════════════════════════════════
# Google Vision API integration for image and diagram analysis.
# ═══════════════════════════════════════════════════════════════════════════════

import base64
import httpx
from pathlib import Path
from typing import Optional, Dict, Any

from interfaces import IVisionAnalyzer
from models import Document, ProcessingStatus
from config import get_google_vision_settings
from utils import get_logger

logger = get_logger(__name__)


class GoogleVisionService(IVisionAnalyzer):
    """
    Google Vision API integration for image analysis.

    Uses the REST API with API key authentication for:
    - OCR text extraction
    - Label detection
    - Object detection
    - Document text extraction
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Vision service.

        Args:
            api_key: Google Vision API key (or from settings)
        """
        settings = get_google_vision_settings()
        self.api_key = api_key or settings.vision_api_key
        self.base_url = "https://vision.googleapis.com/v1/images:annotate"

        if not self.api_key:
            logger.warning("Google Vision API key not configured")

    def analyze_image(self, image_path: Path) -> str:
        """
        Analyze an image and extract comprehensive description.

        Combines OCR, label detection, and object detection.

        Args:
            image_path: Path to the image file

        Returns:
            Comprehensive textual description
        """
        if not self.api_key:
            return self._fallback_description(image_path)

        try:
            # Read and encode image
            image_data = self._encode_image(image_path)

            # Make API request with multiple features
            response = self._call_vision_api(image_data, [
                {"type": "TEXT_DETECTION"},
                {"type": "LABEL_DETECTION", "maxResults": 10},
                {"type": "OBJECT_LOCALIZATION", "maxResults": 10},
            ])

            # Parse response
            return self._parse_analysis_response(response, image_path)

        except Exception as e:
            logger.error(f"Vision analysis failed: {e}")
            return self._fallback_description(image_path)

    def extract_text_from_image(self, image_path: Path) -> str:
        """
        Perform OCR on an image to extract text.

        Args:
            image_path: Path to the image file

        Returns:
            Extracted text
        """
        if not self.api_key:
            return ""

        try:
            image_data = self._encode_image(image_path)

            response = self._call_vision_api(image_data, [
                {"type": "DOCUMENT_TEXT_DETECTION"},
            ])

            # Extract text from response
            if response and 'responses' in response:
                first_response = response['responses'][0]
                if 'fullTextAnnotation' in first_response:
                    return first_response['fullTextAnnotation']['text']
                elif 'textAnnotations' in first_response:
                    return first_response['textAnnotations'][0].get('description', '')

            return ""

        except Exception as e:
            logger.error(f"OCR extraction failed: {e}")
            return ""

    def analyze_document(self, document: Document) -> Document:
        """
        Analyze a document's image/diagram content.

        Args:
            document: Document to analyze

        Returns:
            Document with vision_analysis populated
        """
        try:
            image_path = document.metadata.path

            # Check if it's an image type that needs vision analysis
            if document.metadata.category.value in ('image', 'diagram'):
                document.status = ProcessingStatus.ANALYZING

                analysis = self.analyze_image(image_path)
                document.vision_analysis = analysis

                # Combine with any existing extracted text
                if document.extracted_text:
                    document.extracted_text = f"{document.extracted_text}\n\n--- Vision Analysis ---\n{analysis}"
                else:
                    document.extracted_text = analysis

                logger.info(
                    "Vision analysis complete",
                    file=document.metadata.name,
                    analysis_length=len(analysis),
                )

            return document

        except Exception as e:
            logger.error(f"Document vision analysis failed: {e}")
            document.error_message = str(e)
            return document

    def _encode_image(self, image_path: Path) -> str:
        """Encode image as base64."""
        with open(image_path, 'rb') as f:
            return base64.b64encode(f.read()).decode('utf-8')

    def _call_vision_api(self, image_data: str, features: list) -> Dict[str, Any]:
        """Call Google Vision API."""
        url = f"{self.base_url}?key={self.api_key}"

        payload = {
            "requests": [{
                "image": {"content": image_data},
                "features": features
            }]
        }

        with httpx.Client(timeout=60) as client:
            response = client.post(url, json=payload)
            response.raise_for_status()
            return response.json()

    def _parse_analysis_response(self, response: Dict[str, Any], image_path: Path) -> str:
        """Parse Vision API response into readable text."""
        parts = [f"Image Analysis: {image_path.name}\n"]

        if not response or 'responses' not in response:
            return parts[0] + "No analysis available."

        result = response['responses'][0]

        # Extract text (OCR)
        if 'textAnnotations' in result:
            text = result['textAnnotations'][0].get('description', '')
            if text.strip():
                parts.append("=== Extracted Text ===")
                parts.append(text.strip()[:2000])  # Limit text length
                parts.append("")

        # Extract labels
        if 'labelAnnotations' in result:
            labels = [f"{l['description']} ({l['score']:.1%})"
                     for l in result['labelAnnotations']]
            if labels:
                parts.append("=== Detected Labels ===")
                parts.append(", ".join(labels))
                parts.append("")

        # Extract objects
        if 'localizedObjectAnnotations' in result:
            objects = [f"{o['name']} ({o['score']:.1%})"
                      for o in result['localizedObjectAnnotations']]
            if objects:
                parts.append("=== Detected Objects ===")
                parts.append(", ".join(objects))
                parts.append("")

        return "\n".join(parts)

    def _fallback_description(self, image_path: Path) -> str:
        """Generate fallback description when API is not available."""
        try:
            from PIL import Image

            with Image.open(image_path) as img:
                width, height = img.size
                mode = img.mode
                format_type = img.format

            return (
                f"Image: {image_path.name}\n"
                f"Dimensions: {width}x{height}\n"
                f"Format: {format_type}\n"
                f"Mode: {mode}\n"
                f"(Vision API analysis not available)"
            )
        except Exception:
            return f"Image: {image_path.name}\n(Analysis not available)"
