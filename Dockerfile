FROM python:3.11-slim

WORKDIR /app

# Avoid buffering so logs flush immediately.
ENV PYTHONUNBUFFERED=1

# Install Python deps (empty files are fine; pip will no-op).
COPY requirements.txt .
RUN if [ -s requirements.txt ]; then pip install --no-cache-dir -r requirements.txt; fi

# Application source.
COPY src ./src
COPY data ./data

# Use exec-form so the Python process receives OS signals directly.
ENTRYPOINT ["python"]
CMD ["src/mimir_generator.py"]
