# Monitor de preço do PS5 Slim Digital

Roda sozinho no GitHub Actions e avisa por e-mail (ou WhatsApp) quando o PS5 Slim **Digital**, novo, fica com
preço **<= R$ 3.800** (limite configurável).

> **Status:** Fase 1 (lojas online). Fase 2 (lojas físicas via Instagram/Facebook) só depois da validação.

## Relatório honesto das fontes (testado em 22/11/2026, do IP residencial)

| Fonte | Estado | Observação |
|---|---|---|
| Zoom / Buscapé | ✅ funciona | Agregadores (Magalu, Amazon, KaBuM etc.). Preço de vitrine: não distingue Pix de parcelado. |
| KaBuM! | ✅ funciona | Preço à vista (com desconto) e cheio separados. |
| Amazon | ✅ via Playwright | `requests` é barrado por bot-check; usa navegador headless. Vendedor (Amazon x terceiro) não é verificado: aviso no alerta. Importados ("International") são excluídos. |
| Havan | ✅ via Playwright | Só lista PS5 com disco hoje; o filtro descarta. Funciona quando aparecer o Digital. |
| AliExpress | ✅ via Playwright (melhor esforço) | Resultados dominados por acessórios. Todo alerta leva aviso de importação/terceiro. |
| Terabyte Shop | ✅ funciona | Vende o console, hoje esgotado (sem preço). Detecta quando voltar ao estoque. |
| Pichau | ❌ bloqueada | 403 até com navegador real; não vamos contornar. |
| Mercado Livre | ⏸ desativado | API oficial implementada, mas sem credenciais | HTML e API pública bloqueados (403/verificação). Com `ML_CLIENT_ID`/`ML_CLIENT_SECRET` usa a API; só loja oficial ou reputação verde. Sem credenciais é pulado. |
| Magalu (direto) | ❌ bloqueado | 403 até com navegador real; coberto só via Zoom/Buscapé. |
| Shopee | ❌ não tentada | Anti-bot agressivo. |
| Americanas, Casas Bahia, Ponto, Fast Shop, Carrefour, Submarino | 🟡 indireto | Aparecem via Zoom/Buscapé quando listados. |
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
playwright install chromium   # Amazon, Havan, AliExpress
python -m pytest            # testes
python main.py --dry-run    # consulta as lojas e mostra o que seria enviado (não envia, não grava)
python main.py --test-notify  # envia mensagem de teste (precisa dos segredos abaixo)
```

## Configuração (passo a passo)

1. **Repositório:** crie um repositório **público** no GitHub e suba este projeto
   (nenhum segredo está no código).
2. **E-mail (Resend, grátis, 100 e-mails/dia):**
   - Crie conta em https://resend.com com o e-mail que vai **receber** os alertas.
   - Em *API Keys*, crie uma chave (permissão de envio).
   - Sem domínio próprio, o remetente padrão `onboarding@resend.dev` só envia para o e-mail da
     própria conta Resend, o que basta aqui.
3. **Secrets** (Settings → Secrets and variables → Actions → *Secrets*):
   - `RESEND_API_KEY`: a chave criada
   - `EMAIL_TO`: o e-mail da conta Resend
   - `CEP`: seu CEP (reservado para o cálculo de frete)
   - (opcional) Mercado Livre: `ML_CLIENT_ID` e `ML_CLIENT_SECRET` (app em developers.mercadolivre.com.br)
   - (opcional) WhatsApp: `NOTIFIER=whatsapp` + `CALLMEBOT_PHONE` + `CALLMEBOT_APIKEY`
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
- `notifier/`: camada abstrata (`Notifier`); e-mail via Resend (padrão) e WhatsApp via CallMeBot (opcional). Para Telegram/e-mail, crie outra subclasse.

## Frequência e custo

Repositório público: minutos do Actions **ilimitados**. Cada execução leva ~30-60 s. (Em repositório
privado seriam ~48 runs/dia x ~1 min = ~1.440 min/mês, dentro dos 2.000 do plano free, mas apertado.)
O cron do Actions pode atrasar vários minutos. Workflows agendados são desativados após 60 dias
sem atividade: o commit do estado na branch `state` a cada execução mantém o repositório ativo.

## Risco de perder o estado

Se a branch `state` for apagada, o monitor recomeça sem histórico: no pior caso repete um alerta.
