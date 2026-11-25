# Gera as páginas do site a partir de um molde comum. Uso: python3 build.py
import pathlib
CFG = dict(exp="300x", mexp="1x", reset_lvl=400, after=1, pts=300, zen="1.000.000", limit=100)
NAV = [("index.html","Início"),("info.html","Informações"),("downloads.html","Downloads"),
       ("ranking.html","Ranking"),("regras.html","Regras"),("cadastro.html","Cadastro")]
def page(fname, title, body, hero=""):
    nav = "".join(f'<a href="{h}"{" class=on" if h==fname else ""}>{t}</a>' for h,t in NAV)
    return f'''<!DOCTYPE html><html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>{title} · MuMaster</title>
<link rel="stylesheet" href="style.css"></head><body>
<header><div class="bar"><a class="logo" href="index.html">Mu<span>Master</span></a><nav>{nav}</nav></div></header>
{hero}<main>{body}</main>
<footer><div class="bar"><div>© 2026 MuMaster · servidor independente, feito por fãs.</div>
<div>Este site não tem nenhuma relação com a Webzen Inc. MU Online é marca registrada da Webzen Inc.</div>
<div>Servidor baseado em software livre (<a href="https://github.com/MUnique/OpenMU">Powered by OpenMU</a>).</div></div></footer>
</body></html>'''
c = CFG
pages = {}
pages["index.html"] = page("index.html","Início", f'''
<div class="grid">
 <div class="card stat"><div class="k">Versão</div><div class="v">Season 6</div></div>
 <div class="card stat"><div class="k">Experiência</div><div class="v">{c["exp"]}</div></div>
 <div class="card stat"><div class="k">Reset</div><div class="v">Nível {c["reset_lvl"]}</div></div>
 <div class="card stat"><div class="k">Jogadores online</div><div class="v">—</div><div class="muted">em breve</div></div>
</div>
<h2>Novidades</h2>
<div class="grid">
 <div class="card"><span class="tag">Aviso</span><h3>Servidor em fase de testes</h3><p class="muted">Estamos ajustando experiência, resets e eventos. A data de abertura será anunciada aqui.</p></div>
 <div class="card"><span class="tag">Sistema</span><h3>Resets liberados</h3><p class="muted">Resete no nível {c["reset_lvl"]} com <code>/reset</code> e ganhe {c["pts"]} pontos a cada reset.</p></div>
</div>
<h2>Como começar</h2>
<ol class="steps">
 <li><b>Crie sua conta</b> <span class="muted">— o cadastro pelo site chega em breve.</span></li>
 <li><b>Baixe o cliente e o launcher</b> na página <a href="downloads.html">Downloads</a>.</li>
 <li><b>Abra o jogo pelo launcher</b> e escolha um servidor.</li>
</ol>
<h2>Classes</h2>
<div class="grid">
 <div class="card"><h3>Dark Wizard</h3><p class="muted">Magias em área e dano à distância. Evolui com Energia.</p></div>
 <div class="card"><h3>Dark Knight</h3><p class="muted">Linha de frente, muita vida e dano físico.</p></div>
 <div class="card"><h3>Fairy Elf</h3><p class="muted">Arqueira e suporte, com buffs para o grupo.</p></div>
 <div class="card"><h3>Magic Gladiator, Dark Lord, Summoner e Rage Fighter</h3><p class="muted">Classes especiais com estilos próprios.</p></div>
</div>''', hero='''<section class="hero"><h1>MuMaster</h1><p>Servidor Season 6 · experiência rápida · resets · eventos</p>
<div class="cta"><a class="btn" href="downloads.html">Baixar e jogar</a><a class="btn ghost" href="info.html">Ver informações</a></div></section>''')
pages["info.html"] = page("info.html","Informações", f'''
<h2>Taxas</h2>
<table><tr><th>Item</th><th>Valor</th></tr>
<tr><td>Versão</td><td>Season 6 Episode 3</td></tr>
<tr><td>Experiência</td><td>{c["exp"]}</td></tr><tr><td>Experiência master</td><td>{c["mexp"]}</td></tr>
<tr><td>Nível máximo</td><td>400</td></tr></table>
<h2>Sistema de reset</h2>
<table><tr><th>Regra</th><th>Valor</th></tr>
<tr><td>Nível para resetar</td><td>{c["reset_lvl"]}</td></tr><tr><td>Nível após o reset</td><td>{c["after"]}</td></tr>
<tr><td>Custo</td><td>{c["zen"]} Zen × número do reset</td></tr><tr><td>Pontos</td><td>{c["pts"]} × número do reset</td></tr>
<tr><td>Limite de resets</td><td>{c["limit"]}</td></tr></table>
<h2>Comandos</h2>
<table><tr><th>Comando</th><th>O que faz</th></tr>
<tr><td><code>/reset</code></td><td>Reseta o personagem quando ele cumpre os requisitos.</td></tr>
<tr><td><code>/resetinfo</code></td><td>Mostra custo e requisitos do próximo reset.</td></tr>
<tr><td><code>/add ene 100</code></td><td>Distribui pontos. Atributos: <code>str</code>, <code>agi</code>, <code>vit</code>, <code>ene</code>, <code>cmd</code>.</td></tr>
<tr><td><code>/pkclear</code></td><td>Limpa o status de PK, conforme as regras do servidor.</td></tr>
<tr><td><code>/language pt</code></td><td>Mensagens do servidor em português.</td></tr></table>
<p class="muted">Distribuir vários pontos de uma vez recarrega o personagem na tela. Ligue o MU Helper depois de distribuir.</p>
<h2>Eventos</h2>
<div class="grid">
 <div class="card"><h3>Blood Castle</h3><p class="muted">Horários a definir.</p></div>
 <div class="card"><h3>Devil Square</h3><p class="muted">Horários a definir.</p></div>
 <div class="card"><h3>Chaos Castle</h3><p class="muted">Horários a definir.</p></div>
 <div class="card"><h3>Castle Siege</h3><p class="muted">Semanal. Horários a definir.</p></div>
</div>''')
pages["downloads.html"] = page("downloads.html","Downloads", '''
<h2>Downloads</h2>
<div class="grid">
 <div class="card"><span class="tag">Obrigatório</span><h3>Cliente Season 6</h3><p class="muted">O link do cliente será publicado aqui na abertura do servidor.</p></div>
 <div class="card"><span class="tag">Obrigatório</span><h3>Launcher</h3><p class="muted">Abre o jogo já conectado ao MuMaster. Precisa do .NET 10 Desktop Runtime.</p></div>
</div>
<h2>Instalação</h2>
<ol class="steps">
 <li>Extraia o cliente numa pasta fora do OneDrive, por exemplo <code>C:\\MuMaster</code>.</li>
 <li>Coloque o <code>main.exe</code> do pacote na pasta do cliente, junto da pasta <code>Data</code>.</li>
 <li>Abra sempre pelo launcher, nunca direto pelo <code>main.exe</code>.</li>
</ol>
<p class="muted">Se o antivírus bloquear um arquivo, baixe de novo somente por este site.</p>''')
pages["ranking.html"] = page("ranking.html","Ranking", '''<h2>Ranking</h2>
<div class="soon"><h3>Em breve</h3><p>Top nível, top resets e top guilds, atualizados direto do servidor.</p></div>''')
pages["cadastro.html"] = page("cadastro.html","Cadastro", '''<h2>Cadastro</h2>
<div class="soon"><h3>Em breve</h3><p>O cadastro de contas pelo site está em preparação.</p></div>''')
pages["regras.html"] = page("regras.html","Regras", '''<h2>Regras do servidor</h2>
<ol class="steps">
 <li><b>Proibido usar programas de trapaça</b> (hacks, bots externos, speed). Punição: banimento.</li>
 <li><b>Respeito no chat.</b> Ofensas, racismo e assédio levam a silenciamento ou banimento.</li>
 <li><b>Proibido vender contas ou itens por dinheiro real</b> fora dos canais oficiais.</li>
 <li><b>Bugs devem ser reportados à equipe.</b> Explorar bug de propósito leva a punição.</li>
 <li><b>A equipe nunca pede a sua senha.</b> Não a passe para ninguém.</li>
</ol>
<p class="muted">As regras podem mudar. Avisos importantes saem na página inicial.</p>''')
for name, html in pages.items():
    pathlib.Path(name).write_text(html, encoding="utf-8")
print("páginas:", ", ".join(pages))
