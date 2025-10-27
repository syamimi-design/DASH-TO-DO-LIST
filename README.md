# Dash To-Do List App

This is a simple to-do list web application built with Dash and Plotly. It is configured for deployment on Google Cloud Run and uses local file storage for attachments.

## Features

- Add new tasks
- Edit existing tasks
- Delete tasks
- Mark tasks as complete or incomplete
- Attach files or images to tasks (stored locally)
- Download task attachments
- Data is stored in the browser session

## Running Locally

### With Python

1.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

2.  **Run the app:**
    ```bash
    python app.py
    ```
    The app will be available at `http://127.0.0.1:8050/`. Uploaded files will be stored in the `uploads` directory.

### With Docker Compose

1.  **Build and run the container:**
    ```bash
    docker-compose up
    ```
    The app will be available at `http://localhost:8050/`.

## Deploying to Google Cloud Run

This project is designed to be deployed to Google Cloud Run using Google Cloud Build.

### Prerequisites

1.  **Google Cloud Project:** You must have a Google Cloud project with billing enabled.
2.  **Enable APIs:** Ensure the following APIs are enabled in your project:
    - Cloud Build API
    - Cloud Run Admin API
    - Identity and Access Management (IAM) API

### Deployment Steps

1.  **Update `cloudbuild.yaml`:**

    Before deploying, you should replace `$PROJECT_ID` with your actual Google Cloud project ID in the `cloudbuild.yaml` file.

2.  **Submit the build:**

    Run the following command from your terminal to start the deployment process:
    ```bash
    gcloud builds submit --config cloudbuild.yaml .
    ```

    This command will trigger Cloud Build to build the Docker image, push it to Google Container Registry, and deploy it to Cloud Run. Once the deployment is complete, the command will output the URL of your live application.
