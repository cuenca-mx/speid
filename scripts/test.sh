#!/usr/bin/env bash

make clean-pyc
pip install -q --upgrade pip
make install-dev

make test