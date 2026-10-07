# Use standard slim python image
FROM python:3.10-slim

# Set the working directory
WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Expose the port Uvicorn will run on
EXPOSE 8000

# Start the FastAPI application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
