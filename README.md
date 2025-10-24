# Dash To-Do List App

This is a simple to-do list web application built with Dash and Plotly. It is configured for deployment on Google Cloud Run and uses Google Cloud Storage for file attachments.

## Features

- Add new tasks
- Edit existing tasks
- Delete tasks
- Mark tasks as complete or incomplete
- Attach files or images to tasks (stored in Google Cloud Storage)
- Download task attachments securely
- Data is stored in the browser session

## Running Locally

### With Python

1.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

2.  **Set up authentication (for GCS access):**
    You need to authenticate with Google Cloud. The easiest way is to use the gcloud CLI:
    ```bash
    gcloud auth application-default login
    ```

3.  **Set the bucket name environment variable:**
    The app needs to know which GCS bucket to use.
    - **Windows (Command Prompt):**
      ```cmd
      set GCS_BUCKET_NAME=ojt252_bucket
      ```
    - **Windows (PowerShell):**
      ```powershell
      $env:GCS_BUCKET_NAME="ojt252_bucket"
      ```
    - **Linux/macOS:**
      ```bash
      export GCS_BUCKET_NAME=ojt252_bucket
      ```

4.  **Run the app:**
    ```bash
    python app.py
    ```
    The app will be available at `http://127.0.0.1:8050/`.

### With Docker Compose

1.  **Build and run the container:**
    ```bash
    docker-compose up
    ```
    The app will be available at `http://localhost:8050/`. Note: Docker Compose setup does not include GCS credentials by default and is intended for basic local testing.

## Deploying to Google Cloud Run

This project is designed to be deployed to Google Cloud Run using Google Cloud Build.

### Prerequisites

1.  **Google Cloud Project:** You must have a Google Cloud project with billing enabled.
2.  **Enable APIs:** Ensure the following APIs are enabled in your project:
    - Cloud Build API
    - Cloud Run Admin API
    - Identity and Access Management (IAM) API
    - Cloud Storage API
3.  **Create a GCS Bucket:** Create a Google Cloud Storage bucket. The name `ojt252_bucket` is hardcoded in the deployment configuration.
4.  **Create a Service Account:** Create a service account that Cloud Run will use to access the GCS bucket.
5.  **Grant Permissions:** Grant the service account the **Storage Object Admin** (`roles/storage.objectAdmin`) role on your GCS bucket. This allows the application to read, write, and delete files.

### Deployment Steps

1.  **Update `cloudbuild.yaml`:**

    Before deploying, you need to replace the placeholder values in the `cloudbuild.yaml` file:
    - `YOUR_PROJECT_ID`: Your Google Cloud project ID.
    - `YOUR_SERVICE_NAME`: The desired name for your Cloud Run service (e.g., `dash-todo-list`).
    - `YOUR_REGION`: The Google Cloud region where you want to deploy the service (e.g., `us-central1`).
    - `YOUR_SERVICE_ACCOUNT`: The full email address of the service account you created (e.g., `your-service-account@your-project-id.iam.gserviceaccount.com`).

2.  **Submit the build:**

    Run the following command from your terminal to start the deployment process:
    ```bash
    gcloud builds submit --config cloudbuild.yaml .
    ```

    This command will trigger Cloud Build to build the Docker image, push it to Google Container Registry, and deploy it to Cloud Run. Once the deployment is complete, the command will output the URL of your live application.
