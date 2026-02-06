FROM node:20-alpine AS ui-builder
WORKDIR /ui
COPY client/package.json client/package-lock.json* ./ 
RUN npm install
COPY client/ ./
RUN npm run build

FROM python:3.11-slim

WORKDIR /app

# Avoid buffering so logs flush immediately.
ENV PYTHONUNBUFFERED=1

# Create non-root user.
RUN addgroup --system app && adduser --system --ingroup app app

# Install Python deps.
COPY requirements.txt .
RUN if [ -s requirements.txt ]; then pip install --no-cache-dir -r requirements.txt; fi

# Application source.
COPY src ./src
COPY --from=ui-builder /ui/dist ./frontend

# Use exec-form so the Python process receives OS signals directly.
USER app
ENTRYPOINT ["python"]
CMD ["src/main.py"]
