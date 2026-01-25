# ═══════════════════════════════════════════════════════════════════════════════
# RepoGraph AI - Video Processor
# ═══════════════════════════════════════════════════════════════════════════════
# Processor for video files (metadata extraction only)
# ═══════════════════════════════════════════════════════════════════════════════

from typing import Set

from models import Document, FileCategory, FileType, ProcessingStatus
from processors.base_processor import BaseProcessor
from utils import get_logger

logger = get_logger(__name__)


class VideoProcessor(BaseProcessor):
    """
    Processor for video files.

    Extracts metadata only (file size, path, type).
    Full video processing would require additional tools.
    """

    @property
    def supported_types(self) -> Set[FileType]:
        return {
            FileType.MP4,
            FileType.AVI,
            FileType.MOV,
            FileType.MKV,
            FileType.WEBM,
        }

    @property
    def category(self) -> FileCategory:
        return FileCategory.VIDEO

    def extract(self, document: Document) -> Document:
        """
        Extract metadata from a video file.

        Args:
            document: Document to process

        Returns:
            Document with extracted_text populated
        """
        try:
            document.status = ProcessingStatus.EXTRACTING

            # Extract basic metadata
            size_mb = document.metadata.size_bytes / (1024 * 1024)

            content = [
                f"Video File: {document.metadata.name}",
                f"Format: {document.metadata.file_type.value.upper()}",
                f"Size: {size_mb:.2f} MB",
                f"Path: {document.metadata.path}",
            ]

            # Try to extract more metadata if ffprobe is available
            extra_info = self._get_video_info(document)
            if extra_info:
                content.extend(extra_info)

            document.extracted_text = "\n".join(content)
            document.status = ProcessingStatus.COMPLETED

            logger.debug(
                "Video metadata extracted",
                file=document.metadata.name,
            )

            return document

        except Exception as e:
            document.status = ProcessingStatus.FAILED
            document.error_message = str(e)
            logger.error(f"Failed to process video: {e}")
            return document

    def _get_video_info(self, document: Document) -> list:
        """Try to get additional video info using ffprobe if available."""
        try:
            import subprocess
            import json

            result = subprocess.run(
                [
                    'ffprobe', '-v', 'quiet',
                    '-print_format', 'json',
                    '-show_format', '-show_streams',
                    str(document.metadata.path)
                ],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                data = json.loads(result.stdout)
                info = []

                # Format info
                if 'format' in data:
                    fmt = data['format']
                    if 'duration' in fmt:
                        duration = float(fmt['duration'])
                        mins = int(duration // 60)
                        secs = int(duration % 60)
                        info.append(f"Duration: {mins}:{secs:02d}")
                    if 'bit_rate' in fmt:
                        bitrate = int(fmt['bit_rate']) / 1000
                        info.append(f"Bitrate: {bitrate:.0f} kbps")

                # Stream info
                for stream in data.get('streams', []):
                    if stream['codec_type'] == 'video':
                        width = stream.get('width', 'unknown')
                        height = stream.get('height', 'unknown')
                        info.append(f"Resolution: {width}x{height}")
                        if 'codec_name' in stream:
                            info.append(f"Video codec: {stream['codec_name']}")
                    elif stream['codec_type'] == 'audio':
                        if 'codec_name' in stream:
                            info.append(f"Audio codec: {stream['codec_name']}")

                return info

        except Exception:
            pass

        return []
