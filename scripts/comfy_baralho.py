#!/usr/bin/env python3
"""Gera o baralho inteiro (30 personagens) em cada modelo, para comparação.

Reaproveita o motor de comfy_bancada.py — só troca os 4 personagens de teste
pelos 30 de verdade, lidos de jjk-characters.json.

O que vem do JSON: o tipo (que define a paleta) e o nome da técnica inata (que
vira o motivo visual). O que NÃO vem do JSON: a tag Danbooru e os traços
físicos. O JSON guarda "Satoru Gojo", nome de exibição em pt-BR, que como
prompt devolve um sujeito genérico de cabelo branco — o modelo aprendeu
"gojou satoru". Daí o mapa abaixo existir separado.

uso: comfy_baralho.py <json> <modelo> [modelo ...]
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from comfy_bancada import MODELOS, envia, espera, grafo  # noqa: E402

SEMENTE_BASE = 4400

# id do JSON -> (tag danbooru, traços físicos)
FICHA = {
    "satoru-gojo": ("gojou satoru", "1boy, white hair, blindfold over eyes, black high-collar uniform"),
    "ryomen-sukuna": ("ryoumen sukuna (jujutsu kaisen)", "1boy, pink hair, four eyes, black facial markings, tattoos, evil grin"),
    "yuta-okkotsu": ("okkotsu yuuta", "1boy, black hair, blue eyes, black school uniform, holding katana"),
    "yuji-itadori": ("itadori yuuji", "1boy, pink hair, undercut, black school uniform, determined"),
    "megumi-fushiguro": ("fushiguro megumi", "1boy, black spiky hair, green eyes, black school uniform, serious"),
    "nobara-kugisaki": ("kugisaki nobara", "1girl, short orange hair, brown eyes, black school uniform, confident smirk"),
    "kento-nanami": ("nanami kento", "1boy, blonde hair, tinted glasses, brown suit, necktie, stern"),
    "aoi-todo": ("toudou aoi (jujutsu kaisen)", "1boy, dark skin, short black hair, very muscular, school uniform"),
    "maki-zenin": ("zen'in maki", "1girl, dark green hair, low ponytail, glasses, black school uniform, holding polearm"),
    "toge-inumaki": ("inumaki toge", "1boy, light hair, high collar covering mouth, seal markings on cheeks"),
    "panda": ("panda (jujutsu kaisen)", "anthro panda, black and white fur, no humans, school uniform, standing"),
    "suguru-geto": ("getou suguru", "1boy, long black hair in a bun, forehead marking, dark kesa robes"),
    "kenjaku": ("kenjaku (jujutsu kaisen)", "1boy, long black hair, stitched scalp, scar across forehead, dark robes"),
    "mahito": ("mahito (jujutsu kaisen)", "1boy, grey patchwork skin, stitched scars on face, tied grey hair, unsettling smile"),
    "jogo": ("jogo (jujutsu kaisen)", "monster, volcano-shaped head, single large eye, no humans, cursed spirit"),
    "hanami": ("hanami (jujutsu kaisen)", "monster, wooden bark body, plant creature, horns, no humans, cursed spirit"),
    "dagon": ("dagon (jujutsu kaisen)", "monster, fish-like humanoid cursed spirit, no humans"),
    "toji-fushiguro": ("fushiguro touji", "1boy, black hair, scar on lips, dark shirt, very muscular, holding a katana"),
    "choso": ("choso (jujutsu kaisen)", "1boy, black hair in twin buns, mark across nose bridge, dark clothes"),
    "kinji-hakari": ("hakari kinji", "1boy, blonde undercut hair, tall, black school uniform, grinning"),
    "hiromi-higuruma": ("higuruma hiromi", "1boy, messy black hair, tired eyes, dark suit, holding a gavel"),
    "kashimo-hajime": ("kashimo hajime", "1boy, long pale hair, pink eyes, lightning sparks, bare chest, staff"),
    "yuki-tsukumo": ("tsukumo yuki", "1girl, long blonde hair, high ponytail, tall, casual jacket"),
    "uraume": ("uraume (jujutsu kaisen)", "1other, short white hair, androgynous, traditional kimono, ice crystals"),
    "ryu-ishigori": ("ishigori ryuu", "1boy, very muscular, tanned skin, white hair, bare chest"),
    "noritoshi-kamo": ("kamo noritoshi", "1boy, black hair in a ponytail, red eyes, black school uniform, composed"),
    "naoya-zenin": ("zen'in naoya", "1boy, blonde hair in a short ponytail, traditional clothes, arrogant sneer"),
    "mei-mei": ("mei mei (jujutsu kaisen)", "1girl, silver white bob cut, dark coat, holding a large axe"),
    "shoko-ieiri": ("ieiri shoko", "1girl, brown hair, tired eyes, white lab coat, cigarette"),
    "ui-ui": ("ui ui (jujutsu kaisen)", "1boy, black hair, young, formal dark suit"),
}

# (positivo, negativo) por família de tipo.
PALETA = {
    "feiticeiro": ("cyan cursed energy aura, cold blue rim light",
                   "orange, yellow, fire, warm lighting, red aura"),
    "maldicao": ("crimson and violet cursed aura, red backlight", "cyan, blue aura"),
    # Ausência se pede no negativo — no positivo o modelo lê "glow" e desenha.
    "restricao": ("steel grey and bone white, matte flat lighting",
                  "glowing, glow, aura, cursed energy, fire, sparks, bloom, lens flare, "
                  "orange, warm lighting, colorful"),
    "neutro": ("muted earth tones, soft neutral lighting", "aura, cursed energy, glow"),
}

# Panda e Choso não se encaixam pelo nome do tipo: "Cadáver Amaldiçoado" não é
# maldição no sentido visual, e "Semi-humano / Cadáver Pintado" é sangue.
EXCECOES = {"panda": "neutro", "choso": "maldicao"}

NEG_BASE = ("worst quality, low quality, bad anatomy, bad hands, text, watermark, "
            "signature, artist name, blurry, jpeg artifacts, cropped, "
            "trading card frame, border, multiple views")


def familia(personagem):
    if personagem["id"] in EXCECOES:
        return EXCECOES[personagem["id"]]
    tipo = personagem.get("tipo", "")
    if "Restrição Celestial" in tipo:
        return "restricao"
    if "Feiticeir" in tipo:
        return "feiticeiro"
    if "Maldição" in tipo:
        return "maldicao"
    return "neutro"


def main():
    dados = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    lista = dados["personagens"] if isinstance(dados, dict) else dados
    destino = Path("saida/baralho")

    for nome_modelo in sys.argv[2:]:
        cfg = MODELOS[nome_modelo]
        print(f"== {nome_modelo}", flush=True)
        for p in lista:
            ident = p["id"]
            if ident not in FICHA:
                print(f"   {ident}: sem ficha, pulando", flush=True)
                continue
            # Retomável: uma leva de 210 imagens não pode recomeçar do zero.
            if list(destino.glob(f"{ident}-{nome_modelo}_*.png")):
                continue
            tag, tracos = FICHA[ident]
            paleta, neg_paleta = PALETA[familia(p)]
            prompt = (f"{tracos}, {tag}, jujutsu kaisen, upper body, looking at viewer, "
                      f"{paleta}, dark background, {cfg['qualidade']}")
            try:
                espera(envia(grafo(cfg, prompt, f"{NEG_BASE}, {neg_paleta}",
                                   SEMENTE_BASE + p["numero_carta"],
                                   f"baralho/{ident}-{nome_modelo}")), limite=1200)
                print(f"   {p['numero_carta']:>2} {ident}", flush=True)
            except Exception as e:
                print(f"   {p['numero_carta']:>2} {ident}: FALHOU {str(e)[:120]}", flush=True)


if __name__ == "__main__":
    main()
