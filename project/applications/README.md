# Aplikacije

Vsaka mapa s `config.yaml` postane Argo CD aplikacija z imenom mape (ustvari jo ApplicationSet v `bootstrap/03-appset.yaml`).

- `config.yaml` – za Argo CD: namespace in Helm chart
- `values.yaml` – za Helm: values za chart

Kako dodati novo aplikacijo? Nova mapa z obema datotekama, push, Sync v Argo CD.

