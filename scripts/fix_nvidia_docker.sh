#!/bin/bash

# Aborta o script em caso de erro
set -e

echo "--- Iniciando a configuração do NVIDIA Container Toolkit ---"

# 1. Adiciona o repositório oficial da NVIDIA
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg \
  && curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
    sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
    sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

# 2. Atualiza a lista de pacotes
sudo apt-get update

# 3. Instala o NVIDIA Container Toolkit
sudo apt-get install -y nvidia-container-toolkit

sudo ubuntu-drivers autoinstall

# 4. Configura o Docker para usar o driver da NVIDIA
sudo nvidia-ctk runtime configure --runtime=docker

# 5. Reinicia o serviço do Docker para aplicar as mudanças
sudo systemctl restart docker

echo "--- Configuração concluída com sucesso! ---"
echo "Tente rodar o seu docker-compose up novamente."