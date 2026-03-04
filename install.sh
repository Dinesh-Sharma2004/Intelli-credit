#!/bin/bash

# Intelli-Credit Installation Script for macOS/Linux

echo "========================================"
echo "Intelli-Credit Installation Script"
echo "========================================"

# Check prerequisites
echo "Checking prerequisites..."

if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker Desktop."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed."
    exit 1
fi

if ! command -v node &> /dev/null; then
    echo "⚠️  Node.js not found. Frontend development may not work."
fi

echo "✓ All prerequisites found"

# Create environment file
echo ""
echo "Setting up environment..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "✓ Created .env file"
fi

# Build and start services
echo ""
echo "Building and starting services..."
docker-compose build
docker-compose up -d

echo ""
echo "Waiting for services to start..."
sleep 10

# Check service health
echo ""
echo "Checking service status..."
docker-compose ps

echo ""
echo "========================================"
echo "✓ Installation completed!"
echo "========================================"
echo ""
echo "Access the application:"
echo "  Frontend:       http://localhost:3000"
echo "  Backend API:    http://localhost:8000"
echo "  API Docs:       http://localhost:8000/docs"
echo "  Vector DB:      http://localhost:8001"
echo ""
