FROM python:3.12-alpine
WORKDIR /srv
COPY app.py mission.py index.html ./
COPY assets/ ./assets/
ENV PYTHONUNBUFFERED=1 PORT=8787 TITANU_DATA_DIR=/data
RUN mkdir -p /data && addgroup -S app && adduser -S app -G app && chown -R app:app /data /srv
USER app
EXPOSE 8787
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 CMD python3 -c "import urllib.request;urllib.request.urlopen('http://127.0.0.1:8787/health',timeout=3)"
CMD ["python3","app.py","--host","0.0.0.0"]