#!/bin/bash

# 1. Initialise la base de données Airflow et crée l'utilisateur admin
docker compose up init-airflow -d

sleep 5

# 2. Lance tous les services Airflow (webserver, scheduler, dag-processor) + les deux Postgres
docker compose up -d

sleep 5

# 3. Déploie Airbyte dans le cluster Kubernetes kind local
#    (si déjà installé, cette commande est idempotente)
abctl local install

sleep 10

# 4. Attend que le pod API Airbyte soit prêt avant d'ouvrir le tunnel
kubectl wait --kubeconfig ~/.airbyte/abctl/abctl.kubeconfig \
  -n airbyte-abctl pod -l app=airbyte-server \
  --for=condition=Ready --timeout=120s

# 5. Expose le token endpoint Airbyte sur le port 8001
#    (l'ingress port 8000 ne route pas ce endpoint, port-forward obligatoire)
pkill -f "port-forward.*8001" 2>/dev/null || true

kubectl port-forward --kubeconfig ~/.airbyte/abctl/abctl.kubeconfig \
  -n airbyte-abctl \
  svc/airbyte-abctl-airbyte-server-svc 8001:8001 &
