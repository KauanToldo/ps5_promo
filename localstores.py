"""Lista automática de lojas físicas (Google Maps via Serper) -> lojas_locais.yaml."""
from __future__ import annotations

import math
import re
from pathlib import Path

import yaml

from filters import normalize
from serper import Serper

HOME = (-27.2342, -52.0278)  # Concórdia - SC (centro)
CITIES = {
    "Concórdia - SC": (-27.2342, -52.0278),
    "Chapecó - SC": (-27.1004, -52.6153),
    "Erechim - RS": (-27.6340, -52.2737),
}
QUERIES = ["loja de videogames", "loja de eletrodomésticos e eletrônicos",
           "loja de informática", "loja de celulares e eletrônicos"]
SKIP = re.compile(r"conserto|assistencia|materiais eletricos|lan house|software ?key|atacado|picole|"
                  r"sorvete|key|refrigera|brinquedo|antena|clickcare|purific|discos|troca tela|"
                  r"speed redes|plexus|imagem digital|distribuidora|automacao|seguranca|som, luz")
BAD_HANDLES = {"popular", "explore", "p", "reel", "reels", "share", "accounts", "stories", "tv"}
CHAINS = ("havan", "colombo", "benoit", "berlanda", "magazine", "casas bahia", "fast shop",
          "carrefour", "americanas", "bahamas", "lojas cem", "koerich", "quero-quero")


def km(a: tuple[float, float], b: tuple[float, float]) -> float:
    """Distância em linha reta (haversine)."""
    la1, lo1, la2, lo2 = map(math.radians, (*a, *b))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 6371 * 2 * math.asin(math.sqrt(h))


def profile(url: str | None, host: str) -> str | None:
    """Normaliza URL de perfil (ignora posts, reels e links de compartilhamento)."""
    if not url or host not in url:
        return None
    m = re.search(rf"{host}/([A-Za-z0-9_.]+)", url)
    if not m or m.group(1).lower() in BAD_HANDLES | {"sharer", "profile.php", "pages", "people"}:
        return None
    return f"https://www.{host}/{m.group(1)}"


def refresh(serper: Serper, path: str = "lojas_locais.yaml", enrich: bool = True) -> list[dict]:
    found: dict[str, dict] = {}
    for city, (lat, lng) in CITIES.items():
        name = city.split(" - ")[0]
        for q in QUERIES:
            for p in serper.maps(q, lat, lng):
                addr = p.get("address") or ""
                title = p.get("title", "").strip()
                if normalize(name) not in normalize(addr) or SKIP.search(normalize(title)):
                    continue  # fora da cidade ou irrelevante
                key = f"{normalize(title)}|{normalize(addr)}"
                site = p.get("website")
                found.setdefault(key, {
                    "nome": title, "cidade": city, "endereco": addr, "site": site,
                    "instagram": profile(site, "instagram.com"),
                    "facebook": profile(site, "facebook.com"),
                    "telefone": p.get("phoneNumber"),
                    "rede": any(c in normalize(title) for c in CHAINS),
                    "distancia_km": round(km(HOME, (p["latitude"], p["longitude"])), 1)
                    if p.get("latitude") else None,
                    "ativa": True,
                })
    stores = list(found.values())
    if enrich:  # tenta achar o perfil de quem não informou link de rede social
        for s in stores:
            if s["instagram"] or s["facebook"]:
                continue
            first = normalize(s["nome"]).split()[0]
            for r in serper.search(f'site:instagram.com "{s["nome"]}" {s["cidade"].split(" - ")[0]}', num=5):
                prof = profile(r.get("link"), "instagram.com")
                if prof and first in normalize((r.get("title") or "") + (r.get("snippet") or "") + prof):
                    s["instagram"] = prof
                    break
    for s in stores:
        s["sem_perfil_publico"] = not (s["instagram"] or s["facebook"])
    stores.sort(key=lambda s: (s["cidade"], s["nome"]))
    Path(path).write_text(
        "# Lojas físicas monitoradas (gerado por `python main.py --refresh-stores`).\n"
        "# Revise: coloque `ativa: false` para ignorar uma loja, ou edite os perfis.\n"
        + yaml.safe_dump({"lojas": stores}, allow_unicode=True, sort_keys=False), encoding="utf8")
    return stores


def load(path: str = "lojas_locais.yaml") -> list[dict]:
    return yaml.safe_load(Path(path).read_text(encoding="utf8"))["lojas"]
