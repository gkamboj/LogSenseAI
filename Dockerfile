# flask_app/Dockerfile
FROM python:3.12-slim

# Set the working directory
WORKDIR /app

# Copy Flask application source code
COPY . .

# Install Flask dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Make port 8501 available to the world outside this container
EXPOSE 8501

# Define environment variable
ENV PORT 8501

# Run streamlit when the container launches
#CMD ["sh", "-c", "streamlit", "run", "app.py", "--server.port", "8501", "--server.address", "0.0.0.0"]
CMD ["sh", "-c", "streamlit run app.py"]