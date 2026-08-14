#!/usr/bin/env python3
"""Capas 16:9 para posts do jujutsu-kaisen.com — o outro consumo do site.

1216x832 é a razão 16:9 mais próxima que o SDXL tem entre as resoluções em que
foi treinado. Gerar em 1920x1080 direto produz corpos duplicados; o caminho é
gerar aqui e escalar depois.

uso: gera_capa.py <checkpoint> <destino> "<ident>|<prompt>" ...
"""
import os
import sys
from pathlib import Path

os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")

LARGURA, ALTURA = 1216, 832
NEGATIVO = (
    "lowres, bad anatomy, bad hands, text, error, cropped, worst quality, "
    "low quality, signature, watermark, username, blurry, multiple views, "
    "trading card frame, border, logo"
)
QUALIDADE = "masterpiece, best quality, absurdres"


def main():
    checkpoint, destino = Path(sys.argv[1]), Path(sys.argv[2])
    destino.mkdir(parents=True, exist_ok=True)

    import torch
    from diffusers import StableDiffusionXLPipeline

    print(f"Carregando {checkpoint.name}...", flush=True)
    pipe = StableDiffusionXLPipeline.from_single_file(
        str(checkpoint), torch_dtype=torch.float16, use_safetensors=True
    ).to("cuda")
    pipe.enable_vae_slicing()
    pipe.enable_vae_tiling()
    pipe.set_progress_bar_config(disable=True)

    for indice, bruto in enumerate(sys.argv[3:]):
        ident, corpo = bruto.split("|", 1)
        alvo = destino / f"capa-{ident}.png"
        if alvo.exists():
            continue
        print(f"  [{ident}]", flush=True)
        imagem = pipe(
            prompt=f"{corpo}, jujutsu kaisen, {QUALIDADE}",
            negative_prompt=NEGATIVO,
            width=LARGURA,
            height=ALTURA,
            num_inference_steps=30,
            guidance_scale=6.0,
            generator=torch.Generator("cuda").manual_seed(1200 + indice),
        ).images[0]
        imagem.save(alvo)
        torch.cuda.empty_cache()
    print(f"OK — capas em {destino}", flush=True)


if __name__ == "__main__":
    main()
