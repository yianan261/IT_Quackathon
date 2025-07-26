FROM python:3.11-slim

WORKDIR /app/backend

# Install system dependencies for Playwright and browser automation
RUN apt-get update && apt-get install -y \
    build-essential \
    wget \
    gnupg \
    software-properties-common \
    libnss3 \
    libatk-bridge2.0-0 \
    libdrm2 \
    libxkbcommon0 \
    libgtk-3-0 \
    libgbm-dev \
    libasound2 \
    && rm -rf /var/lib/apt/lists/*

# Copy Python dependencies first (for Docker layer caching)
COPY backend/requirements.txt .

# Install Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright and browsers
RUN playwright install chromium
RUN playwright install-deps chromium

# Copy your application code
COPY ./backend .

# Create directory for browser profiles and screenshots
RUN mkdir -p /app/backend/app/services/chrome_profile
RUN mkdir -p /app/backend/app/navigation_screenshots

# Set proper permissions
RUN chmod -R 755 /app/backend

EXPOSE 8000

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"] 