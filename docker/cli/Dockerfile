FROM debian:trixie-slim AS builder

LABEL org.opencontainers.image.title="RNAmining CLI"
LABEL org.opencontainers.image.description="Coding-potential prediction for RNA sequences"
LABEL org.opencontainers.image.source="https://github.com/SamSantosidc/RNAmining-updated"

ARG MINIFORGE_VERSION=26.3.2-2
ARG MINIFORGE_SHA256=42260ffe3830fb953d5eee1bbb32229ff06aa7c3833c1ed7a9a0420a95685d94
ENV RNAMINING_PROJECT_DIR=/opt/rnamining
ENV RNAMINING_MODEL_DIR=/opt/rnamining/models/coding_prediction
ENV PATH="/opt/conda/envs/rnamining/bin:/opt/conda/bin:${PATH}"

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates curl bzip2 \
    && rm -rf /var/lib/apt/lists/*

COPY docker/cli/runtime-environment.yml /tmp/rnamining-runtime-environment.yml

RUN curl -fsSL \
        "https://github.com/conda-forge/miniforge/releases/download/${MINIFORGE_VERSION}/Miniforge3-${MINIFORGE_VERSION}-Linux-x86_64.sh" \
        --output /tmp/miniforge.sh \
    && echo "${MINIFORGE_SHA256}  /tmp/miniforge.sh" | sha256sum --check --strict \
    && bash /tmp/miniforge.sh -b -p /opt/conda \
    && rm /tmp/miniforge.sh \
    && /opt/conda/bin/conda env create --file /tmp/rnamining-runtime-environment.yml \
    && /opt/conda/bin/conda clean --all --yes \
    && rm /tmp/rnamining-runtime-environment.yml

WORKDIR ${RNAMINING_PROJECT_DIR}
COPY pyproject.toml README.md ./
COPY src ./src
COPY models ./models

RUN /opt/conda/envs/rnamining/bin/python -m pip install --no-deps --no-build-isolation . \
    && rm -rf /opt/conda/envs/rnamining/lib/python3.14*/site-packages/pip \
        /opt/conda/envs/rnamining/lib/python3.14*/site-packages/pip-*.dist-info \
        /opt/conda/envs/rnamining/lib/python3.14*/site-packages/setuptools \
        /opt/conda/envs/rnamining/lib/python3.14*/site-packages/setuptools-*.dist-info \
        /opt/conda/envs/rnamining/lib/python3.14*/site-packages/setuptools-*.egg-info \
        /opt/conda/envs/rnamining/lib/python3.14*/site-packages/pkg_resources \
    && rm -f /opt/conda/envs/rnamining/bin/pip* \
    && /opt/conda/envs/rnamining/bin/python -c "import rnamining; import rnamining.inference; print(rnamining.__version__)"

FROM debian:trixie-slim

LABEL org.opencontainers.image.title="RNAmining CLI"
LABEL org.opencontainers.image.description="Coding-potential prediction for RNA sequences"
LABEL org.opencontainers.image.source="https://github.com/SamSantosidc/RNAmining-updated"

ARG APP_VERSION=1.1.0

ENV RNAMINING_PROJECT_DIR=/opt/rnamining
ENV RNAMINING_MODEL_DIR=/opt/rnamining/models/coding_prediction
ENV PATH="/opt/conda/envs/rnamining/bin:${PATH}"

WORKDIR ${RNAMINING_PROJECT_DIR}

# The builder's source tree, build tools, datasets, and caches do not enter
# the final image. The installed package contains the CLI and resources.
COPY --from=builder /opt/conda/envs/rnamining /opt/conda/envs/rnamining
COPY --from=builder /opt/rnamining/models/coding_prediction ./models/coding_prediction

RUN python -c "import rnamining; print(rnamining.__file__)" \
    && python -c "import rnamining.inference; print('inference runtime ready')"

LABEL org.opencontainers.image.version="${APP_VERSION}"
