#!/usr/bin/env bash

make clean-pyc
pip install -q --upgrade pip
make install-dev
flask db upgrade

pytest -v -k "not get_post_request"