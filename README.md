# Dash To-Do List App

This is a simple to-do list web application built with Dash and Plotly.

## Features

- Add new tasks
- Edit existing tasks
- Delete tasks
- Data is stored in the browser session

## Running Locally

1.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

2.  **Run the app:**
    ```bash
    python app.py
    ```

    The app will be available at `http://127.0.0.1:8050/`.

## Deploying to Google Cloud Run

This project is configured for deployment to Google Cloud Run using Cloud Build.

1.  **Enable the Cloud Build, Cloud Run, and Container Registry APIs in your GCP project.**

2.  **Set your project ID:**
    ```bash
    gcloud config set project YOUR_PROJECT_ID
    ```

3.  **Submit the build:**
    ```bash
    gcloud builds submit --config cloudbuild.yaml .
    ```

This will build the Docker image, push it to Google Container Registry, and deploy it to Cloud Run.
