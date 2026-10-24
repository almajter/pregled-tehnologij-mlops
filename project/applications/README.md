# Aplikacije

Vsaka mapa s `config.yaml` postane Argo CD aplikacija z imenom mape (ustvari jo ApplicationSet v `bootstrap/03-appset.yaml`).

- `config.yaml` – za Argo CD: namespace in Helm chart
- `values.yaml` – za Helm: values za chart

Kako dodati novo aplikacijo? Nova mapa z obema datotekama, push, Sync v Argo CD.

## Ročno

`seaweedfs` in `mlflow` potrebujeta Secret `seaweedfs-s3-credentials` v `mlops`, ki se pred prvim Sync ustvari ročno:

    oc create secret generic seaweedfs-s3-credentials -n mlops \
      --from-literal=AWS_ACCESS_KEY_ID=$(openssl rand -hex 10) \
      --from-literal=AWS_SECRET_ACCESS_KEY=$(openssl rand -hex 20)

`vllm` potrebuje Secret `vllm-api-key` v `model-serving` (API ključ za klice na `/v1`):

    oc create secret generic vllm-api-key -n model-serving \
      --from-literal=VLLM_API_KEY=$(openssl rand -hex 24)

