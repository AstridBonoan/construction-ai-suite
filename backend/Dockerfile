FROM python:3.11-slim
WORKDIR /app

# Install runtime dependencies
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.11-slim
WORKDIR /app

# Install runtime dependencies
COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code into the image (context is ./backend)
COPY . .

ENV PYTHONPATH=/app

# Use Gunicorn to serve the Flask app in production
CMD ["gunicorn", "app.main:app", "-b", "0.0.0.0:5000", "--workers", "2", "--threads", "4"]
COPY requirements.txt .
