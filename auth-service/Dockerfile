# Use the official Python 3.12 lightweight (slim) base image
FROM python:3.12-slim

# Set /app as the working directory inside the Docker container
# All subsequent commands will execute relative to this directory
WORKDIR /app

# Copy requirements.txt from the host machine into the container's /app directory
# This file contains the Python dependencies required by the application
COPY requirements.txt .

# Install all Python dependencies listed in requirements.txt
# --no-cache-dir avoids storing pip installation cache, reducing image size
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application source code (app.py) into the container's /app directory
COPY app.py .

# Inform Docker that the application listens on port 5000
# This documents the container port; it does not automatically publish the port
EXPOSE 5000

# Define the default command to execute when the container starts
# Runs the Python application using app.py
CMD ["python", "app.py"]