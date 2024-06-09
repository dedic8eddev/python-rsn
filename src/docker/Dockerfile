FROM ubuntu:18.04

ENV LANG="en_US.UTF-8"
ENV LANGUAGE="en_US:en"
ENV LC_ALL="en_US.UTF-8"
ENV DEBIAN_FRONTEND="noninteractive"
ENV TZ="Europe/Pairs"

RUN set -eux; \
	apt-get update; \
	apt-get install -y gosu; \
	rm -rf /var/lib/apt/lists/*; \
# verify that the binary works
	gosu nobody true

RUN apt-get update && apt-get install -y \
    locales \
    python3 \
    cython \
    python3-dev \
    libpq-dev \
    libffi6 \
    libffi-dev \
    libde265-dev \
    x265 \
    libheif-dev \
    libldap2-dev \
    libpq-dev \
    libsasl2-dev \
    python3-pip \
    gdal-data \
    libgdal-dev \
    python3-gdal \
    git \
    automake \
    gcc \
    vim \
    nano \
    poppler-utils \
    bash-completion \
    wget && \
    apt-get clean

RUN wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add - && \
    echo "deb http://apt.postgresql.org/pub/repos/apt/ bionic-pgdg main" |tee /etc/apt/sources.list.d/pgdg.list

RUN apt-get update && apt-get install -y --no-install-recommends \
    postgis postgresql-12-postgis-3 && \
    apt-get clean

RUN locale-gen en_US.UTF-8

RUN git clone https://github.com/strukturag/libheif.git libheif \
    && cd libheif \
    && ./autogen.sh \
    && ./configure \
    && make -j4 \
    && make install \
    && ldconfig

RUN python3 -m pip install --upgrade pip

RUN gdal-config --version
RUN python3 -m pip download GDAL==2.2.3
RUN tar -xpzf GDAL-2.2.3.tar.gz
CMD GDAL-2.2.3/ \
    && python3 setup.py build_ext --include-dirs=/usr/include/gdal/ \
    && python3 setup.py build \
    && python3 setup.py install

COPY ./requirements.txt /project/src/
WORKDIR /project/src/

RUN python3 -m pip install -r requirements.txt