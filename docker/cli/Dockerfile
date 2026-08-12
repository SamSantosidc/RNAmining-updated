FROM debian:trixie-slim

LABEL org.opencontainers.image.title="RNAmining CLI"
LABEL org.opencontainers.image.description="Coding-potential prediction for RNA sequences"
LABEL org.opencontainers.image.source="https://github.com/SamSantosidc/RNAmining-updated"

ARG MINIFORGE_VERSION=26.3.2-2
ARG MINIFORGE_SHA256=42260ffe3830fb953d5eee1bbb32229ff06aa7c3833c1ed7a9a0420a95685d94
ARG APP_VERSION=1.0.4

ENV RNAMINING_PROJECT_DIR=/opt/rnamining
ENV RNAMINING_MODEL_DIR=/opt/rnamining/models/coding_prediction
ENV PATH="/opt/conda/envs/rnamining/bin:/opt/conda/bin:${PATH}"

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates curl bzip2 \
    && rm -rf /var/lib/apt/lists/*

COPY environment.yml /tmp/rnamining-environment.yml

RUN curl -fsSL \
        "https://github.com/conda-forge/miniforge/releases/download/${MINIFORGE_VERSION}/Miniforge3-${MINIFORGE_VERSION}-Linux-x86_64.sh" \
        --output /tmp/miniforge.sh \
    && echo "${MINIFORGE_SHA256}  /tmp/miniforge.sh" | sha256sum --check --strict \
    && bash /tmp/miniforge.sh -b -p /opt/conda \
    && rm /tmp/miniforge.sh \
    && /opt/conda/bin/conda env create --file /tmp/rnamining-environment.yml \
    && /opt/conda/bin/conda clean --all --yes \
    && rm /tmp/rnamining-environment.yml

WORKDIR ${RNAMINING_PROJECT_DIR}
COPY pyproject.toml README.md ./
COPY src ./src
COPY models ./models

RUN python -m pip install --no-deps --no-build-isolation . \
    && python -c "import rnamining; print(rnamining.__file__)"

LABEL org.opencontainers.image.version="${APP_VERSION}"

ENTRYPOINT ["rnamining"]
