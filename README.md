# Dash To-Do List App

This is a simple to-do list web application built with Dash and Plotly.

## Features

- Add new tasks
- Edit existing tasks
- Delete tasks
- Mark tasks as complete or incomplete
- Attach files or images to tasks
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

    The app will be available at `http://127.0.0.1:8050/`.

### With Docker Compose

1.  **Build and run the container:**
    ```bash
    docker-compose up
    ```

    The app will be available at `http://localhost:8050/`.

## Deploying to Google Cloud Run

This project is configured for deployment to Google Cloud Run using Cloud Build.

1.  **Enable the Cloud Build, Cloud Run, and Container Registry APIs in your GCP project.**

2.  **Create a Google Cloud Storage bucket** and update the `BUCKET_NAME` in `app.py` and `cloudbuild.yaml` with your bucket name.

3.  **Grant the necessary IAM permissions** to the Cloud Build and Cloud Run service accounts.

4.  **Set your project ID:**
    ```bash
    gcloud config set project YOUR_PROJECT_ID
    ```

5.  **Submit the build:**
    ```bash
    gcloud builds submit --config cloudbuild.yaml .
    ```

This will build the Docker image, push it to Google Container Registry, and deploy it to Cloud Run.
