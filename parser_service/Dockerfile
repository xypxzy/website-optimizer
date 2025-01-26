FROM python:3.12-slim

# Install build dependencies
RUN apt-get update && apt-get install -y \
    libffi-dev \
    libssl-dev \
    wget \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -r requirements.txt

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libnss3 \
    libgconf-2-4 \
    libfontconfig1 \
    && rm -rf /var/lib/apt/lists/*

COPY . .

ENV PYTHONPATH=/app
ENV GOOGLE_CHROME_BIN=/usr/bin/google-chrome

EXPOSE 50051

CMD ["python", "app/main.py"]
