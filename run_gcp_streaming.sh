#!/bin/bash

# GCP Real-time Image Classification Automation Script
set -e

# Configuration
PROJECT_ID="${PROJECT_ID:-innate-empire-468812-h0}"
REGION="${REGION:-us-central1}"
ZONE="${ZONE:-us-central1-c}"
CLUSTER_NAME="${CLUSTER_NAME:-dataproc-cluster}"
BUCKET_NAME="${BUCKET_NAME:-${PROJECT_ID}-streaming}"

TOPIC_NAME="image-classification-topic"
SUBSCRIPTION_NAME="image-classification-sub"

INPUT_PATH="gs://${BUCKET_NAME}/streaming-input"
OUTPUT_PATH="gs://${BUCKET_NAME}/streaming-output"
APP_PATH="gs://${BUCKET_NAME}/app"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_dependencies() {
    log_info "Checking dependencies..."
    
    local missing=0
    
    for cmd in gcloud gsutil bq python3; do
        if ! command -v $cmd &> /dev/null; then
            log_error "$cmd is required but not installed"
            missing=$((missing + 1))
        fi
    done
    
    if [ $missing -gt 0 ]; then
        log_error "$missing dependencies missing. Please install them first."
        exit 1
    fi
    
    # Check authentication
    if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
        log_error "Not authenticated with gcloud. Run 'gcloud auth login' first."
        exit 1
    fi
    
    gcloud config set project $PROJECT_ID
    log_success "Dependencies validated"
}

enable_apis() {
    log_info "Enabling required GCP APIs..."
    
    local apis=(
        "compute.googleapis.com"
        "dataproc.googleapis.com"
        "storage.googleapis.com"
    )
    
    for api in "${apis[@]}"; do
        gcloud services enable $api --project=$PROJECT_ID --quiet
    done
    
    log_success "APIs enabled"
}

setup_storage() {
    log_info "Setting up Cloud Storage..."
    
    # Create bucket if it doesn't exist
    if ! gsutil ls -b gs://$BUCKET_NAME &>/dev/null; then
        gsutil mb -p $PROJECT_ID -c STANDARD -l $REGION gs://$BUCKET_NAME
        log_success "Created bucket: gs://$BUCKET_NAME"
    else
        log_info "Bucket already exists: gs://$BUCKET_NAME"
    fi
    
    # Create directory structure
    echo "Ready for streaming" | gsutil cp - gs://$BUCKET_NAME/streaming-input/README.txt
    echo "Results output" | gsutil cp - gs://$BUCKET_NAME/streaming-output/README.txt
    echo "Application files" | gsutil cp - gs://$BUCKET_NAME/app/README.txt
    
    log_success "Storage setup completed"
}

setup_dataproc_cluster() {
    log_info "Setting up Dataproc cluster..."
    
    if gcloud dataproc clusters describe $CLUSTER_NAME --region=$REGION &>/dev/null; then
        local state=$(gcloud dataproc clusters describe $CLUSTER_NAME --region=$REGION --format="value(status.state)")
        if [ "$state" = "RUNNING" ]; then
            log_info "Cluster already running: $CLUSTER_NAME"
            return 0
        else
            log_warning "Cluster exists but not running. State: $state"
            gcloud dataproc clusters delete $CLUSTER_NAME --region=$REGION --quiet
        fi
    fi
    
    log_info "Creating new Dataproc cluster with external IPs..."
    gcloud dataproc clusters create $CLUSTER_NAME \
        --region=$REGION \
        --zone=$ZONE \
        --num-masters=1 \
        --num-workers=2 \
        --worker-machine-type=e2-standard-2 \
        --master-machine-type=e2-standard-2 \
        --master-boot-disk-size=30GB \
        --worker-boot-disk-size=30GB \
        --max-age=3h \
        --public-ip-address \
        --initialization-actions=gs://goog-dataproc-initialization-actions-${REGION}/python/pip-install.sh \
        --metadata=PIP_PACKAGES="tensorflow pillow pandas pyarrow" \
        --quiet
    
    log_success "Dataproc cluster created: $CLUSTER_NAME"
}

upload_application_files() {
    log_info "Uploading application files to GCS..."
    
    # Upload Python files
    gsutil cp gcp_streaming_classifier.py gs://$BUCKET_NAME/app/
    gsutil cp image_processor.py gs://$BUCKET_NAME/app/
    gsutil cp requirements.txt gs://$BUCKET_NAME/app/
    
    # Upload model if it exists
    if [ -f "trained_flower_model.keras" ]; then
        gsutil cp trained_flower_model.keras gs://$BUCKET_NAME/app/
        log_success "Uploaded trained model"
    else
        log_warning "No trained model found, will use MobileNetV2"
    fi
    
    log_success "Application files uploaded"
}

submit_streaming_job() {
    log_info "Submitting Spark streaming job to Dataproc..."
    
    gcloud dataproc jobs submit pyspark \
        gs://$BUCKET_NAME/app/gcp_streaming_classifier.py \
        --cluster=$CLUSTER_NAME \
        --region=$REGION \
        --py-files=gs://$BUCKET_NAME/app/image_processor.py \
        --properties="spark.sql.streaming.checkpointLocation=gs://$BUCKET_NAME/checkpoints" \
        -- \
        --project-id=$PROJECT_ID \
        --bucket=$BUCKET_NAME \
        --input-path=$INPUT_PATH \
        --output-path=$OUTPUT_PATH \
        --cluster=$CLUSTER_NAME
    
    log_success "Streaming job submitted"
}

simulate_data() {
    log_info "Starting data simulation..."
    
    if [ ! -d "sample_images" ]; then
        log_error "sample_images directory not found"
        return 1
    fi
    
    local image_count=$(find sample_images -name "*.jpg" | wc -l)
    if [ $image_count -eq 0 ]; then
        log_error "No .jpg files found in sample_images/"
        return 1
    fi
    
    log_info "Found $image_count sample images"
    log_info "Uploading images every 10 seconds for real-time simulation..."
    
    local count=0
    for image_file in sample_images/*.jpg; do
        [ -e "$image_file" ] || continue
        
        local filename=$(basename "$image_file")
        local flower_type=$(echo "$filename" | cut -d'_' -f1)
        local timestamp=$(date +%s)
        local target_file="${timestamp}_${filename}"
        
        gsutil cp "$image_file" "gs://${BUCKET_NAME}/streaming-input/${target_file}"
        
        count=$((count + 1))
        log_success "Uploaded image $count: $flower_type -> $target_file"
        
        if [ $count -lt $image_count ]; then
            sleep 10
        fi
    done
    
    log_success "Data simulation completed: $count images uploaded"
}

monitor_job() {
    log_info "Monitoring streaming job..."
    log_info "Job logs will appear below. Press Ctrl+C to stop monitoring."
    
    # Get the latest job ID
    local job_id=$(gcloud dataproc jobs list \
        --cluster=$CLUSTER_NAME \
        --region=$REGION \
        --filter="status.state=RUNNING" \
        --format="value(reference.jobId)" \
        --limit=1)
    
    if [ -z "$job_id" ]; then
        log_error "No running jobs found"
        return 1
    fi
    
    log_info "Monitoring job: $job_id"
    gcloud dataproc jobs wait $job_id --region=$REGION --project=$PROJECT_ID
}

show_results() {
    log_info "Checking results..."
    
    local result_files=$(gsutil ls gs://$BUCKET_NAME/streaming-output/*.json 2>/dev/null | wc -l)
    
    if [ $result_files -gt 0 ]; then
        log_success "Found $result_files result files"
        
        log_info "Sample results:"
        gsutil ls gs://$BUCKET_NAME/streaming-output/*.json | head -3 | while read file; do
            echo "File: $(basename $file)"
            gsutil cat "$file" | python3 -m json.tool
            echo "---"
        done
    else
        log_warning "No result files found yet"
    fi
}

cleanup() {
    log_info "Cleaning up resources..."
    
    # Stop any running jobs
    local jobs=$(gcloud dataproc jobs list \
        --cluster=$CLUSTER_NAME \
        --region=$REGION \
        --filter="status.state=RUNNING" \
        --format="value(reference.jobId)")
    
    for job_id in $jobs; do
        gcloud dataproc jobs kill $job_id --cluster=$CLUSTER_NAME --region=$REGION --quiet
        log_info "Stopped job: $job_id"
    done
    
    # Delete cluster
    gcloud dataproc clusters delete $CLUSTER_NAME --region=$REGION --quiet
    log_success "Cluster deleted"
    
    # Optionally clean up bucket
    read -p "Delete storage bucket gs://$BUCKET_NAME? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        gsutil -m rm -r gs://$BUCKET_NAME
        log_success "Bucket deleted"
    fi
}

show_status() {
    log_info "System Status:"
    
    # Cluster status
    local cluster_state=$(gcloud dataproc clusters describe $CLUSTER_NAME --region=$REGION --format="value(status.state)" 2>/dev/null || echo "NOT_FOUND")
    echo "Cluster: $cluster_state"
    
    # Running jobs
    local running_jobs=$(gcloud dataproc jobs list --cluster=$CLUSTER_NAME --region=$REGION --filter="status.state=RUNNING" --format="value(reference.jobId)" 2>/dev/null | wc -l)
    echo "Running jobs: $running_jobs"
    
    # Bucket status
    if gsutil ls -b gs://$BUCKET_NAME &>/dev/null; then
        echo "Bucket: EXISTS"
        local input_files=$(gsutil ls gs://$BUCKET_NAME/streaming-input/*.jpg 2>/dev/null | wc -l)
        local output_files=$(gsutil ls gs://$BUCKET_NAME/streaming-output/*.json 2>/dev/null | wc -l)
        echo "Input images: $input_files"
        echo "Output results: $output_files"
    else
        echo "Bucket: NOT_FOUND"
    fi
}

show_menu() {
    echo
    echo "GCP Real-time Image Classification"
    echo "1. Full Setup (recommended)"
    echo "2. Setup Infrastructure Only"
    echo "3. Start Streaming Job"
    echo "4. Simulate Data"
    echo "5. Monitor Job"
    echo "6. Show Results"
    echo "7. Show Status"
    echo "8. Cleanup All"
    echo "9. Exit"
    echo
}

full_setup() {
    log_info "Starting full setup..."
    
    check_dependencies
    enable_apis
    setup_storage
    setup_dataproc_cluster
    upload_application_files
    submit_streaming_job
    
    log_success "Full setup completed!"
    log_info "Next steps:"
    echo "- Run option 4 to simulate data"
    echo "- Run option 5 to monitor the job"
    echo "- Run option 6 to see results"
}

main() {
    if [ $# -eq 0 ]; then
        while true; do
            show_menu
            read -p "Choose an option (1-9): " choice
            case $choice in
                1) full_setup ;;
                2) check_dependencies; enable_apis; setup_storage; setup_dataproc_cluster ;;
                3) upload_application_files; submit_streaming_job ;;
                4) simulate_data ;;
                5) monitor_job ;;
                6) show_results ;;
                7) show_status ;;
                8) cleanup ;;
                9) log_info "Goodbye!"; exit 0 ;;
                *) log_error "Invalid option. Please choose 1-9." ;;
            esac
            echo
            read -p "Press Enter to continue..."
        done
    else
        case "$1" in
            "setup") full_setup ;;
            "infra") check_dependencies; enable_apis; setup_storage; setup_dataproc_cluster ;;
            "start") upload_application_files; submit_streaming_job ;;
            "simulate") simulate_data ;;
            "monitor") monitor_job ;;
            "results") show_results ;;
            "status") show_status ;;
            "cleanup") cleanup ;;
            *) echo "Usage: $0 [setup|infra|start|simulate|monitor|results|status|cleanup]"; exit 1 ;;
        esac
    fi
}

# Set trap for cleanup on exit
trap 'log_warning "Script interrupted"' INT

main "$@"
