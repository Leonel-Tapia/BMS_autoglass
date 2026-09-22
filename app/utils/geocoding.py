import os
import time
import requests
from typing import Optional, Tuple
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / ".env")

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"

# User-Agent identificable (Nominatim lo exige con un contacto real)
HEADERS = {
    "User-Agent": "BMSAutoglass/1.0 (contact: leo@BMS Autoglass.us)"
}

_last_request_time = 0


def _nominatim_request(params: dict) -> Optional[dict]:
    """Petición a Nominatim respetando el rate limit de 1 req/seg."""
    global _last_request_time
    elapsed = time.time() - _last_request_time
    if elapsed < 1.0:
        time.sleep(1.0 - elapsed)

    try:
        response = requests.get(NOMINATIM_URL, params=params, headers=HEADERS, timeout=15)
        _last_request_time = time.time()

        if response.status_code == 200:
            data = response.json()
            return data[0] if data else None
        else:
            print(f"Nominatim HTTP {response.status_code}: {response.text[:200]}")
            return None
    except Exception as e:
        print(f"Error conexión Nominatim: {e}")
        return None


def geocode_address(address: str) -> Optional[Tuple[float, float]]:
    """
    Convierte una dirección en coordenadas (lat, lng) usando Nominatim.
    Intenta varias variantes para maximizar la tasa de éxito.
    """
    if not address:
        return None

    # Intento 1: dirección tal cual viene (con Unit, Apt, etc.)
    result = _nominatim_request({
        "q": address,
        "format": "jsonv2",
        "limit": 1
    })
    if result:
        return float(result["lat"]), float(result["lon"])

    print(f"Intento 1 falló para '{address}', probando variantes...")

    # Intento 2: quitar "Unit XX" / "Apt XX" / "#XX" (suelen confundir al parser)
    clean_address = address
    for marker in [" Unit ", " Apt ", " Ste ", " #"]:
        if marker in clean_address:
            parts = clean_address.split(",")
            parts[0] = parts[0].split(marker)[0]
            clean_address = ",".join(parts)
            break

    if clean_address != address:
        result = _nominatim_request({
            "q": clean_address,
            "format": "jsonv2",
            "limit": 1
        })
        if result:
            print(f"  ✓ Intento 2 (sin Unit/Apt) funcionó: {clean_address}")
            return float(result["lat"]), float(result["lon"])

    # Intento 3: solo calle + ciudad + estado (sin ZIP)
    parts = clean_address.split(",")
    if len(parts) >= 3:
        simple_address = f"{parts[0].strip()}, {parts[1].strip()}, {parts[2].strip()}"
        result = _nominatim_request({
            "q": simple_address,
            "format": "jsonv2",
            "limit": 1
        })
        if result:
            print(f"  ✓ Intento 3 (sin ZIP) funcionó: {simple_address}")
            return float(result["lat"]), float(result["lon"])

    print(f"  ✗ No se pudo geocodificar: {address}")
    return None