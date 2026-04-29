# Troubleshooting — Pipeline ELT (Airflow + Airbyte + dbt)

> Ce document recense les bugs non-évidents rencontrés pendant la construction du pipeline. Si une étape du Quick Start échoue, cherche le symptôme ici.

---

## 1. Airbyte — Token endpoint pas exposé sur le port 8000

**Problème** : L'ingress Kubernetes d'Airbyte (port 8000) ne route que le frontend et `/api/v1/connector_builder`. Le token endpoint `/api/v1/applications/token` retourne du HTML → `JSONDecodeError`.

Le vrai API server tourne sur le pod `airbyte-abctl-server` port **8001**, accessible uniquement via `kubectl port-forward`.

**Fix** : Dans `start.sh` :

```bash
kubectl wait --kubeconfig ~/.airbyte/abctl/abctl.kubeconfig \
  -n airbyte-abctl pod -l app=airbyte-server \
  --for=condition=Ready --timeout=120s

kubectl port-forward --kubeconfig ~/.airbyte/abctl/abctl.kubeconfig \
  -n airbyte-abctl \
  svc/airbyte-abctl-airbyte-server-svc 8001:8001 &
```

Dans `stop.sh` :

```bash
pkill -f "port-forward.*airbyte-server" || true
```

> Port **8000** = ingress (UI + appels métier). Port **8001** = token endpoint uniquement.

---

## 2. SDK Airbyte — Trois bugs OAuth2 à patcher

Le provider Airflow utilise le SDK Python `airbyte-api==0.53.0`. Ce SDK contient trois bugs quand utilisé avec `abctl`.

### Bug A — credentials envoyés en form-encoded au lieu de JSON

Le SDK envoie la requête de token en `application/x-www-form-urlencoded`, mais Airbyte attend du JSON. Réponse vide. `JSONDecodeError: Expecting value: line 1 column 1 (char 0)`.

### Bug B — urljoin écrase le path du server_url

`sdk_configuration.get_server_details()` retire silencieusement le slash final. Donc `urljoin('http://host.docker.internal:8001/api', 'v1/applications/token')` produit `.../v1/...` au lieu de `.../api/v1/...`. Cette URL renvoie le frontend HTML avec un 200. `JSONDecodeError`.

**Fix** : Mettre l'URL absolue complète dans le champ Schema de la connexion Airflow. Si `urlparse(token_url).netloc` est non-vide, le SDK court-circuite `urljoin` :

```text
Schema = http://host.docker.internal:8001/api/v1/applications/token
```

### Bug C — token_type absent de la réponse Airbyte

Airbyte renvoie `{"access_token": "..."}` sans champ `token_type`. Le SDK vérifie `token_type == "Bearer"` et lève une exception.

### Fix cumulé dans le Dockerfile

```dockerfile
RUN sed -i \
    -e 's/self\.client\.post(token_url, data=payload)/self.client.post(token_url, json=payload)/' \
    -e 's/if response_data\.get("token_type") != "Bearer":/if False and response_data.get("token_type") != "Bearer":/' \
    /home/airflow/.local/lib/python3.13/site-packages/airbyte_api/_hooks/clientcredentials.py
```

> Toujours rebuilder avec `--no-cache` — le `RUN sed` est mis en cache et peut s'appliquer sur une vieille version du SDK.

---

## 3. Provider Airflow — /api/v1/ vs /api/public/v1/

**Problème** : Une fois les bugs SDK résolus, le token est obtenu mais les appels métier renvoient `403 Forbidden`. Le provider appelle `/api/v1/jobs` (API interne) qui rejette le token applicatif. L'API correcte est `/api/public/v1/jobs`.

**Référence** : [GitHub Issue apache/airflow#41365](https://github.com/apache/airflow/issues/41365)

**Fix** : Mettre le chemin complet jusqu'à `/v1` dans le champ Host. Le SDK fait `remove_suffix(url, '/')` puis concatène `/jobs` :

```text
Host = http://host.docker.internal:8000/api/public/v1
```

---

## 4. abctl local uninstall efface toutes les configurations Airbyte

Chaque `abctl local uninstall` (appelé dans `stop.sh`) supprime toutes les sources, destinations et connexions. Au redémarrage il faut tout recréer dans l'UI (`localhost:8000`) :

1. Source Postgres — host : `source_postgres`, port `5433`, db `source_db`
2. Destination Postgres — host : `destination_postgres`, port `5434`, db `destination_db`
3. Connection entre les deux — noter le nouveau `connectionId`
4. Mettre à jour `CONN_ID` dans `airflow/dags/elt_dag.py`

---

## Connexion Airflow vers Airbyte (valeurs qui fonctionnent)

| Champ | Valeur |
| ----- | ------ |
| Connection Id | `airbyte` |
| Connection Type | `Airbyte` |
| Host | `http://host.docker.internal:8000/api/public/v1` (cf. §3) |
| Schema | `http://host.docker.internal:8001/api/v1/applications/token` (cf. §2B) |
| Login | Client-Id depuis `abctl local credentials` |
| Password | Client-Secret depuis `abctl local credentials` |
