ls
cd data
ls
gsutil cp iris.csv gs://mlops-course-citric-aleph-461515-j9-unique/data
pip freeze >> requirements.txt
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip list
clear
git init
dvc init
pip install dvc
dvc init
dvc add iris.csv
dvc add data/iris.csv
pip install --upgrade dvc[gs]
dvc add data/iris.csv
rm -rf .dvc
dvc init
dvc add data/iris.csv
rm .dvc/*.sqlite
ls -l .dvc | grep .sqlite
clear
ls
ls data/
pwd
cd data
ls
pwd
gsutil cp iris.csv gs://mlops-course-citric-aleph-461515-j9-unique/data
clear
pip install 'feast[gcp]'
feast init iris_feature_repo
cd iris_feature_repo
bq mk iris_dataset
bq load --autdetect iris_dataset.iris_table gs://mlops-course-citric-aleph-461515-j9-unique/data/iris.csv
bq load --autodetect iris_dataset.iris_table gs://mlops-course-citric-aleph-461515-j9-unique/data/iris.csv
feast apply
cd ..
feast apply
cd iris_feature_repo/feature_repo
feast apply
feast apply
feast apply
feast apply
feast apply
feast apply
echo ".ipynb_checkpoints" > .feastignore
feast apply
feast apply
feast apply
feast apply
feast apply
feast apply
feast apply
feast apply
feast apply
feast apply
feast apply
gcloud app create --region=nam5
gcloud app create --region=us-central1
gcloud app create --region=us
gcloud services enable firestore.googleapis.com appengine.googleapis.com
gcloud firestore databases create --region=us-central
gcloud firestore databases create --region=us-central1
gcloud firestore databases create --location=us-central
feast apply
feast apply
feast apply
feast apply
feast apply
feast apply
feast apply
feast apply
feast materialize 2025-01-01T00:00:00 2026-01-01T00:00:00
feast materialize 2025-01-01T00:00:00 2026-01-01T00:00:00
feast materialize 202301-01T00:00:00 2023-12-31T00:00:00
feast materialize 2023-01-01T00:00:00 2023-12-31T00:00:00
feast apply
feast materialize 2025-01-01T00:00:00 2025-12-31T00:00:00
feast apply
