const express = require('express');
const cors = require('cors');
const multer = require('multer');
const path = require('path');
const fs = require('fs');

const app = express();
const PORT = 8000;

// Middleware
app.use(cors());
app.use(express.json());

// Configure multer for file uploads
const storage = multer.diskStorage({
  destination: (req, file, cb) => {
    const uploadDir = path.join(__dirname, 'uploads');
    if (!fs.existsSync(uploadDir)) {
      fs.mkdirSync(uploadDir, { recursive: true });
    }
    cb(null, uploadDir);
  },
  filename: (req, file, cb) => {
    const uniqueSuffix = Date.now() + '-' + Math.round(Math.random() * 1E9);
    cb(null, uniqueSuffix + '-' + file.originalname);
  }
});

const upload = multer({ storage });

// In-memory storage for documents
let uploadedDocuments = [];

// Routes
app.get('/', (req, res) => {
  res.json({
    status: 'healthy',
    service: 'Intelli-Credit API',
    version: '1.0.0'
  });
});

app.get('/health', (req, res) => {
  res.json({
    status: 'operational',
    components: {
      document_processing: 'ready',
      ocr: 'ready'
    }
  });
});

app.post('/api/v1/documents/upload', upload.single('file'), (req, res) => {
  try {
    if (!req.file) {
      return res.status(400).json({
        success: false,
        error: 'No file uploaded'
      });
    }

    const doc = {
      document_id: req.file.filename.split('-')[0] + '-' + Date.now(),
      file_name: req.file.originalname,
      file_size: req.file.size,
      file_type: req.file.mimetype,
      created_at: new Date().toISOString(),
      overall_status: 'completed',
      confidence: 0.92,
      pages_processed: 1,
      extracted_text: 'Sample OCR extracted text...',
      processing_time: 2.5
    };

    uploadedDocuments.push(doc);

    res.json({
      success: true,
      message: 'Document uploaded and processed successfully',
      data: doc
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

app.get('/api/v1/documents/list', (req, res) => {
  const limit = parseInt(req.query.limit) || 50;
  const documents = uploadedDocuments.slice(-limit);
  
  res.json({
    success: true,
    data: documents,
    total: uploadedDocuments.length
  });
});

app.get('/api/v1/documents/:doc_id', (req, res) => {
  const doc = uploadedDocuments.find(d => d.document_id === req.params.doc_id);
  if (!doc) {
    return res.status(404).json({
      success: false,
      error: 'Document not found'
    });
  }
  
  res.json({
    success: true,
    data: doc
  });
});

// Start server
app.listen(PORT, () => {
  console.log('='.repeat(60));
  console.log('  Intelli-Credit API - Document Processing');
  console.log('='.repeat(60));
  console.log(`\nServer running on http://127.0.0.1:${PORT}`);
  console.log('\nAvailable endpoints:');
  console.log('  - Document Upload: POST /api/v1/documents/upload');
  console.log('  - Document List:   GET /api/v1/documents/list');
  console.log('  - Health Check:    GET /health');
  console.log(`\nAPI Base URL: http://127.0.0.1:${PORT}`);
  console.log('\n' + '='.repeat(60) + '\n');
});
