FROM python:3.8-slim-buster AS builder

RUN pip install poetry

WORKDIR /build
COPY . .

RUN poetry export -f requirements.txt --output requirements.txt

RUN poetry build

# ---
FROM python:3.8-slim-buster

WORKDIR /app

COPY --from=builder /build/requirements.txt .
RUN pip install -r requirements.txt

COPY --from=builder /build/dist dist
RUN pip install --no-deps dist/*.whl

ENTRYPOINT ["run-applifting-exercise"]