from localprices import classify, extract_prices, parse_post_date

L = 3800


def test_preco_a_vista_e_parcelado():
    p = extract_prices("PS5 Slim Digital R$ 3.799 à vista ou 12x de R$ 349")
    assert p[0].value == 3799 and p[0].payment == "à vista"


def test_pix():
    assert extract_prices("PlayStation 5 Slim Digital 3.699,00 no Pix")[0].payment == "Pix"


def test_alerta_alta_digital_abaixo_do_limite():
    prio, price, _ = classify("Promoção PS5 Slim Digital por R$ 3.799 à vista", L)
    assert prio == "alta" and price.value == 3799


def test_ignora_acima_do_limite_disco_pro_usado_e_jogos():
    for t in ["PS5 Slim Digital R$ 4.599,00", "PS5 Slim com leitor de disco R$ 3.500",
              "PS5 Pro digital R$ 3.500", "PS5 Slim Digital usado R$ 3.000",
              "Jogo God of War para PS5 R$ 249"]:
        assert classify(t, L) is None, t


def test_sem_preco_vira_verificar():
    prio, price, warns = classify("Queima de estoque PS5! Vem conferir", L)
    assert prio == "verificar" and price is None and "VERIFICAR NA LOJA" in warns[0]


def test_datas_do_google():
    assert parse_post_date("29 de out. de 2026").day == 29
    assert parse_post_date("há 3 dias") is not None
    assert parse_post_date(None) is None
