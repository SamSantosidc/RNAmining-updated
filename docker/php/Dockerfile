FROM php:7.2.2-fpm

MAINTAINER Thaís Ratis <thaisratis@gmail.com>


COPY docker/php/config/php.ini /usr/local/etc/php/php.ini
COPY environment.yml /tmp/rnamining-environment.yml


# PHP 7.2 is based on Debian Stretch, whose repositories are archived.
# Debian Stretch is archived. These repositories are only used
# temporarily to reproduce the legacy PHP environment.
RUN printf '%s\n' \
        'deb [trusted=yes] http://archive.debian.org/debian stretch main' \
        'deb [trusted=yes] http://archive.debian.org/debian-security stretch/updates main' \
        > /etc/apt/sources.list \
    && printf 'Acquire::Check-Valid-Until "false";\n' \
        > /etc/apt/apt.conf.d/99archive \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        libzip-dev \
        zlib1g-dev \
    && docker-php-ext-install zip \
    && rm -rf /var/lib/apt/lists/*

# DOWNLOAD SCRIPT ANACONDA
RUN curl https://repo.anaconda.com/archive/Anaconda3-2020.07-Linux-x86_64.sh --output /opt/Anaconda3-2020.07-Linux-x86_64.sh
RUN chmod +x /opt/Anaconda3-2020.07-Linux-x86_64.sh

RUN /opt/Anaconda3-2020.07-Linux-x86_64.sh -b -p /usr/local/anaconda3

RUN rm /opt/Anaconda3-2020.07-Linux-x86_64.sh

RUN /usr/local/anaconda3/bin/conda env create --file /tmp/rnamining-environment.yml \
    && /usr/local/anaconda3/bin/conda clean --all --yes \
    && rm /tmp/rnamining-environment.yml

ENV PATH="/usr/local/anaconda3/envs/rnamining/bin:${PATH}"
