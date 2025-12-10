#!/bin/bash
# Build script for Selfmade Labs Docker images
# This script builds all lab images with ttyd web terminals

set -e  # Exit on error

echo "========================================"
echo "Building Selfmade Labs Docker Images"
echo "========================================"
echo ""

# Build Ubuntu SSH Lab
echo "[1/2] Building Ubuntu SSH Lab..."
cd labs/ubuntu-ssh
docker build -t selfmade/ubuntu-ssh:latest .
cd ../..
echo "✓ Ubuntu SSH Lab built successfully"
echo ""

# Build Kali Linux Lab
echo "[2/2] Building Kali Linux Lab..."
cd labs/kali-linux
docker build -t selfmade/kali-linux:latest .
cd ../..
echo "✓ Kali Linux Lab built successfully"
echo ""

echo "========================================"
echo "All lab images built successfully!"
echo "========================================"
echo ""
echo "Available images:"
docker images | grep selfmade
echo ""
echo "To start the platform, run:"
echo "  uvicorn app.main:app --reload --port 8000"
echo ""
