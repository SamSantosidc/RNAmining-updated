FROM php:8.5.8-fpm-trixie

LABEL org.opencontainers.image.authors="Thaís Ratis <thaisratis@gmail.com>"

ARG MINIFORGE_VERSION=26.3.2-2
ARG MINIFORGE_SHA256=42260ffe3830fb953d5eee1bbb32229ff06aa7c3833c1ed7a9a0420a95685d94

COPY docker/php/config/php.ini /usr/local/etc/php/php.ini
COPY environment.yml /tmp/rnamining-environment.yml

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        libzip-dev \
        zlib1g-dev \
    && docker-php-ext-install -j"$(nproc)" zip \
    && rm -rf /var/lib/apt/lists/*

RUN curl -fsSL \
        "https://github.com/conda-forge/miniforge/releases/download/${MINIFORGE_VERSION}/Miniforge3-${MINIFORGE_VERSION}-Linux-x86_64.sh" \
        --output /tmp/miniforge.sh \
    && echo "${MINIFORGE_SHA256}  /tmp/miniforge.sh" | sha256sum --check --strict \
    && bash /tmp/miniforge.sh -b -p /opt/conda \
    && rm /tmp/miniforge.sh \
    && /opt/conda/bin/conda env create --file /tmp/rnamining-environment.yml \
    && /opt/conda/bin/conda clean --all --yes \
    && rm /tmp/rnamining-environment.yml

ENV PATH="/opt/conda/envs/rnamining/bin:${PATH}"
