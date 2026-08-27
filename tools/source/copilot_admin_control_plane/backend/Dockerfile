FROM python:3.12-slim

WORKDIR /app
COPY tools/source/copilot_admin_control_plane/backend /app/backend
COPY tools/source/copilot_admin_control_plane/frontend /app/frontend
ENV PYTHONUNBUFFERED=1 \
    COPILOT_ADMIN_BACKEND_HOST=0.0.0.0 \
    COPILOT_ADMIN_BACKEND_PORT=8765 \
    SPS_REPO_ROOT=/workspace \
    COPILOT_ADMIN_FRONTEND_DIR=/app/frontend
EXPOSE 8765
CMD ["python", "-m", "backend.app"]
