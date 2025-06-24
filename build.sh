#!/bin/bash

# Install Python dependencies
pip install -r backend/requirements.txt

# Download the spaCy model
python -m spacy download en_core_web_sm
