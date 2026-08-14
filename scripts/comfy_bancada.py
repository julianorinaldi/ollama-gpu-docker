#!/usr/bin/env python3
"""Bancada de comparação de modelos pela API do ComfyUI.

Roda o MESMO conjunto de personagens em modelos de arquiteturas diferentes, com
os parâmetros que cada autor recomenda, e grava tudo em saida/bancada/.

Por que pela API e não por diffusers como os outros scripts: Anima e NetaYume
não são SDXL. O diffusers 0.32 da imagem do container-generate-video-ai não
conhece essas arquiteturas; o ComfyUI conhece. Como a stack já está de pé, sai
mais barato falar com ela do que manter um segundo ambiente Python.

uso: comfy_bancada.py <modelo> [modelo ...]     (sem argumento: lista os nomes)
"""
import json
import sys
import time
import urllib.request

COMFY = "http://localhost:8188"
LARGURA, ALTURA = 896, 1152
SEMENTE_BASE = 77

# Mesma lista dos outros scripts, para a comparação ser direta.
PERSONAGENS = [
    ("gojo", "gojou satoru", "1boy, white hair, blindfold over eyes, black high-collar uniform",
     "cyan cursed energy aura, cold blue rim light", "orange, yellow, fire, warm lighting"),
    ("sukuna", "ryoumen sukuna (jujutsu kaisen)", "1boy, pink hair, four eyes, black facial markings, tattoos, evil grin",
     "crimson and violet cursed aura, red backlight", "cyan, blue aura"),
    ("toji", "fushiguro touji", "1boy, black hair, scar on lips, dark shirt, holding a katana",
     "steel grey and bone white, matte flat lighting",
     "glowing, glow, aura, cursed energy, fire, sparks, bloom, orange, warm lighting, colorful"),
    ("nobara", "kugisaki nobara", "1girl, short orange hair, brown eyes, black school uniform, confident smirk",
     "cyan cursed energy aura, cold blue rim light", "orange, yellow, fire, warm lighting"),
]

NEG_BASE = ("worst quality, low quality, bad anatomy, bad hands, text, watermark, "
            "signature, artist name, blurry, jpeg artifacts, cropped, "
            "trading card frame, border")

# Cada autor recomenda um ponto de operação diferente; comparar todos no mesmo
# sampler seria comparar errado.
MODELOS = {
    # Aesthetic já vem afinado — o card manda NÃO usar score tags nele.
    "anima": {
        "tipo": "unet",
        "unet": "anima-aesthetic-v1.1.safetensors",
        "clip": "qwen_3_06b_base.safetensors",
        "vae": "qwen_image_vae.safetensors",
        "sampler": "er_sde", "scheduler": "normal", "cfg": 4.5, "passos": 30,
        "qualidade": "masterpiece, best quality, safe",
    },
    "anima29": {
        "tipo": "unet",
        "unet": "Anima-2.9B-preview-v1.safetensors",
        "clip": "qwen_3_06b_base.safetensors",
        "vae": "qwen_image_vae.safetensors",
        "sampler": "er_sde", "scheduler": "normal", "cfg": 4.5, "passos": 30,
        "qualidade": "masterpiece, best quality, safe",
    },
    "netayume": {
        "tipo": "checkpoint",
        "checkpoint": "NetaYume_v4_all_in_one.safetensors",
        "sampler": "euler_ancestral", "scheduler": "normal", "cfg": 5.5, "passos": 40,
        "qualidade": "masterpiece, best quality, absurdres",
    },
    "illustrious2": {
        "tipo": "checkpoint",
        "checkpoint": "Illustrious-XL-v2.0.safetensors",
        "sampler": "euler_ancestral", "scheduler": "normal", "cfg": 6.0, "passos": 30,
        "qualidade": "masterpiece, best quality, absurdres",
    },
    # Generalista (Alibaba), Apache-2.0. Entra por curiosidade, não como
    # candidato: é focado em fotorrealismo e provavelmente não conhece os
    # personagens por nome.
    #
    # É destilado: roda em 8 passos com cfg=1. E cfg=1 significa SEM guidance
    # livre de classificador — ou seja, o prompt negativo é simplesmente
    # ignorado. Como as regras de paleta deste projeto moram no negativo
    # (Restrição Celestial "sem brilho"), o Z-Image não consegue obedecê-las.
    "zimage": {
        "tipo": "unet",
        "unet": "z_image_turbo_int8_convrot.safetensors",
        "clip": "qwen_3_4b_fp8_mixed.safetensors",
        "vae": "z_image_ae.safetensors",
        "sampler": "euler", "scheduler": "simple", "cfg": 1.0, "passos": 8,
        "qualidade": "anime illustration, highly detailed",
    },
    # Reprovado na primeira rodada (desenha moldura de carta e marca d'água
    # falsa), mas fica na bancada para a comparação ser completa.
    "noobai": {
        "tipo": "checkpoint",
        "checkpoint": "NoobAI-XL-v1.1.safetensors",
        "sampler": "euler_ancestral", "scheduler": "normal", "cfg": 5.0, "passos": 28,
        "qualidade": "masterpiece, best quality, absurdres",
    },
    # Referência: o que está escolhido hoje, pela mesma API, para a comparação
    # não misturar diferenças de motor com diferenças de modelo.
    "animagine": {
        "tipo": "checkpoint",
        "checkpoint": "animagine-xl-4.0-opt.safetensors",
        "sampler": "euler_ancestral", "scheduler": "normal", "cfg": 6.0, "passos": 30,
        "qualidade": "masterpiece, best quality, absurdres",
    },
}


def grafo(cfg_modelo, positivo, negativo, semente, prefixo):
    """Monta o workflow em formato de API. Os ids são strings, como o ComfyUI espera."""
    if cfg_modelo["tipo"] == "checkpoint":
        carga = {"4": {"class_type": "CheckpointLoaderSimple",
                       "inputs": {"ckpt_name": cfg_modelo["checkpoint"]}}}
        modelo, clip, vae = ["4", 0], ["4", 1], ["4", 2]
    else:
        # O encoder do Anima é detectado pelo próprio state dict (Qwen3-0.6B),
        # então o "type" do CLIPLoader não importa aqui.
        carga = {
            "4": {"class_type": "UNETLoader",
                  "inputs": {"unet_name": cfg_modelo["unet"], "weight_dtype": "default"}},
            "5": {"class_type": "CLIPLoader",
                  "inputs": {"clip_name": cfg_modelo["clip"], "type": "stable_diffusion"}},
            "6": {"class_type": "VAELoader", "inputs": {"vae_name": cfg_modelo["vae"]}},
        }
        modelo, clip, vae = ["4", 0], ["5", 0], ["6", 0]

    g = dict(carga)
    g.update({
        "10": {"class_type": "CLIPTextEncode", "inputs": {"clip": clip, "text": positivo}},
        "11": {"class_type": "CLIPTextEncode", "inputs": {"clip": clip, "text": negativo}},
        # EmptySD3LatentImage cobre latente de 16 canais (Anima/Lumina) e também
        # funciona para SDXL, então um nó só serve os dois caminhos.
        "12": {"class_type": "EmptySD3LatentImage",
               "inputs": {"width": LARGURA, "height": ALTURA, "batch_size": 1}},
        "13": {"class_type": "KSampler", "inputs": {
            "model": modelo, "positive": ["10", 0], "negative": ["11", 0], "latent_image": ["12", 0],
            "seed": semente, "steps": cfg_modelo["passos"], "cfg": cfg_modelo["cfg"],
            "sampler_name": cfg_modelo["sampler"], "scheduler": cfg_modelo["scheduler"],
            "denoise": 1.0}},
        "14": {"class_type": "VAEDecode", "inputs": {"samples": ["13", 0], "vae": vae}},
        "15": {"class_type": "SaveImage", "inputs": {"images": ["14", 0], "filename_prefix": prefixo}},
    })
    return g


def envia(g):
    req = urllib.request.Request(
        f"{COMFY}/prompt", data=json.dumps({"prompt": g}).encode(),
        headers={"Content-Type": "application/json"})
    try:
        return json.load(urllib.request.urlopen(req))["prompt_id"]
    except urllib.error.HTTPError as e:
        # O ComfyUI devolve 400 com o motivo exato da recusa no corpo (nó,
        # campo, valor aceito). Sem isto vira "HTTP Error 400" e nada mais.
        raise RuntimeError(f"ComfyUI recusou o workflow: {e.read().decode()[:1200]}") from None


def espera(pid, limite=900):
    """O /prompt volta na hora; o histórico só ganha a entrada quando termina."""
    inicio = time.time()
    while time.time() - inicio < limite:
        with urllib.request.urlopen(f"{COMFY}/history/{pid}") as r:
            h = json.load(r)
        if pid in h:
            st = h[pid].get("status", {})
            if st.get("status_str") == "error":
                raise RuntimeError(f"ComfyUI falhou: {json.dumps(st)[:400]}")
            return
        time.sleep(3)
    raise TimeoutError(f"{pid} passou de {limite}s")


def main():
    alvos = sys.argv[1:]
    if not alvos:
        print("modelos:", ", ".join(MODELOS))
        return
    for nome in alvos:
        cfg = MODELOS[nome]
        print(f"== {nome} ({cfg['sampler']}/{cfg['scheduler']} cfg={cfg['cfg']} passos={cfg['passos']})", flush=True)
        for i, (ident, tag, traco, paleta, neg_extra) in enumerate(PERSONAGENS):
            positivo = (f"{traco}, {tag}, jujutsu kaisen, upper body, looking at viewer, "
                        f"{paleta}, dark background, {cfg['qualidade']}")
            t0 = time.time()
            espera(envia(grafo(cfg, positivo, f"{NEG_BASE}, {neg_extra}",
                               SEMENTE_BASE + i, f"bancada/{ident}-{nome}")))
            print(f"   {ident}: {time.time()-t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
