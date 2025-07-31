FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml uv.lock ./
RUN pip install uv
# Restrict uv sync to Python 3.11 only to avoid dependency resolution issues
RUN uv sync --python=3.11
RUN uv pip install -e .
RUN uv clean

COPY . .

RUN mkdir -p uploads

CMD ["uv", "run", "python", "main.py", "--cpu_mode"] 