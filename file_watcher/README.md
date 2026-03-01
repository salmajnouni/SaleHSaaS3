# File Watcher Service

This is a simple, lightweight Python service that acts as the automated trigger for the entire data processing workflow.

## How it Works

1.  **Polling**: The service continuously polls the `/data/incoming` directory every 10 seconds.
2.  **Detection**: When it finds one or more new files, it picks them up for processing.
3.  **API Call**: For each file, it sends a `POST` request to the `salehsaas_pipeline` service (`http://salehsaas_pipeline:8001/process-file/`).
4.  **Archiving**: 
    - Upon a successful API response (HTTP 200), it moves the processed file to the `/data/processed` directory, prepending a timestamp to the filename.
    - If the API returns an error, it moves the file to the `/data/failed` directory for manual inspection.

This service ensures that any document you drop into the `incoming` folder is automatically ingested into your local AI brain without any manual intervention.
