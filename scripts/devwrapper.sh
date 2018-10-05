#!/usr/bin/env bash

pip install -q --upgrade pip
make install-dev
flask db upgrade

exec "$@"