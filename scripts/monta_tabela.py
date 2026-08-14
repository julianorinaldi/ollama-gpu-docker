#!/usr/bin/env python3
"""Monta a página de comparação: 30 personagens em linhas, modelos em colunas.

As miniaturas vão embutidas como data: URI para a página ser um arquivo só,
que abre em qualquer lugar sem depender da pasta de imagens ao lado.

uso: monta_tabela.py <json> <destino.html> [largura_da_miniatura]
"""
import base64
import io
import json
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from comfy_baralho import familia  # noqa: E402

ORIGEM = Path("saida/baralho")

# A tabela existe para responder "o modelo obedeceu à paleta do tipo?". Por isso
# cada linha carrega a paleta que foi PEDIDA — sem isso, quem olha não tem como
# julgar obediência, só gosto.
PALETA_ROTULO = {
    "feiticeiro": ("Ciano", "ciano"),
    "maldicao": ("Carmim", "carmim"),
    "restricao": ("Cinza fosco", "aco"),
    "neutro": ("Neutro", "neutro"),
}
# Ordem de leitura: o escolhido primeiro, depois os demais por proximidade.
COLUNAS = [
    ("netayume", "NetaYume v4"),
    ("animagine", "Animagine 4.0"),
    ("anima", "Anima"),
    ("anima29", "Anima 2.9B"),
    ("illustrious2", "Illustrious v2"),
    ("zimage", "Z-Image"),
    ("noobai", "NoobAI"),
]


def miniatura(caminho, largura):
    """Devolve None se o arquivo ainda estiver sendo escrito.

    A tabela é montada com o gerador rodando, então volta e meia se pega um PNG
    pela metade. Tratar como ausente é melhor que derrubar a montagem inteira —
    na próxima passagem ele já estará completo.
    """
    try:
        im = Image.open(caminho).convert("RGB")
    except OSError:
        return None
    im = im.resize((largura, round(im.height * largura / im.width)), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=78, optimize=True)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


def main():
    dados = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    lista = dados["personagens"] if isinstance(dados, dict) else dados
    destino = Path(sys.argv[2])
    largura = int(sys.argv[3]) if len(sys.argv) > 3 else 200

    presentes = [(c, r) for c, r in COLUNAS if list(ORIGEM.glob(f"*-{c}_*.png"))]
    linhas, total = [], 0
    for p in lista:
        celulas = []
        for chave, _ in presentes:
            achados = sorted(ORIGEM.glob(f"{p['id']}-{chave}_*.png"))
            dado = miniatura(achados[0], largura) if achados else None
            if dado:
                celulas.append(f'<td><img loading="lazy" src="{dado}" alt=""></td>')
                total += 1
            else:
                celulas.append('<td class="vazio">—</td>')
        rotulo, classe = PALETA_ROTULO[familia(p)]
        linhas.append(
            f'<tr><th scope="row">'
            f'<span class="num">{p["numero_carta"]:02d}</span>'
            f'<span class="nome">{p["nome"]}</span>'
            f'<span class="chip {classe}">{rotulo}</span>'
            f'</th>{"".join(celulas)}</tr>')

    cabecalho = "".join(f"<th>{r}</th>" for _, r in presentes)
    destino.write_text(PAGINA.format(
        cabecalho=cabecalho, linhas="\n".join(linhas),
        total=total, modelos=len(presentes)), encoding="utf-8")
    print(f"{destino} — {total} imagens, {len(presentes)} modelos")


PAGINA = """<title>Baralho JJK — comparação de modelos</title>
<style>
  /* Claro é o padrão; o escuro redefine só os tokens, nas duas portas
     (preferência do sistema e escolha explícita). */
  :root {{
    --fundo: #eef1f4; --papel: #ffffff; --faixa: #f7f9fa;
    --tinta: #101419; --fraco: #5a6572; --linha: #d8dde3;
    --destaque: #0e7490; --sombra: rgba(16, 20, 25, .10);
    --ciano: #0e7490; --carmim: #b4232a; --aco: #5c6773; --neutro: #8a6d3b;
  }}
  @media (prefers-color-scheme: dark) {{
    :root:not([data-theme="light"]) {{
      --fundo: #0b0e13; --papel: #151a23; --faixa: #1b212b;
      --tinta: #e6ebf2; --fraco: #8a95a4; --linha: #262d38;
      --destaque: #22d3ee; --sombra: rgba(0, 0, 0, .45);
      --ciano: #22d3ee; --carmim: #f0666b; --aco: #a6b0bd; --neutro: #d1ac6d;
    }}
  }}
  :root[data-theme="dark"] {{
    --fundo: #0b0e13; --papel: #151a23; --faixa: #1b212b;
    --tinta: #e6ebf2; --fraco: #8a95a4; --linha: #262d38;
    --destaque: #22d3ee; --sombra: rgba(0, 0, 0, .45);
    --ciano: #22d3ee; --carmim: #f0666b; --aco: #a6b0bd; --neutro: #d1ac6d;
  }}

  body {{
    margin: 0; background: var(--fundo); color: var(--tinta);
    font: 15px/1.55 ui-sans-serif, system-ui, -apple-system, "Segoe UI", sans-serif;
  }}
  header {{ padding: 34px 24px 18px; max-width: 74ch; }}
  h1 {{
    font-size: clamp(1.35rem, 1rem + 1.4vw, 1.9rem); line-height: 1.15;
    margin: 0 0 10px; letter-spacing: -.015em; text-wrap: balance;
  }}
  header p {{ margin: 0 0 14px; color: var(--fraco); }}
  .legenda {{
    display: flex; flex-wrap: wrap; gap: 8px 18px; margin: 0; padding: 0;
    list-style: none; font-size: .82rem; color: var(--fraco);
  }}
  .legenda span {{ font-weight: 600; }}

  .rolagem {{ overflow-x: auto; padding: 8px 24px 56px; }}
  table {{ border-collapse: separate; border-spacing: 0; background: var(--papel); }}

  thead th {{
    position: sticky; top: 0; z-index: 2; background: var(--papel);
    padding: 12px 10px; font-size: .74rem; font-weight: 700;
    letter-spacing: .09em; text-transform: uppercase; color: var(--destaque);
    border-bottom: 2px solid var(--linha); white-space: nowrap;
  }}
  thead th:first-child {{ left: 0; z-index: 3; text-align: left; }}

  tbody th {{
    position: sticky; left: 0; z-index: 1; background: var(--papel);
    text-align: left; padding: 10px 18px 10px 12px; min-width: 200px;
    border-right: 1px solid var(--linha); border-bottom: 1px solid var(--linha);
    vertical-align: middle; box-shadow: 6px 0 12px -10px var(--sombra);
  }}
  tbody tr:nth-child(even) th, tbody tr:nth-child(even) td {{ background: var(--faixa); }}

  .num {{
    display: inline-block; min-width: 1.6em; margin-right: 8px;
    font-variant-numeric: tabular-nums; font-size: .82rem; color: var(--fraco);
  }}
  .nome {{ font-weight: 650; }}
  /* O chip diz qual paleta foi PEDIDA — é o gabarito da comparação. */
  .chip {{
    display: inline-block; margin-top: 5px; padding: 2px 8px; border-radius: 999px;
    font-size: .68rem; font-weight: 700; letter-spacing: .07em;
    text-transform: uppercase; border: 1px solid currentColor;
  }}
  .chip.ciano {{ color: var(--ciano); }}
  .chip.carmim {{ color: var(--carmim); }}
  .chip.aco {{ color: var(--aco); }}
  .chip.neutro {{ color: var(--neutro); }}

  td {{ padding: 4px; vertical-align: top; border-bottom: 1px solid var(--linha); }}
  td img {{ display: block; width: 210px; height: auto; border-radius: 3px; }}
  .vazio {{ color: var(--fraco); text-align: center; font-size: .8rem; }}
</style>
<header>
  <h1>Baralho JJK — a mesma ficha em {modelos} modelos</h1>
  <p>{total} imagens geradas na RTX 3060. Para cada personagem, o prompt e a
     seed são idênticos em todas as colunas — só o modelo muda.</p>
  <ul class="legenda">
    <li>A paleta vem do tipo do personagem, e o chip de cada linha diz qual foi pedida:</li>
    <li><span class="chip ciano">Ciano</span> feiticeiro</li>
    <li><span class="chip carmim">Carmim</span> maldição</li>
    <li><span class="chip aco">Cinza fosco</span> restrição celestial, sem brilho</li>
  </ul>
</header>
<div class="rolagem">
<table>
  <thead><tr><th>Personagem</th>{cabecalho}</tr></thead>
  <tbody>
{linhas}
  </tbody>
</table>
</div>
"""

if __name__ == "__main__":
    main()
