# Afiliado Shopee: descoberta de produtos + gerador de vídeos

Ferramenta em Python que, **todo dia**:

1. Consulta a **API oficial de afiliados da Shopee** em ~28 nichos diferentes;
2. Filtra produtos ruins (nota baixa, pouca venda, preço fora da faixa);
3. Dá uma **pontuação** equilibrando *quanto você ganha por venda* e *chance de vender*;
4. Descobre **quais nichos estão rendendo mais** (você não precisa escolher nicho);
5. Gera **vídeos verticais 9:16** (Shopee Vídeo / Reels / TikTok), capa, legenda com hashtags
   e o texto do comentário com seu link de afiliado.

A postagem continua sendo **manual** (cerca de 2 minutos por vídeo). Automatizar login e postagem
vai contra os termos da Shopee e pode **banir sua conta de afiliado**.

## 1. Como conseguir a API (gratuita)

1. Entre em <https://affiliate.shopee.com.br> com sua conta de afiliado.
2. No menu, procure **"Open API"** (às vezes fica em *Ferramentas* ou no rodapé do painel).
3. Solicite o acesso. Após a aprovação aparecem o **AppID** e o **Secret** (chave secreta).
4. **Nunca** mande o Secret para ninguém nem faça commit dele. Ele fica só no arquivo `.env`
   ou nos *Secrets* do GitHub.

> Se a opção Open API não aparecer, abra um chamado no suporte de afiliados pedindo
> "acesso à Open API de afiliados". Algumas contas novas precisam ter vendas antes.

## 2. Instalação (no seu computador)

Pré-requisitos: [Python 3.10+](https://www.python.org/downloads/) e
[ffmpeg](https://ffmpeg.org/download.html) (no Windows: `winget install ffmpeg`).

```bash
git clone <este repositório>
cd hello-world
python -m venv .venv
# Windows: .venv\Scripts\activate    |   Linux/Mac: source .venv/bin/activate
pip install -r requirements.txt
```

## 3. Testar sem a API (modo demonstração)

```bash
python -m afiliado --demo --top 3
```

Abra a pasta `saida/AAAA-MM-DD/`. Lá estão `relatorio.md`, `candidatos.csv` e uma pasta por
produto com `video.mp4`, `capa.jpg`, `legenda.txt` e `comentario_fixado.txt`.

## 4. Usar com dados reais

```bash
cp .env.example .env      # depois edite o .env com AppID e Secret
python -m afiliado --top 5 --link-curto
```

| Opção | O que faz |
|---|---|
| `--top 5` | quantos vídeos gerar |
| `--nichos "pet,cozinha"` | limita a nichos específicos (padrão: descoberta automática) |
| `--link-curto` | gera link com *Sub ID* por vídeo; no painel você vê **qual vídeo vendeu** |
| `--narracao` | adiciona voz em português (`pip install edge-tts`) |
| `--musica arquivo.mp3` | música de fundo (use só música livre de direitos) |
| `--sem-video` | só o relatório |

## 5. Rodar sozinho todo dia (GitHub Actions, grátis)

1. No GitHub: **Settings › Secrets and variables › Actions › New repository secret**
   e crie `SHOPEE_APP_ID` e `SHOPEE_SECRET`.
2. O workflow `.github/workflows/afiliado-diario.yml` roda todo dia às 07:17 (Brasília).
3. Para baixar: aba **Actions** › execução do dia › **Artifacts**.

## Rotina sugerida (5 a 10 minutos por dia)

1. Baixe os vídeos do dia e leia o `relatorio.md`.
2. **Confira no app se o preço ainda é o mesmo** antes de postar.
3. Poste no Shopee Vídeo **vinculando o produto** pelo próprio app (é assim que a Shopee
   rastreia a venda). Adicione uma música em alta do próprio app.
4. Reposte o mesmo vídeo no Reels/TikTok com o link do `comentario_fixado.txt`.
5. Depois de 1 a 2 semanas, veja no painel quais *Sub IDs* venderam e ajuste os pesos em
   `afiliado/pontuacao.py`.

## Estrutura do código

```
afiliado/
├── __main__.py          # rotina diária (linha de comando)
├── config.py            # lê .env
├── modelos.py           # classe Produto
├── pontuacao.py         # filtros, nota de cada produto e ranking de nichos
├── video.py             # gera cenas com Pillow + vídeo com ffmpeg
├── legenda.py           # legenda, hashtags e roteiro de narração
├── historico.py         # não repete produto por 14 dias
├── relatorio.py         # relatorio.md + candidatos.csv
├── demo.py              # dados fictícios para teste
└── shopee/
    ├── api.py           # cliente GraphQL com assinatura SHA256
    └── descoberta.py    # varredura automática de nichos
```

Testes: `pip install pytest && python -m pytest`

## Próximos passos

- [ ] Mercado Livre (quando for aprovado no programa de afiliados)
- [ ] Usar mais de uma foto do produto no vídeo
- [ ] Painel com histórico de cliques e vendas por nicho
