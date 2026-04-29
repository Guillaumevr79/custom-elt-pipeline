pkill -f "port-forward.*airbyte-server" || true

docker compose down -v

sleep 5

#abctl local uninstall #efface tout le cluster Kubernetes et donc toutes les connexions Airbyte. Après ça, recréer les connexions dans l'UI et mettre à jour CONN_ID


