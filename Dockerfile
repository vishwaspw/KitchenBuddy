FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -r requirements.txt

# Clean up any old .pyc and __pycache__ files
RUN find . -name "*.pyc" -delete && find . -name "__pycache__" -delete

COPY . .

CMD ["gunicorn", "app:app"] 