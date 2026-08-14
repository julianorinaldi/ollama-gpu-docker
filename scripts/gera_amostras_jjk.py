#!/usr/bin/env python3
"""Amostras de arte de carta do jujutsu-kaisen.com com SDXL anime local.

Roda dentro do container diffusers (ver README). Gera 896x1152 — a carta usa
3/4 com object-fit:cover, e 896x1152 é a resolução nativa do SDXL mais próxima
disso; forçar 768x1024 exato perde área de treino e a qualidade cai.

O ponto todo deste script é a TAG DANBOORU. Animagine e NoobAI são treinados
com o vocabulário do Danbooru, então "gojou satoru" não é uma descrição: é um
identificador que o modelo aprendeu. Escrever "Satoru Gojo" em inglês corrente
devolve um personagem genérico de cabelo branco. Por isso o mapa abaixo existe
separado do JSON do site — o JSON tem o nome de exibição em pt-BR, que não
serve como prompt.
"""
import os
import sys
from pathlib import Path

os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")

LARGURA, ALTURA = 896, 1152
PASSOS = 30
SEMENTE_BASE = 77

# Paleta amarrada ao tipo — a mesma regra do gerador que já roda em produção
# (site/cartas-source/), para a arte dizer o mesmo que o selo da carta.
#
# A Restrição Celestial carrega um NEGATIVO próprio, e isso não é detalhe: na
# primeira leva o Toji saiu com aura laranja mesmo com "absolutely no glow" no
# positivo. Pedir ausência de algo no prompt positivo não funciona — o modelo
# lê "glow" e desenha glow. Ausência se pede no negativo.
PALETA = {
    # O negativo do feiticeiro veta laranja/amarelo porque na primeira leva a
    # Nobara puxou a cena inteira para o tom do cabelo dela e o ciano sumiu.
    # Numa grade de cartas isso quebra a leitura: a cor é o que diz o tipo.
    "feiticeiro": (
        "cyan cursed energy aura, cold blue rim light",
        "orange, yellow, fire, warm lighting, red aura",
    ),
    "maldicao": ("crimson and violet cursed aura, red backlight", "cyan, blue aura"),
    "restricao": (
        "steel grey and bone white, matte flat lighting",
        "glowing, glow, aura, cursed energy, fire, sparks, bloom, lens flare, "
        "orange, warm lighting, colorful",
    ),
}

# tag danbooru, tipo, traço visual que o modelo precisa ouvir
PERSONAGENS = [
    ("gojo", "gojou satoru", "feiticeiro", "1boy, white hair, blindfold over eyes, black high-collar uniform"),
    ("sukuna", "ryoumen sukuna (jujutsu kaisen)", "maldicao", "1boy, pink hair, four eyes, black facial markings, tattoos, evil grin"),
    ("toji", "fushiguro touji", "restricao", "1boy, black hair, scar on lips, dark shirt, holding a katana"),
    ("yuji", "itadori yuuji", "feiticeiro", "1boy, pink hair, undercut, black school uniform, determined expression"),
    ("megumi", "fushiguro megumi", "feiticeiro", "1boy, black spiky hair, green eyes, black school uniform, serious"),
    ("nobara", "kugisaki nobara", "feiticeiro", "1girl, short orange hair, brown eyes, black school uniform, confident smirk"),
]

# Tags de qualidade recomendadas pelo card do Animagine 4.0; o NoobAI responde
# ao mesmo vocabulário.
#
# Mantenha o conjunto curto. O CLIP do SDXL corta em 77 tokens, e como as tags
# de qualidade ficam no FIM do prompt, são justamente elas que se perdem — na
# primeira leva o log avisou que "absurdres, highres, newest" foi truncado.
QUALIDADE = "masterpiece, best quality, absurdres"
NEGATIVO = (
    "lowres, bad anatomy, bad hands, text, error, missing finger, extra digits, "
    "fewer digits, cropped, worst quality, low quality, low score, bad score, "
    "average score, signature, watermark, username, blurry, multiple views, "
    "full body, chibi, 3d, realistic, photo"
)


def main():
    checkpoint = Path(sys.argv[1])
    saida = Path(sys.argv[2])
    rotulo = checkpoint.stem.split("-")[0].lower()
    saida.mkdir(parents=True, exist_ok=True)

    import torch
    from diffusers import StableDiffusionXLPipeline

    print(f"Carregando {checkpoint.name}...", flush=True)
    pipe = StableDiffusionXLPipeline.from_single_file(
        str(checkpoint), torch_dtype=torch.float16, use_safetensors=True
    ).to("cuda")
    # Mesma lição do container-generate-video-ai: SDXL em 12 GB só fecha a conta
    # com VAE fatiado e cache limpo entre as imagens.
    pipe.enable_vae_slicing()
    pipe.enable_vae_tiling()
    pipe.set_progress_bar_config(disable=True)

    for indice, (ident, tag, tipo, traco) in enumerate(PERSONAGENS):
        destino = saida / f"{ident}-{rotulo}.png"
        if destino.exists():
            print(f"  {destino.name} já existe — pulando", flush=True)
            continue
        paleta, negativo_extra = PALETA[tipo]
        prompt = (
            f"{traco}, {tag}, jujutsu kaisen, upper body, looking at viewer, "
            f"{paleta}, dark background, trading card illustration, {QUALIDADE}"
        )
        negativo = f"{NEGATIVO}, {negativo_extra}" if negativo_extra else NEGATIVO
        semente = SEMENTE_BASE + indice
        print(f"  [{ident}] seed={semente}", flush=True)
        gerador = torch.Generator("cuda").manual_seed(semente)
        imagem = pipe(
            prompt=prompt,
            negative_prompt=negativo,
            width=LARGURA,
            height=ALTURA,
            num_inference_steps=PASSOS,
            guidance_scale=6.0,
            generator=gerador,
        ).images[0]
        imagem.save(destino)
        torch.cuda.empty_cache()
    print(f"OK — amostras em {saida}", flush=True)


if __name__ == "__main__":
    main()
