FROM python:3.13-slim AS builder
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends build-essential libpq-dev \
    && rm -rf /var/lib/apt/lists/*
COPY requirements/ requirements/
ARG REQUIREMENTS_FILE=requirements/prod.txt
RUN pip install --user -r ${REQUIREMENTS_FILE}

FROM python:3.13-slim
RUN apt-get update && apt-get install -y --no-install-recommends libpq5 curl \
    && rm -rf /var/lib/apt/lists/* && useradd --create-home appuser
WORKDIR /app
COPY --from=builder /root/.local /home/appuser/.local
COPY --chown=appuser:appuser . .
USER appuser
ENV PATH=/home/appuser/.local/bin:$PATH
ENV DJANGO_SETTINGS_MODULE=config.settings.local
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s \
    CMD curl -f http://localhost:8000/ || exit 1
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]