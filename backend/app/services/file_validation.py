FILE_SIGNATURES = {
    "image/jpeg": (b"\xff\xd8\xff",),
    "image/png": (b"\x89PNG\r\n\x1a\n",),
    "image/webp": (b"RIFF", b"WEBP"),
    "application/pdf": (b"%PDF-",),
}

HEIF_BRANDS = {b"heic", b"heix", b"hevc", b"hevx", b"mif1", b"msf1"}


def has_valid_file_signature(file_bytes, mime_type):
    if mime_type in {"image/heic", "image/heif"}:
        return (
            len(file_bytes) >= 12
            and file_bytes[4:8] == b"ftyp"
            and file_bytes[8:12] in HEIF_BRANDS
        )

    signatures = FILE_SIGNATURES.get(mime_type)
    if signatures is None:
        return True
    if mime_type == "image/webp":
        return len(file_bytes) >= 12 and file_bytes.startswith(b"RIFF") and file_bytes[8:12] == b"WEBP"
    return any(file_bytes.startswith(signature) for signature in signatures)
