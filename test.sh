#!/usr/bin/env bash
set -e

if ! docker compose ps --status running | grep -q web; then
    echo "El servicio 'web' no está corriendo. Ejecutá ./run.sh primero."
    exit 1
fi

echo "Corriendo tests con cobertura de ramas..."
docker compose exec web coverage run manage.py test

echo ""
echo "Reporte de cobertura:"
docker compose exec web coverage report -m
