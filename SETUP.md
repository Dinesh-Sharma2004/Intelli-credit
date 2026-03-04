# Intelli-Credit Installation & Setup Guide

## System Requirements

- **OS**: Windows 10+, macOS 10.15+, or Ubuntu 20.04+
- **CPU**: 4 cores minimum (8 cores recommended)
- **RAM**: 8GB minimum (16GB recommended)
- **Disk**: 10GB free space
- **Docker**: Latest version
- **Node.js**: 18.0.0 or higher
- **Python**: 3.11 or higher

## Installation Steps

### Step 1: Clone Repository
```bash
git clone https://github.com/yourusername/intelli-credit.git
cd intelli-credit
```

### Step 2: Install Docker
Download and install Docker Desktop from https://www.docker.com/products/docker-desktop

### Step 3: Build and Start Services

#### Using Docker Compose (Easiest)
```bash
# Build all services
docker-compose build

# Start all services
docker-compose up -d

# Verify services are running
docker-compose ps
```

#### Manual Setup (Local Development)

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

### Step 4: Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Vector Database**: http://localhost:8001

## Troubleshooting

### Port Already in Use
```bash
# Windows
netstat -ano | findstr "3000"
taskkill /PID <PID> /F

# macOS/Linux
lsof -ti:3000 | xargs kill -9
```

### Docker Issues
```bash
# Clear Docker cache
docker system prune -a

# Rebuild images
docker-compose build --no-cache
```

### Missing Dependencies
```bash
# Backend
pip install --upgrade pip
pip install -r requirements.txt --force-reinstall

# Frontend
npm cache clean --force
npm install
```

## First Time Setup

1. **Create sample data**: The system includes demo data in `/backend/data/`
2. **Train ML model**: Pre-trained models are included
3. **Initialize vector DB**: ChromaDB automatically initializes on startup
4. **Test API**: Visit http://localhost:8000/docs for interactive API testing

## Demo Workflow

1. **Upload Document**: Go to `/documents` and upload a PDF
2. **View Extraction**: Check `/ingestor` for extracted data
3. **Research Company**: Use `/research` to look up company information
4. **Score Risk**: Navigate to `/risk-scoring` to see ML predictions
5. **Generate CAM**: Create a document on `/cam-generator`

## Next Steps

- Read the full README.md
- Explore API endpoints at `/docs`
- Review sample data in `/backend/data/`
- Check out component examples in `/frontend/src/components/`
