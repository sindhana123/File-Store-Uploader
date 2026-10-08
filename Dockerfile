FROM python:3.10-slim-buster

# Update and install required packages (ffmpeg is crucial for media bots)
RUN apt-get update -y && apt-get install -y \
    ffmpeg \
    git \
    wget \
    curl \
    unzip \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirement and install
COPY requirements.txt requirements.txt
RUN pip3 install -U --no-cache-dir -r requirements.txt

# Copy all source files
COPY . .

EXPOSE 8080

# Run the command
CMD ["python3", "main.py"]
