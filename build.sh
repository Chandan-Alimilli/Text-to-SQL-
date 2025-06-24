#!/bin/bash

# Linux-specific: Install compilers and dev tools needed by spaCy dependencies
apt-get update && apt-get install -y build-essential gcc python3-dev

# Upgrade pip and install dependencies
pip install --upgrade pip
pip install -r backend/requirements.txt --prefer-binary

# Download spaCy language model
python -m spacy download en_core_web_sm
