FROM python:3.11.4-slim-bullseye AS prod

# Install required system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    wget \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Go
ENV GO_VERSION=1.24.2
RUN wget -q https://golang.org/dl/go${GO_VERSION}.linux-amd64.tar.gz \
    && tar -C /usr/local -xzf go${GO_VERSION}.linux-amd64.tar.gz \
    && rm go${GO_VERSION}.linux-amd64.tar.gz

# Add Go to PATH
ENV PATH=$PATH:/usr/local/go/bin
ENV GOPATH=/root/go
ENV PATH=$PATH:$GOPATH/bin

# Install Nuclei
RUN go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest

# Install poetry
RUN pip install poetry==1.8.2

# Configure poetry
RUN poetry config virtualenvs.create false
RUN poetry config cache-dir /tmp/poetry_cache

# Copy requirements
COPY pyproject.toml poetry.lock /app/src/
WORKDIR /app/src

# Install Python dependencies
RUN --mount=type=cache,target=/tmp/poetry_cache poetry install --only main

# Clean up build dependencies but keep nuclei and its requirements
RUN apt-get purge -y gcc \
    && apt-get autoremove -y \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    # Keep git as it's needed for nuclei template updates
    && apt-get update && apt-get install -y --no-install-recommends git

# Copy application code
COPY . /app/src/
RUN --mount=type=cache,target=/tmp/poetry_cache poetry install --only main

# Update Nuclei templates
RUN nuclei -update-templates

CMD ["/usr/local/bin/python", "-m", "launch_check_api"]

FROM prod AS dev

RUN --mount=type=cache,target=/tmp/poetry_cache poetry install
