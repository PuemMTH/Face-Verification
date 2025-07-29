FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY pyproject.toml uv.lock ./
RUN pip install uv && uv pip install --system -e .

# Copy application code
COPY . .

# Create uploads directory
RUN mkdir -p uploads

# Set environment variables to suppress TensorFlow warnings
ENV TF_CPP_MIN_LOG_LEVEL=2
ENV GLOG_minloglevel=2

# Run the application
CMD ["python", "main.py"] 