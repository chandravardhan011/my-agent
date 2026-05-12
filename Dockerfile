FROM python:3.11-slim

WORKDIR /app

# Install dependencies first (layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app files
COPY . .

# Create log directory
RUN mkdir -p /app/logs

# Don't run as root
RUN useradd -m appuser && chown -R appuser /app
USER appuser

EXPOSE 5000

CMD ["python", "app.py"]
