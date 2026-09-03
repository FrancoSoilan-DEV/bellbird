# DELIVERY.md

## Candidato

**[PENDIENTE — completar con tu nombre]**

## Tiempo efectivo dedicado

**[PENDIENTE — completar]** (el enunciado pide informar el tiempo real aproximado, no hay penalización por dedicar más horas)

## Commit final

**[PENDIENTE — completar con el hash del último commit antes de la entrega]**

```bash
git log --oneline -1
```

## Pruebas ejecutadas

```bash
docker compose exec web python manage.py test applications
```

Resultado: **29 tests, todos en verde** (`applications.expenses`) + tests de `applications.users`.

### Cobertura

```bash
docker compose exec web coverage run --branch --source='applications' manage.py test
docker compose exec web coverage report -m
```

Resultado: **100% de cobertura de ramas** sobre `applications/` (mínimo exigido: 85%).