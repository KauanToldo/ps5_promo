# Monitor de preço do PS5 Slim Digital

Roda sozinho no GitHub Actions e avisa por WhatsApp quando o PS5 Slim **Digital**, novo, fica com
preço **<= R$ 3.800** (limite configurável).

> **Status:** Fase 1 (lojas online). Fase 2 (lojas físicas via Instagram/Facebook) só depois da validação.

## Relatório honesto das fontes (testado em 22/11/2026, do IP residencial)

| Fonte | Estado | Observação |
|---|---|---|
| Zoom | ✅ funciona | Agregador (Magalu, Amazon, KaBuM etc.). Preço de vitrine: não diz se é Pix ou parcelado. |
| Buscapé | ✅ funciona | Mesma plataforma/dados do Zoom (redundância). |
| KaBuM! | ✅ funciona | Preço à vista (com desconto) e cheio separados. |
| Havan | ❌ não viável simples | Resultados carregados por JavaScript. Exigiria Playwright. |
| Mercado Livre | ❌ bloqueado | API de busca devolve 403 e o HTML redireciona para login. |
| Amazon, Shopee, AliExpress | ❌ não tentadas | Bloqueiam IP de datacenter (GitHub Actions). Cobertas só via Zoom/Buscapé quando listadas. |
| Americanas, Casas Bahia, Ponto, Fast Shop, Carrefour, Submarino, Magalu | 🟡 indireto | Aparecem via Zoom/Buscapé; sem módulo próprio ainda. |
| Girafa | ❌ sem resposta | Conexão falhou no teste. |
| Nuuvem / PlayStation Store | ➖ n/a | Não vendem o console. |

**Importante:** os testes acima foram do seu IP. Do GitHub Actions (IP de datacenter) o resultado
pode ser diferente: valide no primeiro run (workflow_dispatch) e olhe o log.

**Frete: ainda NÃO calculado.** Nenhum módulo calcula frete para o seu CEP; todo alerta sai com
"frete não calculado" e o gatilho usa só o preço do produto (como a SPEC prevê). O CEP já está
previsto como Secret (`CEP`) para quando implementarmos o cálculo por loja.

## Rodar localmente

```bash
pip install -r requirements.txt
python -m pytest            # testes
python main.py --dry-run    # consulta as lojas e mostra o que seria enviado (não envia, não grava)
python main.py --test-notify  # envia mensagem de teste (precisa dos segredos abaixo)
```

## Configuração (passo a passo)

1. **Repositório:** crie um repositório **público** no GitHub e suba este projeto
   (nenhum segredo está no código).
2. **WhatsApp (CallMeBot, grátis):**
   - Salve o número do bot (divulgado na página oficial quando há vaga) e envie: `I allow callmebot to send me messages`
     (confira as instruções atuais em https://www.callmebot.com/blog/free-api-whatsapp-messages/).
   - Você recebe uma **apikey**. Se o bot estiver lotado, use a alternativa Telegram (a ser adicionada).
3. **Secrets** (Settings → Secrets and variables → Actions → *Secrets*):
   - `CALLMEBOT_PHONE`: seu número com DDI, ex. `5549999999999`
   - `CALLMEBOT_APIKEY`: a apikey recebida
   - `CEP`: seu CEP (reservado para o cálculo de frete)
4. **Limite de preço:** edite `limite_preco` em `config.yaml` ou crie a *Variable* `LIMITE_PRECO`.
5. **Ligar:** Actions → "Monitor PS5" → *Run workflow*. Depois o cron roda a cada 30 min.
6. **Filtros:** palavras incluir/excluir, vendedores confiáveis e preço suspeito ficam em `config.yaml`.

## Como funciona

- `sources/`: um módulo por fonte (`fetch()`), com timeout e retry com backoff. Falha em uma
  fonte não derruba as outras.
- `filters.py`: só aceita PS5 Slim Digital; rejeita usado, disco, Pro, acessórios, pré-venda etc.
  Preço abaixo de R$ 2.500 não é descartado: sai marcado **SUSPEITO**.
- `storage.py`: estado em `state.json` na branch `state`. Anti-spam: mesmo anúncio+preço só 1x/24h,
  preço menor reenvia na hora, heartbeat semanal, aviso único se uma fonte falhar por 3+ dias.
- `notifier/`: camada abstrata (`Notifier`); hoje CallMeBot. Para Telegram/e-mail, crie outra subclasse.

## Frequência e custo

Repositório público: minutos do Actions **ilimitados**. Cada execução leva ~30-60 s. (Em repositório
privado seriam ~48 runs/dia x ~1 min = ~1.440 min/mês, dentro dos 2.000 do plano free, mas apertado.)
O cron do Actions pode atrasar vários minutos. Workflows agendados são desativados após 60 dias
sem atividade: o commit do estado na branch `state` a cada execução mantém o repositório ativo.

## Risco de perder o estado

Se a branch `state` for apagada, o monitor recomeça sem histórico: no pior caso repete um alerta.
