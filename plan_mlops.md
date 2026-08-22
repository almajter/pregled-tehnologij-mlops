# Plan: MLOps thesis artifact — self-hosted LLM app, productionized

Working plan for the BSc thesis *Pregled tehnologij MLOps*. This is the build/ops plan
for the **artifact**; the written thesis maps onto it in §9.

> **Status of this document.** This supersedes the AI-drafted `project/CLAUDE.md`
> "locked decisions" (SentiNews, CPU sklearn sentiment classifier). Those were a
> machine's guesses, never sent to the mentor. The new direction below is the one to
> build against. `project/` is scaffolding and can be replaced wholesale.

---

## 1. What we are building (one paragraph)

Take a **turnkey, open-source, self-hosted LLM application** and take it from
"runs on a laptop" to a **production-grade, reproducible, observed, continuously-evaluated
service** running entirely on our own hardware — no cloud, no per-token cost, no data
leaving the box. The thesis subject is the **operations** around it: reproducible infra,
data/model/prompt versioning, self-hosted CI/CD, automated quality evaluation, monitoring,
and governance. The ML app is a **local RAG assistant** over a document corpus.

## 2. Hard constraints (real, not guessed)

- **Degree:** BSc (diplomsko delo). Scope stays to *one solid path* through each stage.
- **Hardware now:** Lenovo ThinkStation P520 — Xeon W-2235 (6c/12t), 64 GB ECC RAM,
  1 TB NVMe, weak Quadro P620. Proxmox VE 9. **No usable GPU** → everything CPU-only.
- **Hardware later (optional):** RTX 3090 (24 GB). Plan must not depend on it; it is a
  documented upgrade path (faster/larger models, GPU passthrough) = thesis "nadaljnje delo".
- **Everything self-hosted, zero cloud cost**, incl. git + CI/CD (self-hosted **GitLab CE**).
- **Corpus:** Slovene public **administrative procedures** from **gov.si / e-uprava**,
  scoped to 2–3 life-event areas (e.g. vehicles, residence/documents, family/benefits).
  Plain-language Slovene (tractable for a small CPU model), genuinely useful, reproducible,
  and public-sector-information licensing feeds the compliance chapter.
- **Open source & reproducible**: code GPL-3.0, someone can clone and run it.
- Mentor: izr. prof. dr. Slavko Žitnik. Professor's brief = review MLOps generally, then
  build-and-maintain a real ML project across the lifecycle (plan → build → maintain),
  covering versioning, tracking, pipelines/packaging, deployment/CI-CD, monitoring,
  compliance.

## 3. The MLOps substance (what keeps this "MLOps", not "sysadmin")

Because we clone a turnkey app, the ML-specific spine must be explicit and owned by us:

1. **We own the ingestion → chunk → embed → index pipeline** (not the app's built-in RAG).
   That pipeline is a versioned, reproducible artifact (DVC).
2. **We own an automated quality-evaluation loop** — a gold Q&A set + LLM-as-judge that
   runs in CI and **gates deploys**. "Did the answers get worse?" is a first-class,
   measured, blocking concern. This is the line between an MLOps thesis and a DevOps thesis.

Everything else (serving, monitoring, CI/CD, IaC) is the ops scaffolding around those two.

## 4. Tool decisions (per lifecycle stage)

Each row is what we **build with**; the *surveyed alternatives* column is what the thesis
chapter 3 comparison tables must cover. Version pins: **pin whatever is pulled on day one
and never chase upgrades mid-thesis** — record exact tags in `project/versions.md`.

| Stage | Choice (build) | Surveyed alternatives (write about) |
|---|---|---|
| LLM serving runtime | **Ollama** (CPU), Slovene model **GaMS** (smallest usable size) | vLLM, llama.cpp server, LocalAI, TGI |
| Embeddings | **Multilingual** model, Slovene-capable (e.g. bge-m3 / multilingual-e5) | Slovene-specific vs multilingual, small vs large |
| Chat UI / app shell | **Open WebUI** | LibreChat, AnythingLLM, Onyx |
| Vector store | **Qdrant** (self-hosted) | Chroma, Weaviate, pgvector, Milvus |
| Data & index versioning | **DVC + MinIO (S3)** | Git-LFS, LakeFS |
| Experiment/eval tracking + registry | **MLflow + Postgres** | Weights & Biases, Neptune, DVCLive |
| Pipeline / orchestration | **DVC pipelines (`dvc.yaml`)** | Prefect, ZenML, Airflow, Dagster |
| Packaging & serving | **Docker + FastAPI (our RAG API)** | BentoML, KServe, Ray Serve |
| Git + CI/CD + registry | **Self-hosted GitLab CE + GitLab Runner + built-in Container Registry** | GitHub Actions, Jenkins, Gitea+Act, Drone |
| Metrics & dashboards | **Prometheus + Grafana** | VictoriaMetrics, Netdata |
| LLM/RAG quality eval | **Custom harness + LLM-as-judge (Ollama)** | Ragas, DeepEval, promptfoo, TruLens |
| Drift / monitoring | **Evidently + custom retrieval metrics** | NannyML, WhyLabs, Arize Phoenix |
| Governance / compliance | **Model cards + data lineage + EU AI Act mapping** | — (survey the regulatory landscape) |

> **Verify-before-relying (do these; do not assume):**
> - **V1. Open WebUI license.** Confirm the current license permits our use and the
>   thesis's open-source claim (it has a branding clause). If it doesn't fit, fall back to
>   **LibreChat** (MIT). Record the finding in `project/versions.md`.
> - **V2. GitLab CE minimum RAM** for our version; size the container from the official
>   requirement, not a guess.
> - **V3. Slovene model choice** — confirm **GaMS**'s current model sizes and whether it runs
>   under Ollama (GGUF); pick the smallest GaMS usable on the W-2235 and **benchmark tokens/sec**
>   on the actual box. Also confirm a Slovene-capable embedding model. Document the quality
>   ceiling — it is the argument for the GPU upgrade. No guessing: verify before locking.
> - **V4. Corpus legality/reproducibility** — check gov.si `robots.txt`, terms of use, and the
>   public-sector-information reuse license *before* ingesting. Record what is redistributable
>   vs fetch-on-run. This also becomes source material for the compliance chapter.

## 5. Target architecture on Proxmox (`pve` @ 10.0.10.4)

Static IPs come from the container range in `homelab/docs/network.md` (10.0.10.10–.39).

```
pve (Proxmox VE 9, 10.0.10.4)
├── LXC 110  ollama-01   10.0.10.10   EXISTS — Ollama model serving (see note below)
├── LXC 111  gitlab-01   10.0.10.11   GitLab CE + Container Registry (git, CI/CD, images)  [BUILT 2026-08-23]
├── LXC 112  runner-01   10.0.10.12   GitLab Runner (docker executor) — runs CI jobs       [BUILT 2026-08-23]
└── LXC 113  mlops-01    10.0.10.13   Docker host — the whole app+ops stack:
      ├── qdrant            :6333    vector store
      ├── minio             :9000/1  S3 (DVC remote, MLflow artifacts)
      ├── mlflow + postgres :5000    tracking + registry
      ├── rag-api (FastAPI) :8000    OUR retrieval+generate service (/health, /metrics)
      ├── open-webui        :3000    chat UI (product surface)
      ├── prometheus        :9090    metrics
      └── grafana           :3001    dashboards
```

Rationale for separating GitLab/runner from the app host: GitLab is heavy and its lifecycle
(upgrades, restarts) must not disturb the app being measured. Keeping the runner separate
from GitLab is standard and lets CI jobs deploy onto `mlops-01` cleanly.

> **Revised 2026-08-23.** VMIDs shifted: the original layout gave `gitlab-01` VMID 110
> and `mlops-01` 10.0.10.10, both already held by the running `ollama-01`.
>
> **Ollama stays on its own container** rather than becoming a compose service on
> `mlops-01`. Model weights are pulled at runtime regardless, so embedding it buys no
> reproducibility that pinning does not; a separate container is a cleaner GPU-passthrough
> target for the 3090 upgrade; and `OLLAMA_BASE_URL` is the swappable-backend abstraction
> needed to discuss vLLM/llama.cpp as alternatives. **Open WebUI does move into
> `mlops-01`'s compose file** — its wiring to `rag-api` is thesis content and must be
> version-controlled. Consequence: `ollama-01` is now thesis infrastructure and its
> version + model tags get pinned in `versions.md`.
>
> Reproducibility (C1) is therefore claimed honestly: *one command against a running
> model server at `$OLLAMA_BASE_URL`, with weights fetched by a documented bootstrap
> step.*
>
> Full design + build notes:
> `homelab/docs/superpowers/specs/2026-08-23-gitlab-ci-cd-design.md`.

Data-flow of the thing we operate:

```
docs (corpus) ──DVC──> ingest ─> chunk ─> embed(Ollama) ─> upsert ─> Qdrant
                                                                        │
user ──> Open WebUI ──> rag-api ──> retrieve(Qdrant) + prompt(Ollama) ──> answer
                                    │
                          Prometheus scrapes /metrics ; MLflow logs runs+eval
```

---

## 6. Build phases

Each phase is independently demoable and maps to thesis content. **Snapshot before each
phase** (`pct snapshot <vmid> pre-phaseN`). Commit code to GitLab as you go.

Notation: run `pct` / `qm` commands as `root@10.0.10.4`. Inside a container use
`pct enter <vmid>` or `pct exec <vmid> -- <cmd>`. **Record every generated secret/token/version
into `homelab/docs/credentials.md` (index only) and `project/versions.md` (versions).**

### Phase 0 — Proxmox base & the three containers

1. Confirm host health: `pveversion`, `systemctl is-system-running`, `df -h /`, `lvs`.
2. Refresh templates: `pveam update && pveam available --section system | grep debian-13`.
   Download the listed tag: `pveam download local <debian-13-standard_..._amd64.tar.zst>`.
3. Create the Docker app host (`mlops-01`, VMID 100). Docker in an unprivileged LXC needs
   `nesting=1` **and** `keyctl=1`:
   ```sh
   pct create 100 local:vztmpl/<debian-13-standard_..._amd64.tar.zst> \
     --hostname mlops-01 --cores 6 --memory 16384 --swap 2048 \
     --rootfs local-lvm:64 \
     --net0 name=eth0,bridge=vmbr0,ip=10.0.10.10/24,gw=10.0.10.1 \
     --nameserver 10.0.10.1 --searchdomain home.arpa \
     --features nesting=1,keyctl=1 --unprivileged 1 --onboot 1
   ```
4. Create GitLab host (`gitlab-01`, VMID 110) — size RAM per **V2** (start 8192 MB,
   raise if needed):
   ```sh
   pct create 110 local:vztmpl/<debian-13-standard_..._amd64.tar.zst> \
     --hostname gitlab-01 --cores 4 --memory 8192 --swap 4096 \
     --rootfs local-lvm:60 \
     --net0 name=eth0,bridge=vmbr0,ip=10.0.10.11/24,gw=10.0.10.1 \
     --nameserver 10.0.10.1 --searchdomain home.arpa \
     --features nesting=1 --unprivileged 1 --onboot 1
   ```
5. Create Runner host (`runner-01`, VMID 111) — also needs Docker, so `nesting=1,keyctl=1`:
   ```sh
   pct create 111 local:vztmpl/<debian-13-standard_..._amd64.tar.zst> \
     --hostname runner-01 --cores 4 --memory 6144 --swap 2048 \
     --rootfs local-lvm:40 \
     --net0 name=eth0,bridge=vmbr0,ip=10.0.10.12/24,gw=10.0.10.1 \
     --nameserver 10.0.10.1 --searchdomain home.arpa \
     --features nesting=1,keyctl=1 --unprivileged 1 --onboot 1
   ```
6. Start all three; inside each: `apt update && apt full-upgrade -y`, then
   `apt install -y ca-certificates curl git`. Create a non-root sudo user for daily work.
7. Add pfSense DNS entries: `mlops-01`, `gitlab-01`, `runner-01` → their IPs (so
   `http://gitlab-01.home.arpa` resolves). Register these as static/reserved.
8. **Snapshot** all three: `pct snapshot 100 base && pct snapshot 110 base && pct snapshot 111 base`.
9. Document in `homelab/docs/`: new containers in `network.md` topology + IP plan, and in
   `hardware.md`/`proxmox-basics.md` as appropriate.

### Phase 1 — Self-hosted GitLab CE + Runner (the CI/CD foundation)

> **DONE 2026-08-23.** GitLab CE **19.3.0-ce.0** on `gitlab-01` (CT 111), gitlab-runner
> **19.3.0** + Docker 29.7.2 on `runner-01` (CT 112), hello-world pipeline green.
> Steps 1–5 below are amended to what actually works — the original instructions were
> wrong in three places. Build notes:
> `homelab/docs/superpowers/specs/2026-08-23-gitlab-ci-cd-design.md`.

1. On `gitlab-01`, install GitLab CE from the official Omnibus apt repository
   (**record the exact package version installed**). Write `/etc/gitlab/gitlab.rb`
   **before** `apt-get install gitlab-ce` — the postinst runs `reconfigure` itself, so
   settings applied afterwards are too late. It must contain:
   - `external_url 'https://gitlab.alters.si'` — the **final public hostname**, not an
     internal one. GitLab bakes this into clone URLs, registry image prefixes, webhooks
     and CI artifact links; changing it after Phase 6 is a migration.
   - `registry_external_url 'https://registry.home.arpa:5050'` — a *separate, LAN-only*
     hostname, so the UI can be published without exposing the registry.
   - `letsencrypt['enable'] = false` + a self-signed cert. HTTP-01 needs inbound
     reachability, and the WAN is CGNAT.
   - `package["modify_kernel_parameters"] = false` — **without this the install fails.**
     Omnibus sets `kernel.shmall`/`kernel.shmmax` via sysctl, but `/proc/sys/kernel` is
     read-only in an unprivileged LXC. Safe to skip (PostgreSQL 9.3+ uses mmap shm).
2. Retrieve the initial root password (`/etc/gitlab/initial_root_password`), log in,
   **change it within 24 h** — GitLab deletes that file on the first reconfigure after
   24 h. Disable open sign-up (private instance).
3. The Container Registry is enabled by `registry_external_url` in step 1. Verify with
   `docker login registry.home.arpa:5050`.
4. On `runner-01`: install Docker + `gitlab-runner`. The container needs
   `nesting=1,keyctl=1` or the docker executor's overlay2 setup fails.
   **The registration-token flow in the original plan no longer exists** — GitLab 19
   removed `--registration-token`. Instead *create* the runner first (Admin → CI/CD →
   Runners → New, or `Ci::Runner.new(runner_type: :instance_type)` via `gitlab-rails
   runner`), which yields a `glrt-` **authentication** token, then:
   `gitlab-runner register --non-interactive --url https://gitlab.alters.si --token glrt-… --executor docker`.
   **Record the runner token.**
   Then add `extra_hosts` to `/etc/gitlab-runner/config.toml` — job containers do not
   inherit the host's `/etc/hosts`, and this also keeps CI on the direct LAN path once
   the name resolves publicly through Cloudflare:
   `extra_hosts = ["gitlab.alters.si:10.0.10.11", "registry.home.arpa:10.0.10.11"]`
5. Create a blank project `mlops-thesis` on the instance, push a hello-world `.gitlab-ci.yml`
   that runs `echo`, confirm the pipeline goes green. **This proves the whole CI path before
   any real work depends on it.**
6. Decide the git story: this instance is the **primary remote**; optionally mirror to a
   private GitHub repo as off-box backup (git is your real thesis backup).
7. **Snapshot** `gitlab-01` and `runner-01` as `ci-working`.

### Phase 2 — Ollama + a small model (CPU), smoke test

1. Install Docker on `mlops-01` (official apt repo): `docker-ce docker-ce-cli containerd.io
   docker-buildx-plugin docker-compose-plugin`; enable the service; add your user to `docker`.
2. Create the repo skeleton on `mlops-01` (this becomes the git project):
   `infra/` (compose + IaC), `pipeline/` (ingest/embed/eval code), `rag-api/` (FastAPI),
   `eval/` (gold set + judge), `monitoring/` (prometheus/grafana), `docs/`.
3. Start Ollama as a container (compose service `ollama`, volume for models, port 11434).
4. Pull the chosen models per **V3** — a small instruct model (3B–4B class) and a small
   embedding model — and **benchmark tokens/sec on the W-2235**. Record numbers; if too slow,
   step down model size. Lock the choice in `project/versions.md`.
5. Smoke test: `curl` a completion and an embedding through Ollama. Commit + push;
   the CI hello-world still green.

### Phase 3 — The ingestion/embedding pipeline (DVC) + corpus versioning

1. Bring up `minio` + `qdrant` compose services (volumes on the container disk, which is on
   `local-lvm` — not on a root-FS plain dir).
2. `uv init` the `pipeline/` package (Python 3.12). Write stages:
   `ingest` (fetch/collect corpus → `data/raw`), `prepare` (clean/chunk → `data/processed`),
   `embed` (Ollama embeddings → vectors), `index` (upsert to Qdrant + snapshot →
   `data/index`). Wire them as a `dvc.yaml` DAG with `params.yaml` (chunk size, model, top-k).
3. `dvc init`; `dvc remote add -d minio s3://dvc` with endpoint `http://minio:9000`;
   `dvc push`. Now corpus + index are versioned and reproducible: `dvc repro` rebuilds the DAG.
4. **Corpus = gov.si / e-uprava administrative procedures**, scoped to 2–3 life-event areas.
   Ingestion (after **V4** legality check) is scripted and re-runnable — "the corpus changed"
   (a procedure updated, or a new area added) is our drift signal later. Adding an area is
   itself a planned drift experiment. Use **extractive-leaning prompts** (quote/cite retrieved
   passages) so the modest Slovene CPU model stays grounded.
5. **Snapshot** `mlops-01` as `pipeline-working`.

### Phase 4 — RAG API + Open WebUI (the product surface)

1. Build `rag-api` (FastAPI, in `rag-api/`, its own `Dockerfile`): `POST /query` →
   embed question (Ollama) → retrieve top-k (Qdrant) → build prompt → generate (Ollama) →
   return answer + sources. Add `GET /health` (returns model + index version) and
   `GET /metrics` (Prometheus: request latency, tokens, retrieval hits, model_version label).
2. Bring up **Open WebUI** (compose service, volume for its data). Configure it to use Ollama,
   and wire our `rag-api` in as the RAG backend (via Open WebUI's pipelines/functions, or
   point the UI at `rag-api` as an OpenAI-compatible endpoint — pick whichever the current
   Open WebUI supports; **verify, don't guess**). If Open WebUI's license fails **V1**,
   swap to LibreChat here.
3. End-to-end demo: ask a question in the UI, get a grounded answer with citations. This is
   the first "useful product" milestone.
4. Commit; **snapshot** as `app-working`.

### Phase 5 — Evaluation harness + MLflow tracking (the ML spine)

1. Bring up `mlflow` + its `postgres` (artifacts to MinIO `s3://mlflow`).
2. Build a **gold evaluation set** in `eval/`: ~30–60 question/expected-answer pairs over the
   corpus (hand-written; this is real thesis work and must be documented as methodology).
3. Write `eval/run_eval.py`: for each gold question, call `rag-api`, score with
   **LLM-as-judge** (Ollama) on correctness + groundedness, plus retrieval metrics
   (hit@k, MRR). Log every run to MLflow: params (model, chunking, top-k), metrics, artifacts.
4. Register the serving config in MLflow (or a `models.yaml`) with `@staging`/`@production`
   pointers; `rag-api` reports the active version in `/health` and as a metric label.
5. Define **success criteria now, before results** (see §7) and record baseline numbers.
6. Commit; **snapshot** as `eval-working`.

### Phase 6 — CI/CD in GitLab (lint → test → eval-gate → build → deploy)

1. Write `.gitlab-ci.yml` stages:
   - `lint` — ruff + formatting.
   - `test` — pytest (pipeline + rag-api unit tests, ~50-doc fixture).
   - `eval` — spin an ephemeral rag-api against a fixed mini-corpus, run `run_eval.py`,
     **fail the pipeline if macro score drops below threshold** (the deploy gate).
   - `build` — build `rag-api` (and any custom) images, push to the GitLab Container Registry.
   - `deploy` — the runner SSHes/`docker compose pull && up -d` on `mlops-01` (deploy key +
     restricted user; **not** stored in the repo).
2. Prove a bad change (e.g. break the prompt) is **caught by the eval gate** and blocks deploy.
   Screenshot this — it is the headline evidence for the whole thesis.
3. Commit; **snapshot** as `cicd-working`.

### Phase 7 — Observability (Prometheus + Grafana)

1. Bring up `prometheus` (scrape `rag-api:/metrics`, `ollama`, node/cAdvisor for host+GPU-less
   resource use) and `grafana` (provisioned datasource + dashboards from files, not clicked).
2. Dashboards: request rate/latency (p50/p95), tokens/s, retrieval hit rate, error rate,
   CPU/RAM, active model version. Add at least one **alert rule** (e.g. p95 latency or
   error-rate threshold).
3. Commit provisioning as code; **snapshot** as `observability-working`.

### Phase 8 — Monitoring/drift, reliability, governance

1. **Drift/quality-over-time:** schedule (GitLab CI scheduled pipeline) a periodic eval +
   Evidently report over incoming/changed corpus; surface a "quality trend" in Grafana or as
   an MLflow-tracked series. Define what triggers a re-index/re-eval.
2. **Reliability:** implement backup + restore + rollback and *test the restore*:
   - `vzdump` of the three LXCs to `local` (schedule via Datacenter → Backup); document
     restore steps. (Closes the backup TODO in `homelab/docs/maintenance.md`.)
   - DVC-tracked data is reproducible; MinIO/MLflow/Postgres volumes covered by vzdump.
   - Demonstrate a rollback: redeploy a previous image tag from the registry.
3. **Governance/compliance** (professor's "regulation compliance tools"): write a model card
   + data-sheet for the corpus, document data lineage (DVC), and map the system against the
   **EU AI Act** obligations for this class of system (likely limited/minimal-risk — argue it).
   This is a *written* deliverable + light tooling, not a big build.
4. **Snapshot** as `maintain-working`.

### Phase 9 — Evaluation write-up + thesis

Measure against §7 criteria, then write. See §9 for chapter mapping.

---

## 7. Success criteria (define before results, then measure)

These make the evaluation chapter honest (measured, not asserted). Set targets *before*
building the thing each measures.

| # | Criterion | How measured | Target (set at Phase 5) |
|---|---|---|---|
| C1 | Reproducibility | Time/steps from clean clone → running stack | one command + N min |
| C2 | Pipeline reproducibility | `dvc repro` reproduces index bit-for-bit / metrics within ε | yes |
| C3 | Deploy automation | Manual steps to ship a change | 0 (git push → deployed) |
| C4 | Quality gate works | Bad change blocked by CI eval | demonstrated |
| C5 | Answer quality | LLM-judge correctness + groundedness on gold set | baseline + threshold |
| C6 | Retrieval quality | hit@k / MRR on gold set | baseline |
| C7 | Observability coverage | % of key signals dashboarded + alerting present | defined checklist |
| C8 | Recoverability | Restore-from-backup + rollback succeed in a drill | both pass |
| C9 | Serving performance | tokens/s, p95 latency on CPU | measured; GPU = future |

## 8. Risks & mitigations

- **Drifts into pure DevOps** → the §3 spine (owned pipeline + gated eval) is mandatory, not optional.
- **CPU too slow to be usable** → small model + small corpus; document as a known limitation
  and as the motivation for the GPU upgrade (turns a weakness into a thesis argument).
- **Scope creep (BSc)** → one tool per stage built; the rest are *surveyed in writing* only.
- **GitLab resource weight** → dedicated container, raise RAM per V2, snapshot before upgrades.
- **Open WebUI license (V1)** → LibreChat fallback decided in advance.
- **Corpus choice unclear** → decide with mentor early (Phase 3 blocks on it).

## 9. Mapping to the written thesis (Slovene, FRI template)

| Chapter | Content | Fed by |
|---|---|---|
| 1 Uvod | Problem → Rešitev → Cilji → Struktura; repo footnote | this plan |
| 2 MLOps — pregled | MLOps vs DevOps, lifecycle, LLMOps specifics, maturity | §1–3 |
| 3 Pregled orodij | Per-stage survey → comparison tables → justified pick | §4 "surveyed alternatives" |
| 4 Zasnova in arhitektura | Use case, corpus, architecture diagram | §5 |
| 5 Implementacija | Versioning, tracking, pipeline/packaging, deploy/CI-CD, monitoring | Phases 2–8 |
| 6 Vrednotenje in diskusija | Criteria (6.1), results (6.2), discussion (6.3) | §7 |
| 7 Zaključek | Summary + nadaljnje delo (GPU/3090, larger models, fine-tuning) | §2, §8 |

## 10. Immediate next actions (in order)

1. **Mentor alignment** — confirm the topic reframe (LLMOps/self-hosted Slovene RAG, not
   sentiment), the gov.si corpus + scope, and that fully-local + CPU + BSc scope is acceptable.
   *Do this before building.*
2. Run verifications **V1–V4** (Open WebUI license, GitLab RAM, GaMS/embedding benchmark on the
   box, gov.si scraping legality).
3. Fix the **corpus scope** — pick the exact 2–3 gov.si life-event areas.
4. Execute **Phase 0**, documenting into the `homelab` wiki as we go.

> Approval gate: this plan is the design. Building starts only after the mentor-alignment
> step (1) and your go-ahead on the specifics (2–3).
