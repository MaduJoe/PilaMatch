# ============================================================
# Stage 1: Builder - install build tools and Python packages
# ============================================================
FROM python:3.11-slim AS builder

WORKDIR /build

# Install build-time system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies into a virtual env for clean copy
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ============================================================
# Stage 2: Runtime - minimal image with only what we need
# ============================================================
FROM python:3.11-slim

WORKDIR /app

# Install runtime-only system dependencies
#   - libpq5: shared library required by asyncpg / psycopg2
#   - postgresql-client: provides pg_isready used in entrypoint.sh
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy pre-built virtual env from builder stage
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Create non-root user
RUN groupadd --system appgroup && \
    useradd --system --gid appgroup --home-dir /app --no-create-home appuser && \
    chown -R appuser:appgroup /app

# Copy application code
COPY --chown=appuser:appgroup . .

# Create uploads directory with proper permissions
RUN mkdir -p /app/uploads && chown -R appuser:appgroup /app/uploads

# Make entrypoint executable
RUN chmod +x entrypoint.sh

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check - verify the /health endpoint responds
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD ["python", "-c", "import httpx; r = httpx.get('http://localhost:8000/health', timeout=5); assert r.status_code == 200"]

# Run the entrypoint script
ENTRYPOINT ["./entrypoint.sh"]
