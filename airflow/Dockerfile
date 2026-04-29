# Image Airflow figée — voir TROUBLESHOOTING.md pour les raisons des patches ci-dessous.
FROM apache/airflow:3.2.1

# Providers Airflow nécessaires au DAG ELT.
# Versions testées et compatibles avec airbyte-api 0.53.0.
RUN pip install --no-cache-dir \
        apache-airflow-providers-docker==4.5.5 \
        apache-airflow-providers-http==6.0.2 \
        apache-airflow-providers-airbyte==5.4.1

# Patches du SDK airbyte-api (cf. TROUBLESHOOTING.md §9 et §11) :
#   1. Le SDK envoie le token request en form-encoded, mais Airbyte attend du JSON.
#   2. Airbyte ne renvoie pas `token_type` dans sa réponse, ce qui fait planter le SDK.
RUN sed -i \
    -e 's/self\.client\.post(token_url, data=payload)/self.client.post(token_url, json=payload)/' \
    -e 's/if response_data\.get("token_type") != "Bearer":/if False and response_data.get("token_type") != "Bearer":/' \
    /home/airflow/.local/lib/python3.13/site-packages/airbyte_api/_hooks/clientcredentials.py

USER root
