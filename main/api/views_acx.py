"""
Proxy backend vers l'API ACX (plateforme de recouvrement ACREMAC).
Toutes les requêtes transitent par le serveur Django — aucune dépendance
côté navigateur (pas de CORS, pas de localStorage, pas de token exposé).
"""

import threading
import time

import requests
from django.conf import settings
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

# ── Configuration ─────────────────────────────────────────────────────────────
ACX_API      = getattr(settings, "ACX_API_URL",          "https://acx-acremac.net/api").rstrip("/")
ACX_USERNAME = getattr(settings, "ACX_SERVICE_USERNAME", "")
ACX_PASSWORD = getattr(settings, "ACX_SERVICE_PASSWORD", "")

_ACX_CONFIGURED = bool(ACX_USERNAME and ACX_PASSWORD)

# ── Cache token en mémoire (thread-safe) ──────────────────────────────────────
_token_cache = {"access": None, "expires_at": 0.0}
_token_lock  = threading.Lock()


def _fetch_new_token() -> str | None:
    """Authentifie le compte de service ACX et retourne le token d'accès."""
    try:
        r = requests.post(
            f"{ACX_API}/auth/token/",
            json={"username": ACX_USERNAME, "password": ACX_PASSWORD},
            timeout=10,
        )
        r.raise_for_status()
        return r.json().get("access")
    except Exception:
        return None


def _get_token() -> str | None:
    """Retourne le token valide (cache 4 min), ou en obtient un nouveau."""
    if not _ACX_CONFIGURED:
        return None
    with _token_lock:
        if _token_cache["access"] and time.time() < _token_cache["expires_at"]:
            return _token_cache["access"]
        token = _fetch_new_token()
        if token:
            _token_cache["access"]     = token
            _token_cache["expires_at"] = time.time() + 240  # 4 min
        return token


def _acx_get(path: str, params: dict) -> list:
    """Appel GET authentifié à l'API ACX avec retry automatique sur 401."""
    token = _get_token()
    if not token:
        return []

    headers = {"Authorization": f"Bearer {token}"}
    url = f"{ACX_API}{path}"

    try:
        r = requests.get(url, params=params, headers=headers, timeout=10)

        # Token expiré → on force un refresh et on réessaie une fois
        if r.status_code == 401:
            with _token_lock:
                _token_cache["access"]     = None
                _token_cache["expires_at"] = 0.0
            token = _get_token()
            if not token:
                return []
            headers = {"Authorization": f"Bearer {token}"}
            r = requests.get(url, params=params, headers=headers, timeout=10)

        if not r.ok:
            return []

        data = r.json()
        return data if isinstance(data, list) else data.get("results", [])

    except requests.Timeout:
        return []
    except Exception:
        return []


# ── Endpoint Django ────────────────────────────────────────────────────────────

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def acx_search(request):
    """
    GET /api/acx/search/?q=<nom>
    Recherche les débiteurs et dossiers similaires dans ACX.
    Authentification : compte de service configuré en settings.
    """
    if not _ACX_CONFIGURED:
        return Response(
            {
                "configured": False,
                "debtors": [],
                "cases": [],
                "message": (
                    "Le compte de service ACX n'est pas configuré. "
                    "Renseignez ACX_SERVICE_USERNAME et ACX_SERVICE_PASSWORD "
                    "dans les variables d'environnement."
                ),
            },
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    q = request.GET.get("q", "").strip()
    if not q:
        return Response({"configured": True, "debtors": [], "cases": []})

    # Appels parallèles débiteurs + dossiers
    results = {"debtors": [], "cases": []}

    def _load(key, path):
        results[key] = _acx_get(path, {"q": q})

    threads = [
        threading.Thread(target=_load, args=("debtors", "/debtors/")),
        threading.Thread(target=_load, args=("cases",   "/cases/")),
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=12)

    return Response({
        "configured": True,
        "q": q,
        "debtors": results["debtors"],
        "cases":   results["cases"],
    })
