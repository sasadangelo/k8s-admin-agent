# Kubernetes Admin Agent Dockerfile
FROM python:3.13-slim

WORKDIR /app

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Install system dependencies and uv
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/* && \
    curl -LsSf https://astral.sh/uv/install.sh | sh

# Add uv to PATH (it installs to ~/.local/bin)
ENV PATH="/root/.local/bin:$PATH"

# Copy project files
COPY --chown=appuser:appuser pyproject.toml /app/
COPY --chown=appuser:appuser README.md /app/
COPY --chown=appuser:appuser src/ /app/src/

# Install Python dependencies using uv
RUN uv pip install --system --no-cache -e .

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health')" || exit 1

# Run the agent
CMD ["uv", "run", "server"]
