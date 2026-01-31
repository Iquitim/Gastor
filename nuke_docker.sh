#!/bin/bash
# Nuke Docker Script - Limpeza Total

echo "======================================================="
echo "💥 DOCKER NUKE - LIMPEZA PROFUNDA 💥"
echo "======================================================="
echo "ATENÇÃO: Este script irá DELETAR:"
echo "  - Todos os containers (parados ou rodando)"
echo "  - Todas as imagens"
echo "  - Todos os volumes (dados do banco serão perdidos!)"
echo "  - Todas as redes"
echo "======================================================="
echo "Pressione Ctrl+C em 5 segundos para cancelar... ou espere para continuar."
sleep 5

echo "1. Parando containers..."
docker stop $(docker ps -aq) 2>/dev/null

echo "2. Removendo containers..."
docker rm $(docker ps -aq) 2>/dev/null

echo "3. Removendo imagens..."
docker rmi -f $(docker images -q) 2>/dev/null

echo "4. Removendo volumes..."
docker volume rm $(docker volume ls -q) 2>/dev/null

echo "5. Removendo redes..."
docker network prune -f 2>/dev/null

echo "6. Limpeza final de sistema..."
docker system prune -a --volumes -f

echo "======================================================="
echo "✅ LIMPEZA CONCLUÍDA! O Docker está zerado."
echo "======================================================="
