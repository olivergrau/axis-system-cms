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
    libgl1 \
    libegl1 \
    libdbus-1-3 \
    libxkbcommon0 \
    libxkbcommon-x11-0 \
    libxcb-cursor0 \
    libxcb-icccm4 \
    libxcb-keysyms1 \
    libxcb-shape0 \
    libwayland-cursor0 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (important for caching)
COPY requirements.txt /tmp/pip-tmp/requirements.txt

# Install Python dependencies
RUN pip install --upgrade pip \
    && pip install -r /tmp/pip-tmp/requirements.txt \
    && pip install mkdocs mkdocs-material pymdown-extensions \
    && rm -rf /tmp/pip-tmp