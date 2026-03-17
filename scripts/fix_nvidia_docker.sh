#!/bin/bash

# Aborta em caso de erro
set -e

echo "--- Iniciando instalação de drivers NVIDIA no Ubuntu ---"

# 1. Atualiza o sistema
sudo apt update && sudo apt upgrade -y

# 2. Instala dependências comuns
sudo apt install -y build-essential gcc make dkms

# 3. Detecta a versão recomendada do driver para sua GPU
RECOMMENDED_DRIVER=$(ubuntu-drivers devices | grep "recommended" | awk '{print $3}')

if [ -z "$RECOMMENDED_DRIVER" ]; then
    echo "ERRO: Nenhum driver recomendado encontrado. Verifique se a GPU está bem conectada."
    exit 1
fi

echo "--- Instalando o driver recomendado: $RECOMMENDED_DRIVER ---"

# 4. Instala o driver automaticamente
sudo apt install -y $RECOMMENDED_DRIVER

echo "--- Instalação concluída! ---"
echo "IMPORTANTE: Você PRECISA reiniciar o servidor para carregar o driver."
echo "Após reiniciar, rode 'nvidia-smi' para confirmar."
echo "Deseja reiniciar agora? (s/n)"
read response
if [ "$response" == "s" ]; then
    sudo reboot
fi