FROM python:3.13-alpine@sha256:9ba6d8cbebf0fb6546ae71f2a1c14f6ffd2fdab83af7fa5669734ef30ad48844

WORKDIR /app
COPY images/sync/dashboard/server.py /app/server.py
COPY images/sync/dashboard/static /app/static

ENV DASHBOARD_HOST=0.0.0.0
ENV DASHBOARD_PORT=8080
ENV DASHBOARD_BASE_PATH=/dashboard
ENV DB_SYNC_DATA_DIR=/data

USER 65532:65532
EXPOSE 8080

CMD ["python", "/app/server.py"]
