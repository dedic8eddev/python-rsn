#!/bin/bash

set -e

USERNAME="raisin"
DBNAME="raisin"

createuser --username "${POSTGRES_USER}" -d ${USERNAME} && \
createdb --username "${POSTGRES_USER}" -O ${USERNAME} ${DBNAME}
