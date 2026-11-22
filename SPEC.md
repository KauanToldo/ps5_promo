# OBJETIVO

Construa um monitor automático de preços do PlayStation 5 SLIM VERSÃO DIGITAL (sem leitor de disco), NOVO e lacrado, que rode sozinho no GitHub Actions e me avise por WhatsApp quando o preço final (produto + frete para a minha região) for MENOR OU IGUAL a R$ 3.800,00.

Responda sempre em português do Brasil (código em inglês, comentários e README em português).

# CONTEXTO

- Moro em Concórdia - SC (peça-me o CEP exato antes de implementar o cálculo de frete).
- O preço limite (R$ 3.800) é o preço FINAL: valor do produto + frete para o meu CEP. Se uma loja não permitir calcular o frete sem login, registre "frete não calculado" e avise mesmo assim quando o preço do produto sozinho já for <= R$ 3.800, deixando isso claro no alerta.
- Execução: GitHub Actions com cron (agendado), sem servidor próprio.
- Notificação: WhatsApp.

# ANTES DE CODAR

1. Apresente um plano curto (arquitetura, fontes, lista de riscos) e espere minha confirmação.
2. Pesquise e me diga honestamente quais fontes são viáveis em GitHub Actions. IPs de datacenter costumam ser bloqueados por Amazon, Mercado Livre, Shopee, AliExpress etc. Para cada fonte, escolha a melhor estratégia, nesta ordem de preferência:
   a) API oficial ou feed/RSS, se existir e for gratuito;
   b) agregadores de preço e promoção (ex.: Zoom, Buscapé, Promobit, Pelando), que listam várias lojas de uma vez;
   c) scraping HTML simples com requests e parser;
   d) navegador headless (Playwright) apenas se não houver alternativa.
   Se uma fonte não for viável, diga isso claramente em vez de fingir que funciona.

# FASE 1: LOJAS ONLINE (implementar primeiro)

Cobrir no mínimo: Mercado Livre, Amazon Brasil, Magazine Luiza, Havan, Shopee, AliExpress, Americanas, Casas Bahia, Ponto, Kabum, Fast Shop, Carrefour, Submarino, Girafa e Nuuvem/PlayStation Store se houver o console. Também lojas menores e especializadas em games do Brasil (pesquise quais existem e sugira a lista para eu aprovar).

Regras de filtragem (muito importante, para evitar falsos alertas):
- Aceitar apenas: console PS5 Slim, edição Digital, novo.
- Rejeitar: usado/seminovo/recondicionado, versão com disco, PS5 fat/antigo, PS5 Pro, controles, jogos, capas, bases, suportes, kits de acessórios, anúncios "somente caixa/peça", e anúncios de "reserva/pré-venda" sem estoque.
- Validar o título com palavras-chave (incluir/excluir) configuráveis em arquivo.
- Marketplaces (Mercado Livre, Shopee, AliExpress, Amazon seller terceiro): exigir loja oficial OU vendedor com boa reputação (configurável). No AliExpress, considerar impostos de importação e prazo, e sinalizar no alerta.
- Preços suspeitos (ex.: abaixo de R$ 2.500) não devem ser descartados: marque como "SUSPEITO, verifique se não é golpe ou erro de preço" no alerta.
- Considerar o preço no Pix/à vista e o parcelado separadamente; o alerta deve mostrar qual é qual. O gatilho usa o menor preço à vista real.

# FASE 2: LOJAS FÍSICAS (Instagram e Facebook)

(Implementar depois que a Fase 1 estiver funcionando. Cada fonte deve ser um módulo "plugin" com a mesma interface da Fase 1.)

Objetivo: encontrar promoções de PS5 Slim Digital, novo, com preço <= R$ 3.800 válidas em lojas físicas, monitorando APENAS os perfis de Instagram e Facebook das lojas. Não usar encartes nem folhetos.

## Cidades cobertas
- Concórdia - SC
- Chapecó - SC
- Erechim - RS (atenção: é Rio Grande do Sul)

## Montagem da lista de lojas (automática)
1. Pesquise no Google (via ferramentas de busca disponíveis) lojas físicas que vendam consoles e games, eletrodomésticos, eletrônicos e informática nas três cidades. Inclua redes grandes com filial na região (ex.: Havan, Magazine Luiza, Casas Bahia, Fast Shop, Americanas, Carrefour, Bahamas, Lojas Cem, Koerich etc., confirmando quais realmente têm loja nas cidades) e lojas locais e independentes, inclusive lojas especializadas em games.
2. Para cada loja encontrada, registre em `lojas_locais.yaml`: nome, cidade/UF, endereço, site, URL do Instagram, URL do Facebook e telefone/WhatsApp se disponível. Marque as que não têm perfil público.
3. Mostre-me a lista gerada para eu revisar (remover ou adicionar lojas) antes de ativar o monitoramento.
4. Faça um comando de atualização da lista (`--refresh-stores`) para eu rodar de vez em quando.

## Coleta nas redes sociais
Seja realista: Instagram e Facebook bloqueiam scraping, principalmente a partir de IPs do GitHub Actions. Pesquise e me apresente as alternativas viáveis, com custo, estabilidade e risco de cada uma, por exemplo:
- RSS-Bridge ou serviços equivalentes;
- buscas do Google com `site:instagram.com` / `site:facebook.com` e palavras-chave (PS5, Playstation 5, PS5 Slim, digital, promoção);
- serviços gratuitos ou com plano free (ex.: Apify, se houver actor público viável);
- páginas públicas do Facebook acessíveis sem login.
Não use contas pessoais minhas nem tente burlar login ou captcha. Se a coleta direta não for viável, diga claramente e proponha a melhor alternativa de "melhor esforço".

## Detecção
- Procurar nos posts e legendas recentes (ex.: últimos 7 dias) termos como: PS5, PlayStation 5, Playstation 5 Slim, console digital, oferta, promoção, queima de estoque.
- Extrair o preço do texto (formatos "R$ 3.799", "3799,00", "3.799 à vista", "12x de..." etc.). Se o preço estiver só na imagem, avaliar OCR (ex.: Tesseract) como etapa opcional e sinalizar a confiança da leitura.
- Só alertar se: for o PS5 Slim DIGITAL, novo, e o preço extraído for <= R$ 3.800. Se o post citar PS5 sem preço legível, ou não deixar claro se é digital ou com disco, envie um alerta de menor prioridade marcado "VERIFICAR NA LOJA".
- Como o preço é de loja física, não há frete: compare o valor direto com R$ 3.800.

## Alerta de loja física (WhatsApp)
Deve começar com "PROMOÇÃO EM LOJA FÍSICA" e conter: nome da loja, cidade/UF, preço, condição de pagamento (à vista, Pix, parcelado), validade da promoção se informada, link do post, data da postagem, e um aviso "confirme preço e estoque com a loja antes de ir" (e a distância ou cidade, já que Chapecó e Erechim ficam fora de Concórdia). Aplicar a mesma deduplicação da Fase 1 (não repetir o mesmo post).

# NOTIFICAÇÃO POR WHATSAPP

Pesquise e proponha a melhor forma gratuita de enviar WhatsApp a partir do GitHub Actions para o meu próprio número (ex.: CallMeBot, Twilio sandbox, WhatsApp Cloud API), com prós e contras de cada uma (custo, limites, estabilidade, risco de banimento). Implemente a que eu escolher. Deixe a camada de notificação abstrata para eu poder trocar de provedor ou adicionar Telegram/e-mail depois.

Mensagem do alerta (curta e clara):
- loja, nome do produto, preço, frete, TOTAL, forma de pagamento, link direto, data/hora da coleta, e avisos (suspeito, importação, vendedor terceiro, frete não calculado).

Regras anti-spam:
- Não reenviar o mesmo alerta (mesma loja, mesmo anúncio e mesmo preço) mais de uma vez por 24h.
- Reenviar imediatamente se o preço cair ainda mais.
- Enviar uma mensagem de "heartbeat" semanal ("monitor ativo, menor preço da semana: X na loja Y") para eu saber que está funcionando.
- Se uma fonte ficar falhando por vários dias, avise-me uma vez, sem spam.

# ARQUITETURA E QUALIDADE

- Linguagem: Python 3.12 (a menos que você justifique outra).
- Estrutura sugerida: `sources/` (um módulo por loja), `filters.py`, `notifier/`, `storage.py`, `config.yaml`, `lojas_locais.yaml`, `main.py`, `tests/`, `.github/workflows/monitor.yml`, `README.md`.
- Cada fonte deve ter timeout, retry com backoff e tratamento de erro independente: uma loja caindo NUNCA pode derrubar as outras.
- Persistência: guarde histórico de preços e alertas já enviados em um arquivo (JSON/CSV/SQLite) versionado em uma branch dedicada ou usando cache/artefatos do Actions. Explique a escolha e o risco de perder o estado.
- Segredos (token WhatsApp, número, CEP) só em GitHub Secrets, nunca no código.
- Respeitar robots.txt e termos de uso quando possível, com delays e User-Agent educado. Sem tentar burlar captchas ou proteções agressivas.
- Logs claros em cada execução, com resumo: quantas lojas consultadas, quantas falharam, menor preço encontrado.
- Testes unitários para os filtros (títulos válidos e inválidos), para a extração de preço de textos de posts e para a lógica de preço + frete + deduplicação.
- Frequência: calcule o consumo de minutos do GitHub Actions (repo público vs privado) e sugira a frequência ideal (ex.: a cada 30 min). Avise sobre as limitações do cron (atrasos) e sobre a desativação automática de workflows agendados após 60 dias sem atividade no repositório, e implemente uma solução (ex.: commit automático do histórico mantém o repo ativo).
- Faça um modo `--dry-run` que roda tudo e mostra o que seria enviado sem mandar WhatsApp, e um comando de teste que envia uma mensagem de exemplo.

# ENTREGÁVEIS

1. Código funcionando da Fase 1, rodando localmente e no Actions.
2. README com passo a passo para eu configurar (criar repositório, Secrets, ativar o WhatsApp, ajustar o limite de preço e o CEP).
3. Relatório honesto: quais lojas funcionam, quais estão bloqueadas, o que ficou como "melhor esforço".
4. Fase 2 em seguida, depois de eu validar a Fase 1.

Trabalhe em etapas pequenas, rode os testes a cada etapa e me mostre o resultado de uma execução real em dry-run antes de ligar o agendamento.