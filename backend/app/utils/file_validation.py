"""File validation and security utilities for anonymous evidence uploads."""

import os
import re
from typing import Tuple

# Maximum allowed file size: 10 MB
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024

# Strictly allowed extensions
ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".pdf", ".txt"}

# Strictly allowed MIME types
ALLOWED_MIME_TYPES = {
    "image/png": {".png"},
    "image/jpeg": {".jpg", ".jpeg"},
    "image/webp": {".webp"},
    "application/pdf": {".pdf"},
    "text/plain": {".txt"},
}

# Dangerous executable / script extensions to explicitly block
DISALLOWED_EXTENSIONS = {
    ".exe", ".bat", ".cmd", ".ps1", ".sh", ".bash", ".zsh",
    ".js", ".jsx", ".ts", ".tsx", ".py", ".pyc", ".pyd",
    ".php", ".phtml", ".asp", ".aspx", ".jsp", ".cgi",
    ".svg", ".html", ".htm", ".xhtml", ".xml",
    ".dll", ".so", ".dylib", ".vbs", ".wsf", ".scr",
    ".com", ".msi", ".jar", ".class",
}


class FileValidationError(ValueError):
    """Raised when an uploaded evidence file fails security or format validation."""
    pass


def sanitize_filename(filename: str) -> str:
    """Sanitize original filename to eliminate directory traversal and control characters."""
    # Extract only the base name (prevents directory traversal e.g. ../../../etc/passwd)
    clean_name = os.path.basename(filename).strip()
    # Replace any spaces or suspicious characters with underscores
    clean_name = re.sub(r"[^a-zA-Z0-9.\-_]", "_", clean_name)
    # Remove leading dots to prevent hidden files
    clean_name = clean_name.lstrip(".")
    if not clean_name:
        clean_name = "evidence_file"
    # Truncate length if excessively long
    if len(clean_name) > 100:
        base, ext = os.path.splitext(clean_name)
        clean_name = f"{base[:90]}{ext}"
    return clean_name


def validate_magic_bytes(header: bytes, ext: str, mime: str) -> bool:
    """Verify file magic numbers/signatures for allowed binary formats."""
    if ext == ".png" or mime == "image/png":
        return header.startswith(b"\x89PNG\r\n\x1a\n")

    if ext in {".jpg", ".jpeg"} or mime == "image/jpeg":
        return header.startswith(b"\xff\xd8\xff")

    if ext == ".pdf" or mime == "application/pdf":
        return header.startswith(b"%PDF-")

    if ext == ".webp" or mime == "image/webp":
        return len(header) >= 12 and header.startswith(b"RIFF") and header[8:12] == b"WEBP"

    if ext == ".txt" or mime == "text/plain":
        # Text files must not contain null bytes (binary indicator)
        if b"\x00" in header:
            return False
        try:
            header.decode("utf-8")
            return True
        except UnicodeDecodeError:
            try:
                header.decode("latin-1")
                return True
            except UnicodeDecodeError:
                return False

    return False


def validate_evidence_file(
    filename: str,
    content_type: str,
    file_bytes: bytes,
) -> Tuple[str, str, int]:
    """Validate uploaded file size, extension, MIME type, and magic bytes.

    Returns:
        (sanitized_filename, validated_mime_type, file_size)

    Raises:
        FileValidationError: If the file fails any security check.
    """
    if not filename or not filename.strip():
        raise FileValidationError("Uploaded file must have a valid filename.")

    file_size = len(file_bytes)
    if file_size == 0:
        raise FileValidationError("Uploaded file is empty (0 bytes).")

    if file_size > MAX_FILE_SIZE_BYTES:
        raise FileValidationError(
            f"File size ({file_size / (1024 * 1024):.1f} MB) exceeds maximum allowed limit of 10 MB."
        )

    # Validate extension
    _, ext = os.path.splitext(filename.lower())
    if ext in DISALLOWED_EXTENSIONS:
        raise FileValidationError(
            f"File extension '{ext}' is prohibited for security reasons."
        )

    if ext not in ALLOWED_EXTENSIONS:
        allowed_list = ", ".join(sorted(ALLOWED_EXTENSIONS))
        raise FileValidationError(
            f"Unsupported file format '{ext}'. Allowed extensions are: [{allowed_list}]."
        )

    # Validate MIME type
    clean_mime = content_type.lower().split(";")[0].strip()
    if clean_mime not in ALLOWED_MIME_TYPES:
        allowed_mimes = ", ".join(sorted(ALLOWED_MIME_TYPES.keys()))
        raise FileValidationError(
            f"Unsupported content type '{clean_mime}'. Allowed MIME types are: [{allowed_mimes}]."
        )

    # Verify extension matches declared MIME type
    if ext not in ALLOWED_MIME_TYPES[clean_mime]:
        raise FileValidationError(
            f"File extension '{ext}' does not match Content-Type '{clean_mime}'."
        )

    # Validate magic bytes header (inspect first 512 bytes)
    header = file_bytes[:512]
    if not validate_magic_bytes(header, ext, clean_mime):
        raise FileValidationError(
            f"File signature/content does not match declared type '{ext}'."
        )

    safe_name = sanitize_filename(filename)
    return safe_name, clean_mime, file_size
