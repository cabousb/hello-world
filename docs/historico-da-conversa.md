# Histórico do projeto: afiliado Shopee

Resumo da conversa com o Claude que deu origem a este projeto, com as decisões tomadas,
os passos já feitos e o que falta. Serve para retomar o trabalho em qualquer sessão nova:
basta pedir ao Claude para ler este arquivo.

---

## 1. Objetivo

Montar uma estrutura de vendas como afiliado, começando pela **Shopee** e depois o
**Mercado Livre**, de forma orgânica (sem pagar planos nem anúncios):

- descobrir todo dia os melhores produtos para divulgar (maior comissão e mais vendas);
- gerar vídeos no formato do Shopee Vídeo, Reels e TikTok;
- postar os vídeos.

## 2. Decisões importantes

| Decisão | Motivo |
|---|---|
| **Não passar login e senha para o Claude** | Senha no chat fica registrada. O ambiente do Claude é temporário e não consegue entrar na conta todo dia. |
| **Não automatizar login nem postagem** | Vai contra os termos da Shopee e do Mercado Livre. O risco é banir a conta de afiliado e perder comissões. |
| **Usar a API oficial de afiliados da Shopee** | É gratuita, permitida e usa uma chave (AppID + Secret) em vez da senha. |
| **Postagem manual** | Cerca de 2 minutos por vídeo. Mantém a conta segura e permite conferir o preço antes. |
| **Começar pela Shopee** | Já aprovado como afiliado lá. A API da Shopee é mais completa. |
| **Sem nicho definido** | O script descobre sozinho os melhores nichos (varre 28 nichos). |
| **Repositório privado** | O código e os vídeos gerados (com links de afiliado) não ficam expostos. Já foi feito. |

## 3. O que já foi construído

Código em Python (detalhes no [README](../README.md)):

- `afiliado/shopee/api.py`: cliente da Shopee Affiliate Open API (GraphQL, assinatura SHA256).
- `afiliado/shopee/descoberta.py`: busca em 28 nichos, por maior comissão e por mais vendidos.
- `afiliado/pontuacao.py`: filtros (nota ≥ 4,3, ≥ 50 vendas, preço de R$ 15 a R$ 600) e nota de 0 a 100:
  ganho por venda 45%, vendas 35%, avaliação 12%, desconto 8%. Também gera o ranking de nichos.
- `afiliado/video.py`: vídeo vertical 1080x1920 de 15 s com 5 cenas
  (abertura, produto, preço, prova social, chamada para o link) e capa.
- `afiliado/legenda.py`: legenda, hashtags, comentário com link e roteiro de narração.
- `afiliado/historico.py`: não repete o mesmo produto por 14 dias.
- `.github/workflows/afiliado-diario.yml`: roda sozinho todo dia às 07:17 (Brasília).

Testado: modo demonstração (`python -m afiliado --demo`) e 8 testes automáticos.
**Ainda não testado com a API real**, porque a chave não foi liberada.

## 4. Passos já concluídos

- [x] Aprovado no programa de afiliados da Shopee
- [x] Estrutura do projeto criada e enviada ao GitHub
- [x] Repositório tornado privado (pelo navegador, em Settings › General › Danger Zone)
- [x] Pedido de acesso à Open API enviado ao suporte de afiliados da Shopee

## 5. Próximos passos

1. **Aguardar a Shopee liberar a API** (AppID e Secret).
2. **Cadastrar a chave no GitHub:** Settings › Secrets and variables › Actions ›
   New repository secret. Criar `SHOPEE_APP_ID` e `SHOPEE_SECRET`.
   No celular, abrir o github.com no navegador com "Site para computador" ativado.
3. **Pedir ao Claude para abrir o pull request** e levar o código para o `main`
   (o GitHub só roda a tarefa diária a partir do `main`).
4. **Primeiro teste real:** aba Actions › "Afiliado Shopee diario" › Run workflow.
   Se der erro, mandar a mensagem de erro ao Claude para ajustar.
5. **Rotina diária:** baixar os vídeos em Actions › Artifacts, conferir o preço no app,
   postar no Shopee Vídeo vinculando o produto, repostar no Reels/TikTok.
6. Depois de 1 a 2 semanas, ver no painel quais *Sub IDs* venderam e ajustar os pesos.
7. Mais tarde: **Mercado Livre**, quando for aprovado no programa de afiliados.

## 6. Como pedir a API (referência)

A opção **Open API** fica no portal de afiliados pelo navegador (affiliate.shopee.com.br),
não no aplicativo. No Android: Chrome › menu ⋮ › "Site para computador".

Mensagem usada para o suporte:

> Olá! Sou afiliado aprovado no Programa de Afiliados Shopee e gostaria de solicitar acesso
> à **Open API de Afiliados**. Preciso das credenciais (**AppID e Secret**) para consultar as
> ofertas disponíveis e gerar meus links de afiliado de forma automatizada, para usar no meu
> conteúdo em vídeo. Poderiam liberar o acesso ou me informar como fazer a solicitação?

Regras de segurança:
- Nunca enviar a senha da conta para ninguém (nem para o suporte, nem para o Claude).
- O Secret da API é como uma senha: vai só nos Secrets do GitHub ou no arquivo `.env`
  (que nunca é enviado ao GitHub).
