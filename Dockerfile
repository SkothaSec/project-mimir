FROM python:3.11.8-slim

WORKDIR /app

# Avoid buffering so logs flush immediately.
ENV PYTHONUNBUFFERED=1

# Create non-root user.
RUN addgroup --system app && adduser --system --ingroup app app

# Install Python deps (empty files are fine; pip will no-op).
COPY requirements.txt .
RUN if [ -s requirements.txt ]; then pip install --no-cache-dir -r requirements.txt; fi

# Application source.
COPY src ./src
COPY data ./data

# Use exec-form so the Python process receives OS signals directly.
USER app
ENTRYPOINT ["python"]
CMD ["src/main.py"]
