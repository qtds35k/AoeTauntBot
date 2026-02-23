# Use an official lightweight Python image
FROM python:3.11-slim

# Install ffmpeg, required for playing audio in discord
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    rm -rf /var/lib/apt/lists/*

# Set the working directory to /app
WORKDIR /app

# Copy dependency definition and install
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Run bot.py when the container launches
CMD ["python", "bot/bot.py"]
