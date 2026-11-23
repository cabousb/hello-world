# Resets e "níveis" no OpenMU

Tudo aqui foi conferido no código-fonte (`src/GameLogic/Resets/`) e na documentação do projeto, mas
**não** foi testado num servidor rodando. Os nomes dos campos vêm do código, e as telas do painel
podem diferir um pouco. Os números são pontos de partida para ajustar jogando.

## O que existe

O plugin de reset (*Reset feature*, em *Configuration → Plugins*) vem **desligado por padrão**. Ative-o
e abra o ⚙ para configurar. Sem isso o jogo responde que o reset não está habilitado. O *Stat reset* é
outro plugin (só zera atributos).

| Campo | Padrão | Notas |
|---|---|---|
| Reset limit | vazio | **Um número único** para o servidor todo. 0 ou vazio = sem limite. |
| Required level | 400 | |
| Level after reset | 10 | Subir esse valor encurta o ciclo: o personagem não recomeça do 1. |
| Required money | 1 | Zen |
| Multiply required money by reset count | ligado | Custo **linear**: base × número do reset. Faixas de preço em Zen não existem. |
| Required reset item + Item cost tiers | nenhum | Quantidade do item por faixa de resets |
| Reset stats | ligado | Volta os atributos ao valor inicial |
| Replace points per reset | ligado | Com *Points tiers*, os pontos passam a ser o **total acumulado** de todos os resets |
| Points tiers | vazio | Cada entrada: "a partir do reset X, Y pontos por reset" |
| Move home / Log out | ligados | |

Comandos de chat: `/reset` e `/resetinfo` (jogadores). `/setresets` e `/getresets` são só de GM e vêm
**desativados por padrão**: ative na página *Chat commands* para testar faixas sem farmar.
Existe também um NPC de reset (*Leo the Helper*, plugin `ResetCharacterNpcPlugin`).

Requisitos por número de **Resets** podem ser colocados em mapas (*Map Requirements*) e em warps.

## Preset "padrão de mercado"

Reset em nível alto com custo crescente, e a **taxa de experiência** controla a dificuldade.

| Campo | Valor |
|---|---|
| Reset limit | 100 (suba depois) |
| Required level / Level after reset | 400 / 1 |
| Required money | 1.000.000, multiplicando pelo nº do reset |
| Points tiers | a partir do reset 1: 300 pontos |
| Experience rate (*General*) | 100–300 médio, 500+ mais leve. Anote o valor antigo antes de mudar. |

Dica de método: escolha quanto tempo um reset deve levar (cerca de 20–30 min no começo, 1–2 h no
meio) e ajuste a experiência depois de jogar um ciclo inteiro. Errar para o lado fácil é melhor,
porque endurecer depois é mais fácil que nerfar.

## Preset "níveis por faixa de resets" (6 níveis de 5 resets)

Limite 30, nível exigido 250, nível após o reset 50, 100.000 Zen. Pontos por faixa 100, 120, 140, 160,
180 e 200 (a partir dos resets 1, 6, 11, 16, 21, 26). Cada faixa libera mapas mais difíceis e uma loja
de sets melhor.

**Armadilha:** não trave por resets os mapas usados para subir de nível (Devias, por exemplo). Quem
recomeça no nível 50 precisa deles para ganhar experiência. Trave só os de fim de jogo. Para isso
peça a lista de mapas do *Map editor* do usuário.

## O que o painel não faz (exige plugin)

- Limite de resets diferente por nível
- Bônus automático de dano ou defesa por nível
- Loja que só vende para quem está no nível certo (a trava por mapa resolve a maioria dos casos)
- Master Reset
- VIP com reset em nível menor (por exemplo 390)
- Custo em Zen por faixas

O ponto de partida para esses plugins é `ResetCharacterAction.cs` e `ResetProgressionCalculator.cs`.

## Pedido do tipo "igual ao servidor X"

Não presuma as regras de um servidor específico. Se uma busca na web não achar a página dele, diga
isso, peça ao usuário que descreva as regras ou cole o texto, e traduza regra por regra para os campos
acima. Copiar a mecânica é normal, mas nome, identidade visual e arquivos do outro servidor não.
