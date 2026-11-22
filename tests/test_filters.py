import pytest
import yaml

from filters import apply_rules, title_ok
from models import Offer

CFG = yaml.safe_load(open("config.yaml", encoding="utf8"))


@pytest.mark.parametrize("t", [
    "Console Sony PlayStation 5 Edição Digital Slim, SSD 825GB, Controle DualSense",
    "Playstation 5 Slim Edição Digital 1TB",
    "Console PS5 Slim Digital 1TB Branco",
])
def test_titulos_validos(t):
    assert title_ok(t, CFG["filtros"])


@pytest.mark.parametrize("t", [
    "Leitor de Disco Para Playstation 5 Slim, PS5 Pro Sony, Edição digital",
    "Suporte Triplo Playstation 5 Slim Ps5 Disco Digital Base Apoio",
    "Capa de Proteção Antipoeira Para Playstation 5 Slim Digital",
    "Console PlayStation 5 Pro 2TB Digital",
    "Console PlayStation 5 Slim com Leitor de Disco",
    "Console PS5 Slim Digital Usado",
    "Console PS5 Slim Digital Seminovo",
    "Console PlayStation 4 Slim 1TB",
    "Jogo God of War para PS5",
    "Playstation 5 Fat Digital 825GB",
    "Console PS5 Slim Digital - Pré-venda",
    "Controle DualSense PS5 Slim Digital",
])
def test_titulos_invalidos(t):
    assert not title_ok(t, CFG["filtros"])


def mk(price, title="Console PS5 Slim Digital", store="KaBuM!", url="https://x/p", **kw):
    return Offer(source="t", store=store, title=title, url=url, price_cash=price, **kw)


def test_preco_suspeito_e_frete_aviso():
    o = apply_rules(mk(2000), CFG)
    assert any("SUSPEITO" in w for w in o.warnings)
    assert "frete não calculado" in o.warnings


def test_vendedor_desconhecido_rejeitado():
    assert apply_rules(mk(3000, store="LojaXpto", seller="LojaXpto"), CFG) is None


def test_pre_venda_no_link_rejeitada():
    assert apply_rules(mk(3000, url="https://z/pre-venda-ps5-slim"), CFG) is None


def test_sem_estoque_rejeitado():
    assert apply_rules(mk(3000, in_stock=False), CFG) is None
