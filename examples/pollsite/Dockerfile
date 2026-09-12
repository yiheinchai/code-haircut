# Production image: record the real test suite against full Django, then
# replace the install with the sliced copy.
#
# Build from the repository root:
#   docker build -f examples/pollsite/Dockerfile .

FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml README.md /tmp/code-haircut/
COPY haircut /tmp/code-haircut/haircut
RUN pip install --no-cache-dir /tmp/code-haircut "django>=4.2,<6"

COPY examples/pollsite /app

RUN haircut build --django -o /tmp/slim -- python manage.py test \
 && haircut apply /tmp/slim --yes \
 && rm -rf /tmp/slim /tmp/code-haircut .haircut

EXPOSE 8000
ENV PYTHONUNBUFFERED=1
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
