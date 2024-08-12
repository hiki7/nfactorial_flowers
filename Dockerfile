FROM python:3.12 as requirements-stage

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /tmp
RUN pip install poetry==1.5.0
COPY ./pyproject.toml ./poetry.lock* /tmp/
RUN poetry export -f requirements.txt --output requirements.txt --without-hashes

FROM python:3.12

WORKDIR /code
COPY --from=requirements-stage /tmp/requirements.txt .
RUN pip install --no-cache-dir --upgrade -r ./requirements.txt
COPY . .

ENTRYPOINT ["uvicorn", "--host", "0.0.0.0", "src.main:app"]
