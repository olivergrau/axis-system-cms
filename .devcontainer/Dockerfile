FROM mcr.microsoft.com/devcontainers/python:1-3.11-bookworm

# Remove problematic yarn sources
RUN rm -f /etc/apt/sources.list.d/yarn.list \
    /etc/apt/sources.list.d/yarn*.list

# Install system packages
RUN apt-get update && apt-get install -y \
    git \
    curl \
    wget \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (important for caching)
COPY requirements.txt /tmp/pip-tmp/requirements.txt

# Install Python dependencies
RUN pip install --upgrade pip \
    && pip install -r /tmp/pip-tmp/requirements.txt \
    && rm -rf /tmp/pip-tmp