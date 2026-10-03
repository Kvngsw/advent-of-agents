FROM python:3.11-slim

# Create a non-root user
RUN groupadd -g 10001 sandbox && \
    useradd -u 10001 -g sandbox -m -s /bin/bash sandbox

WORKDIR /app

# Install dependencies
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy server code
COPY server.py /app/server.py

# Set permissions
RUN chown -R sandbox:sandbox /app

USER sandbox

EXPOSE 8080

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8080"]
