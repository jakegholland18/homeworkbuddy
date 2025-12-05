#!/bin/bash
# Render build script for CozmicLearning

# Update package lists
apt-get update

# Install Tesseract OCR for image text extraction
apt-get install -y tesseract-ocr

# Install Python dependencies
pip install -r requirements.txt

# Note: Database migrations now run automatically during app startup in app.py
