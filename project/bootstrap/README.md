# Bootstrap

Ročno, enkrat: namesti Argo CD. Vse ostalo nato namešča Argo CD iz gita.

- `00-namespace.yaml` – namespace `gitops`
- `01-subscription.yaml` – Argo CD Operator (`community-operators`, kanal `alpha`), izvožen iz konzole, brez `startingCSV`
- `02-argocd.yaml` – instanca Argo CD z Route (privzeto reencrypt)

Dokumentacija operatorja: https://github.com/argoproj-labs/argocd-operator/tree/master/docs

```sh
oc apply -f project/bootstrap/
```

Na novem clustru `02-argocd.yaml` pade z `no matches for kind "ArgoCD"`, dokler operator ni `Succeeded`. Počakaj in ponovi.

Prijava kot `admin`, geslo:

```sh
oc extract secret/argocd-cluster -n gitops --to=-
```

Odstranitev: izbriši instanco ArgoCD, odstrani operator, izbriši `gitops`.
