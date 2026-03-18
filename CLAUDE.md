# ETL Monorepo — bootcamp-ockm

## Stack
- Python 3.11+ com type hints obrigatórios
- GCP: Cloud Run Jobs, BigQuery, Cloud Storage, Secret Manager
- IaC: Terraform 1.5+
- CI/CD: Cloud Build (cloudbuild.yaml)
- Validação: Pydantic v2
- Retry: Tenacity com exponential backoff
- Docker: imagem única para N jobs (monorepo pattern)

## Arquitetura de dados
- Raw: GCS `raw/` em Parquet
- Trusted: BigQuery dataset `trusted` (dados limpos e tipados)
- Refined: BigQuery dataset `refined` (dados consolidados)

## Convenções de código
- Structured logging em JSON (campos obrigatórios: event, job, timestamp, valid_records, dlq_records, duration_seconds, success)
- Dead Letter Queue (DLQ) para registros inválidos — nunca descartar silenciosamente
- Schemas Pydantic em `schemas/` — um arquivo por entidade
- Secrets via Secret Manager, NUNCA em .env commitado ou hardcoded
- Testes com pytest em `tests/` — mínimo: happy path + edge cases + DLQ

## Estrutura de jobs
- Cada job em `etl-monorepo/jobs/{job_name}/` com `main.py` + `config.yaml`
- Template base em `jobs/job_template/`
- Scaffold via `make init JOB={nome}` (roda `scripts/init_job.py`)
- Um Terraform file por job: `infra/job_{nome}.tf`

## Módulos compartilhados
- `shared/gcs.py` — helpers GCS
- `shared/bq.py` — helpers BigQuery
- `shared/api_client.py` — HTTP client genérico

## Segurança
- Service account com least privilege (roles específicas, nunca Editor/Owner)
- Security groups: nunca 0.0.0.0/0
- .env é gitignored — usar .env-exemplo como referência

## Terraform
- Provider Google em `infra/main.tf`
- Módulo reutilizável em `infra/modules/cloud_run_job/`
- Projeto: mestrado-insper, região: us-central1
