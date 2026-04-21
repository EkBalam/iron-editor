"""Firma HMAC-SHA256 para archivos de IronEdit."""
from __future__ import annotations
import hmac
import hashlib
import pathlib
import time


_COMMENT_MAP: dict[str, tuple[str, str] | None] = {
    ".py":   ("#", ""),   ".sh":   ("#", ""),  ".bash": ("#", ""),
    ".yml":  ("#", ""),   ".yaml": ("#", ""),  ".toml": ("#", ""),
    ".js":   ("//", ""),  ".ts":   ("//", ""), ".java": ("//", ""),
    ".c":    ("//", ""),  ".cpp":  ("//", ""), ".css":  ("//", ""),
    ".rs":   ("//", ""),
    ".html": ("<!--", "-->"), ".htm": ("<!--", "-->"), ".md": ("<!--", "-->"),
    ".sql":  ("--", ""),
    ".json": None,
}
_TAG = "IRONEDIT"


def get_comment_for_ext(ext: str) -> tuple[str, str] | None:
    """Retorna (prefix, suffix) para el comentario de firma, o None si no aplica (JSON)."""
    return _COMMENT_MAP.get(ext.lower(), ("#", ""))


def load_secret_key() -> str:
    """Carga SECRET_KEY desde ironedit.key (CWD) o ~/.ironedit.key. Fallback hardcoded."""
    candidates = [
        pathlib.Path.cwd() / "ironedit.key",
        pathlib.Path.home() / ".ironedit.key",
    ]
    for path in candidates:
        try:
            if path.is_file():
                for line in path.read_text(encoding="utf-8").splitlines():
                    line = line.strip()
                    if line.startswith("SECRET_KEY="):
                        return line[len("SECRET_KEY="):].strip()
        except OSError:
            continue
    return "ironedit-default-insecure-key"


def _compute_hmac(content: str, filename: str, timestamp: str, secret_key: str) -> str:
    message = f"{content}\n{filename}\n{timestamp}".encode("utf-8")
    return hmac.new(secret_key.encode("utf-8"), message, hashlib.sha256).hexdigest()


def sign_content(content: str, filename: str, ext: str, secret_key: str) -> str:
    """Retorna el texto completo del archivo con la firma HMAC como última línea."""
    style = get_comment_for_ext(ext)
    if style is None:
        return content

    prefix, suffix = style
    timestamp = str(int(time.time()))
    mac = _compute_hmac(content, filename, timestamp, secret_key)

    sig_line = f"{prefix} {_TAG}:{timestamp}:{mac}"
    if suffix:
        sig_line = f"{sig_line} {suffix}"

    body = content.rstrip("\n")
    return f"{body}\n{sig_line}\n"


def strip_and_verify(
    content: str, filename: str, ext: str, secret_key: str
) -> tuple[str, bool, bool]:
    """
    Retorna (clean_content, has_signature, is_valid).
    - clean_content: texto sin la línea de firma
    - has_signature: True si se encontró línea de firma
    - is_valid: True si el HMAC coincide
    JSON siempre retorna (content, True, True).
    """
    style = get_comment_for_ext(ext)
    if style is None:
        return content, True, True

    prefix, suffix = style
    lines = content.splitlines(keepends=True)
    if not lines:
        return content, False, False

    last_line = lines[-1].rstrip("\r\n")
    sig_prefix = f"{prefix} {_TAG}:"

    if not last_line.startswith(sig_prefix):
        return content, False, False

    inner = last_line[len(sig_prefix):]
    if suffix and inner.endswith(f" {suffix}"):
        inner = inner[: -len(f" {suffix}")]

    parts = inner.split(":", 1)
    if len(parts) != 2:
        return content, True, False

    timestamp, stored_mac = parts
    clean_body = "".join(lines[:-1])
    expected_mac = _compute_hmac(clean_body, filename, timestamp, secret_key)

    is_valid = hmac.compare_digest(stored_mac, expected_mac)
    return clean_body, True, is_valid
