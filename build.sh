#!/bin/bash

# Update and install system-level build tools required by blis and spacy
apt-get update && apt-get install -y build-essential gcc python3-dev

# Upgrade pip
pip install --upgrade pip

# Install Python dependencies
pip install -r backend/requirements.txt

# Download the spaCy model
python -m spacy download en_core_web_sm


uvicorn main:app --host=0.0.0.0 --port=10000
