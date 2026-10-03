"""Local picture upload support for Device Maintenance cards."""

from __future__ import annotations

import base64
import binascii
from pathlib import Path
from typing import Any

import voluptuous as vol

from homeassistant.components import websocket_api
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.util import slugify

from .const import CONF_NAME, CONF_PICTURE_KEY, DOMAIN

WS_UPLOAD_PICTURE = f"{DOMAIN}/picture/upload"
WS_REMOVE_PICTURE = f"{DOMAIN}/picture/remove"

MAX_PICTURE_BYTES = 5 * 1024 * 1024
PICTURE_EXTENSIONS = ("jpeg", "jpg", "png", "webp")
PICTURE_FOLDER = "device_maintenance_card"
PICTURE_URL_PREFIX = f"/local/{PICTURE_FOLDER}/pictures"

_MIME_TO_EXTENSION = {
    "image/jpeg": "jpeg",
    "image/jpg": "jpeg",
    "image/png": "png",
    "image/webp": "webp",
}
_DATA_REGISTERED = "picture_websocket_registered"


def _picture_directory(hass: HomeAssistant) -> Path:
    """Return the Device Maintenance card picture directory."""
    return Path(hass.config.path("www", PICTURE_FOLDER, "pictures"))


def _entry_for_message(hass: HomeAssistant, entry_id: str) -> ConfigEntry:
    """Resolve and validate a Device Maintenance config entry."""
    entry = hass.config_entries.async_get_entry(entry_id)
    if entry is None or entry.domain != DOMAIN:
        raise ValueError("Device Maintenance-trackern kunde inte hittas")
    return entry


def _picture_slug(entry: ConfigEntry) -> str:
    """Return the canonical picture slug for one tracker."""
    raw_key = str(
        entry.options.get(
            CONF_PICTURE_KEY,
            entry.data.get(CONF_NAME, entry.title),
        )
        or entry.data.get(CONF_NAME, entry.title)
        or entry.title
    ).strip()
    key = slugify(raw_key)
    if not key:
        raise ValueError("Kunde inte skapa ett giltigt bildnamn för trackern")
    return key


def _validate_picture_bytes(data: bytes, extension: str) -> None:
    """Validate the minimal image signature before writing a file."""
    valid = False
    if extension == "jpeg":
        valid = data.startswith(b"\xff\xd8\xff")
    elif extension == "png":
        valid = data.startswith(b"\x89PNG\r\n\x1a\n")
    elif extension == "webp":
        valid = len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP"
    if not valid:
        raise ValueError("Bildens innehåll matchar inte filformatet")


def decode_picture(content: str, mime_type: str) -> tuple[str, bytes]:
    """Decode and validate a base64 encoded picture."""
    extension = _MIME_TO_EXTENSION.get(mime_type.lower())
    if extension is None:
        raise ValueError("Endast JPEG, PNG och WebP stöds")

    try:
        data = base64.b64decode(content, validate=True)
    except (binascii.Error, ValueError) as err:
        raise ValueError("Ogiltig bilddata") from err

    if not data:
        raise ValueError("Bildfilen är tom")
    if len(data) > MAX_PICTURE_BYTES:
        raise ValueError("Bildfilen är större än 5 MB")

    _validate_picture_bytes(data, extension)
    return extension, data


def write_picture(directory: Path, slug: str, extension: str, data: bytes) -> Path:
    """Write a picture atomically and remove stale extension variants."""
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / f"{slug}.{extension}"
    temporary = directory / f".{slug}.{extension}.tmp"

    temporary.write_bytes(data)
    temporary.replace(target)

    for candidate_extension in PICTURE_EXTENSIONS:
        candidate = directory / f"{slug}.{candidate_extension}"
        if candidate != target:
            candidate.unlink(missing_ok=True)

    return target


def remove_pictures(directory: Path, slug: str) -> list[str]:
    """Remove every supported picture variant for one tracker."""
    removed: list[str] = []
    for extension in PICTURE_EXTENSIONS:
        candidate = directory / f"{slug}.{extension}"
        if candidate.exists():
            candidate.unlink()
            removed.append(candidate.name)
    return removed


@callback
def async_setup_picture_websocket(hass: HomeAssistant) -> None:
    """Register Device Maintenance picture websocket commands once."""
    domain_data = hass.data.setdefault(DOMAIN, {})
    if domain_data.get(_DATA_REGISTERED):
        return

    websocket_api.async_register_command(hass, websocket_upload_picture)
    websocket_api.async_register_command(hass, websocket_remove_picture)
    domain_data[_DATA_REGISTERED] = True


@websocket_api.websocket_command(
    {
        vol.Required("type"): WS_UPLOAD_PICTURE,
        vol.Required("entry_id"): str,
        vol.Required("mime_type"): str,
        vol.Required("content"): str,
    }
)
@websocket_api.require_admin
@websocket_api.async_response
async def websocket_upload_picture(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Upload or replace the picture owned by one Device Maintenance tracker."""
    try:
        entry = _entry_for_message(hass, msg["entry_id"])
        slug = _picture_slug(entry)
        extension, data = decode_picture(msg["content"], msg["mime_type"])
        target = await hass.async_add_executor_job(
            write_picture,
            _picture_directory(hass),
            slug,
            extension,
            data,
        )
    except ValueError as err:
        connection.send_error(msg["id"], "invalid_picture", str(err))
        return
    except OSError as err:
        connection.send_error(msg["id"], "save_failed", str(err))
        return

    connection.send_result(
        msg["id"],
        {
            "entry_id": entry.entry_id,
            "picture_key": slug,
            "filename": target.name,
            "url": f"{PICTURE_URL_PREFIX}/{target.name}",
        },
    )


@websocket_api.websocket_command(
    {
        vol.Required("type"): WS_REMOVE_PICTURE,
        vol.Required("entry_id"): str,
    }
)
@websocket_api.require_admin
@websocket_api.async_response
async def websocket_remove_picture(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Remove the picture owned by one Device Maintenance tracker."""
    try:
        entry = _entry_for_message(hass, msg["entry_id"])
        slug = _picture_slug(entry)
        removed = await hass.async_add_executor_job(
            remove_pictures,
            _picture_directory(hass),
            slug,
        )
    except ValueError as err:
        connection.send_error(msg["id"], "invalid_picture", str(err))
        return
    except OSError as err:
        connection.send_error(msg["id"], "remove_failed", str(err))
        return

    connection.send_result(
        msg["id"],
        {
            "entry_id": entry.entry_id,
            "picture_key": slug,
            "removed": removed,
        },
    )
