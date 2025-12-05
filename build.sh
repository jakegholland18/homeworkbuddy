#!/bin/bash
# Render build script for CozmicLearning

# Update package lists
apt-get update

# Install Tesseract OCR for image text extraction
apt-get install -y tesseract-ocr

# Install Python dependencies
pip install -r requirements.txt

# Run database migrations
echo "Running database migrations..."
python migrations/add_password_reset_tokens.py
