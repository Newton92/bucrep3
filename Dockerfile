from python:3.12.11-alpine3.22

RUN apk add --no-cache --virtual .build-deps musl-dev linux-headers \
    g++ gcc zlib-dev make python3-dev jpeg-dev py3-pip py3-pillow \
    py3-cffi py3-brotli pango postgresql-dev fontconfig ttf-freefont \
    font-noto terminus-font \
    && fc-cache -f

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt && pip install gunicorn

COPY . .

VOLUME ["/app/static", "/app/media", "/app/main/media", "/app/main/static"]

CMD ["gunicorn", "-t", "300", "--workers", "5", "--bind", "0.0.0.0:80", \
    "bucrep.wsgi", "--access-logfile", "a.log", "--error-logfile", \
    "err.log", "--log-level", "debug"]
