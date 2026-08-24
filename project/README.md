# sentinews-mlops

The MLOps pipeline artifact for the thesis *Pregled tehnologij MLOps*. Scaffolding only — the
stages are stubs. See `../.claude/CLAUDE.md` for the locked decisions and version pins.

## Reproduction (target state)

```bash
cp .env.example .env
docker compose up -d          # MinIO, MLflow + Postgres, API, Prometheus, Grafana
uv sync
dvc pull                      # data + models from the MinIO remote
dvc repro                     # ingest -> prepare -> train -> evaluate -> reference
```

| Service | URL |
|---|---|
| MLflow | http://localhost:5000 |
| API (FastAPI docs) | http://localhost:8000/docs |
| MinIO console | http://localhost:9001 |
| Prometheus | http://localhost:9090 |
| Grafana | http://localhost:3000 |

## Layout

```
src/           ingest, prepare, train, evaluate, reference + api/ and simulate/
tests/         pytest suite (+ ~50-article fixture)
monitoring/    prometheus.yml, grafana provisioning, Evidently drift job
dvc.yaml       the five pipeline stages — DVC's DAG is the orchestrator
params.yaml    ingest cutoff + all hyperparameters
```

## Not done yet

- DVC remote not initialised (`dvc remote add -d minio s3://dvc`, endpoint `http://localhost:9000`)
- MinIO / Prometheus / Grafana image tags still need exact pins
- Corpus not downloaded; `params.ingest.until` slice dates depend on the real date distribution
- Licence: the code is to be released under GPL-3.0 (`LICENSE` not yet added)
