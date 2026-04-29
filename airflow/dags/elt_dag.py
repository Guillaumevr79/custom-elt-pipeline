from datetime import datetime
#from airflow.decorators import dag, task
from airflow import DAG
from docker.types import Mount
# from airflow.providers.standard.operators.python import PythonOperator
from airflow.providers.airbyte.operators.airbyte import AirbyteTriggerSyncOperator
from airflow.providers.docker.operators.docker import DockerOperator
import subprocess
import sys

CONN_ID = '691ed787-dd48-411e-a346-6d3b87846608'

default_args = {
    'owner':'airflow',
    'depends_on_past':False,
    'email_on_failure':False,
    'email_on_retry':False,
}

# def run_elt_script():
#     script_path = "/opt/airflow/elt/elt_script.py"
#     result = subprocess.run([sys.executable, script_path],
#                             capture_output=True, text=True)
#     if result.returncode != 0:
#         raise Exception(f"Script failed with error: {result.stderr}")
#     else:
#         print(result.stdout)

'''
dag = DAG(
    'elt_and_dbt',
    default_args=default_args,
    description='An ELT workflow with dbt',
    start_date=datetime(2023, 10, 28),
    catchup=False,
)

t1 = PythonOperator(
    task_id="run_elt_script",
    python_callable=run_elt_script,
    dag=dag
)

t2 = DockerOperator(
    task_id="dbt_run",
    image='ghcr.io/dbt-labs/dbt-postgres:1.9.latest@sha256:a705312b55af0ebdd149977914c28502a382d74dca8fe51fff368371a61cc8a7',
    platform='linux/amd64',
    command=[
        "run",
        "--profiles-dir",
        "/root",
        "--project-dir",
        "/opt/dbt"
    ],
    auto_remove=True,
    docker_url="unix://var/run/docker.sock",
    network_mode="bridge",
    mounts=[
        Mount(source='/Users/guillaume/Docs/Formations/Roadmap/ELT/dbt_transformations',
                target='/dbt', type='bind'),
        Mount(source='/Users/guillaume/.dbt',
                target='/dbt', type='bind')
    ],
    dag=dag
)
t1 >> t2
'''

with DAG(
    dag_id='elt_and_dbt',
    start_date=datetime(2024, 1, 1),
    default_args=default_args,
    # schedule_interval="@daily",
    catchup=False
) as dag:
    # t1 = PythonOperator(
    #     task_id="run_elt",
    #     python_callable=run_elt_script
    # )
    t1 = AirbyteTriggerSyncOperator(
        task_id='airbyte_postgres_postgres',
        airbyte_conn_id='airbyte',
        connection_id=CONN_ID,
        asynchronous=False,
        timeout=3600,
        wait_seconds=3
    )

    t2 = DockerOperator(
        task_id="dbt_run",
    image='ghcr.io/dbt-labs/dbt-postgres:1.9.latest@sha256:a705312b55af0ebdd149977914c28502a382d74dca8fe51fff368371a61cc8a7',
    # platform='linux/amd64',
    command=[
        "run",
        "--profiles-dir",
        "/root",
        "--project-dir",
        "/dbt"
    ],
    auto_remove="success",
    docker_url="unix://var/run/docker.sock",
    network_mode="bridge",
    mounts=[
        Mount(source='/Users/guillaume/Docs/Formations/Roadmap/ELT/dbt_transformations',
                target='/dbt', type='bind'),
        Mount(source='/Users/guillaume/.dbt',
                target='/root', type='bind')
        ]
    )

t1 >> t2
