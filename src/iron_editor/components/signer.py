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


def _read_key_file_values() -> dict[str, str]:
    """Lee pares CLAVE=valor desde ironedit.key (CWD) o ~/.ironedit.key (primer archivo que exista gana)."""
    candidates = [
        pathlib.Path.cwd() / "ironedit.key",
        pathlib.Path.home() / ".ironedit.key",
    ]
    for path in candidates:
        try:
            if path.is_file():
                values: dict[str, str] = {}
                for line in path.read_text(encoding="utf-8").splitlines():
                    line = line.strip()
                    if "=" in line:
                        key, _, value = line.partition("=")
                        values[key.strip()] = value.strip()
                if values:
                    return values
        except OSError:
            continue
    return {}


def load_secret_key() -> str:
    """Carga SECRET_KEY desde ironedit.key (CWD) o ~/.ironedit.key. Fallback hardcoded."""
    return load_identity()[1]


def load_identity() -> tuple[str | None, str]:
    """Retorna (student_id, secret_key). student_id es None si no está configurado (default)."""
    values = _read_key_file_values()
    secret_key = values.get("SECRET_KEY") or "ironedit-default-insecure-key"
    student_id = values.get("STUDENT_ID") or None
    return student_id, secret_key


def save_identity(student_id: str, secret_key: str, path: pathlib.Path | None = None) -> pathlib.Path:
    """Guarda SECRET_KEY/STUDENT_ID en ~/.ironedit.key (o `path` si se indica)."""
    target = path or (pathlib.Path.home() / ".ironedit.key")
    clean_id = student_id.replace(":", "").replace("\n", "").replace("\r", "").strip()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(f"SECRET_KEY={secret_key}\nSTUDENT_ID={clean_id}\n", encoding="utf-8")
    return target


def _compute_hmac(
    content: str, filename: str, timestamp: str, secret_key: str, student_id: str | None = None
) -> str:
    if student_id:
        message = f"{content}\n{filename}\n{timestamp}\n{student_id}".encode("utf-8")
    else:
        message = f"{content}\n{filename}\n{timestamp}".encode("utf-8")
    return hmac.new(secret_key.encode("utf-8"), message, hashlib.sha256).hexdigest()


def sign_content(
    content: str, filename: str, ext: str, secret_key: str, student_id: str | None = None
) -> str:
    """Retorna el texto completo del archivo con la firma HMAC como última línea."""
    style = get_comment_for_ext(ext)
    if style is None:
        return content

    prefix, suffix = style
    timestamp = str(int(time.time()))
    body = content.rstrip("\n")
    # HMAC se computa sobre el body tal como quedará en el archivo (body + "\n"),
    # para que strip_and_verify pueda reconstruir el mismo valor desde clean_body.
    mac = _compute_hmac(f"{body}\n", filename, timestamp, secret_key, student_id)

    if student_id:
        sig_line = f"{prefix} {_TAG}:{timestamp}:{student_id}:{mac}"
    else:
        sig_line = f"{prefix} {_TAG}:{timestamp}:{mac}"
    if suffix:
        sig_line = f"{sig_line} {suffix}"

    return f"{body}\n{sig_line}\n"


def strip_and_verify(
    content: str, filename: str, ext: str, secret_key: str
) -> tuple[str, bool, bool, str | None]:
    """
    Retorna (clean_content, has_signature, is_valid, signer_id).
    - clean_content: texto sin la línea de firma
    - has_signature: True si se encontró línea de firma
    - is_valid: True si el HMAC coincide
    - signer_id: STUDENT_ID embebido en la firma, o None si es formato de 2 partes
    JSON siempre retorna (content, True, True, None).
    """
    style = get_comment_for_ext(ext)
    if style is None:
        return content, True, True, None

    prefix, suffix = style
    lines = content.splitlines(keepends=True)
    if not lines:
        return content, False, False, None

    last_line = lines[-1].rstrip("\r\n")
    sig_prefix = f"{prefix} {_TAG}:"

    if not last_line.startswith(sig_prefix):
        return content, False, False, None

    inner = last_line[len(sig_prefix):]
    if suffix and inner.endswith(f" {suffix}"):
        inner = inner[: -len(f" {suffix}")]

    parts = inner.split(":")
    clean_body = "".join(lines[:-1])

    if len(parts) == 2:
        timestamp, stored_mac = parts
        expected_mac = _compute_hmac(clean_body, filename, timestamp, secret_key)
        is_valid = hmac.compare_digest(stored_mac, expected_mac)
        return clean_body, True, is_valid, None

    if len(parts) == 3:
        timestamp, signer_id, stored_mac = parts
        expected_mac = _compute_hmac(clean_body, filename, timestamp, secret_key, signer_id)
        is_valid = hmac.compare_digest(stored_mac, expected_mac)
        return clean_body, True, is_valid, signer_id

    return content, True, False, None
