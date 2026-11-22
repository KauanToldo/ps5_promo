import json
import re


def next_data(html: str) -> dict:
    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.S)
    if not m:
        raise ValueError("__NEXT_DATA__ não encontrado (layout mudou ou página bloqueada)")
    return json.loads(m.group(1))
