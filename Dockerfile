# Use an official Python runtime as a parent image
FROM python:3.9

# Set the working directory to /app
WORKDIR /app
COPY requirements.txt requirements.txt

# Install any needed packages specified in requirements.txt
RUN pip3 install -r requirements.txt
# RUN pip install --trusted-host pypi.python.org -r requirements.txt

# Copy the current directory contents into the container at /app
COPY . .

# Make port 80 available to the world outside this container
# EXPOSE 80
# EXPOSE 443

# Define environment variable
# ENV NAME World

# Run bot.py when the container launches
CMD ["python3", "app.py"]
