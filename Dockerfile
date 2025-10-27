# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the dependencies file to the working directory
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application's code to the working directory
COPY . .

# Create the uploads directory
RUN mkdir uploads

# Expose the port the app runs on
EXPOSE 8080

# Run app.py when the container launches
# The container must listen on the port defined by the PORT environment variable
CMD ["gunicorn", "-b", "0.0.0.0:$PORT", "app:server"]
