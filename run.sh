#!/usr/bin/env bash
set -e

echo "Verificando prerrequisitos..."

if ! command -v docker &> /dev/null; then
    echo "Error: Docker no está instalado. Instalalo antes de continuar."
    exit 1
fi

if ! docker compose version &> /dev/null; then
    echo "Error: Docker Compose no está disponible."
    exit 1
fi

if [ ! -f .env ]; then
    echo "No se encontró .env, se crea a partir de .env.example..."
    cp .env.example .env
fi

echo "Levantando servicios (esto puede tardar la primera vez)..."
docker compose up --build -d

echo "Esperando a que la base de datos esté lista..."
until docker compose exec -T db pg_isready -U "$(grep DB_USER .env | cut -d '=' -f2)" &> /dev/null; do
    sleep 1
done

echo "Aplicando migraciones..."
docker compose exec web python manage.py migrate

echo "Cargando datos demo..."
docker compose exec web python manage.py seed_demo_data

echo ""
echo "Listo. La aplicación está corriendo en:"
echo "  http://localhost:8000/"
echo ""
echo "Credenciales demo:"
echo "  Empleado:    empleado1 / demo1234"
echo "  Responsable: responsable1 / demo1234"
echo "  Doble rol:   dual1 / demo1234"