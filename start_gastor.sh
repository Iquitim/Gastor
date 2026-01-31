#!/bin/bash

echo "🚀 Iniciando Gastor..."

# Inicia os containers em background e recria se necessário
docker compose up -d --build

echo "⏳ Aguardando serviços inicializarem..."
# Aguarda um pouco para os serviços subirem antes de abrir o navegador
sleep 5

echo "🌍 Abrindo navegador..."
# Abre o navegador padrão no Linux
if command -v xdg-open &> /dev/null; then
    xdg-open http://localhost
elif command -v gnome-open &> /dev/null; then
    gnome-open http://localhost
else
    echo "⚠️  Não foi possível detectar o comando para abrir o navegador automaticamente."
fi

echo "✅ Gastor rodando! Acesse http://localhost se o navegador não abrir."
