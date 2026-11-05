# Optional container build (untested). If you prefer running directly on Ubuntu,
# use server/scripts/setup_server.sh instead — that is the primary path.
FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
        curl ca-certificates git xz-utils ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Node 20
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && apt-get install -y nodejs

# ffmpeg 7 static (in case the distro package is 5.x/6.x)
RUN ffmpeg -version | head -1 || true

WORKDIR /app
COPY . .

RUN bash server/scripts/setup_server.sh

EXPOSE 8000
CMD ["bash", "server/scripts/run_local.sh"]
