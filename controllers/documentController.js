const multer = require('multer');
const path = require('path');
const fs = require('fs');
const Document = require('../models/Document');


const storage = multer.diskStorage({
  destination: (req, file, cb) => {
    cb(null, 'uploads/');
  },
  filename: (req, file, cb) => {
    cb(null, Date.now() + path.extname(file.originalname));
  }
});

const upload = multer({
  storage: storage,
  fileFilter: (req, file, cb) => {
    if (file.mimetype === 'application/pdf' && path.extname(file.originalname).toLowerCase() === '.pdf') {
      cb(null, true);
    } else {
      cb(new Error('Only PDF files are allowed'), false);
    }
  }
});

exports.uploadPDF = upload.single('pdf');

exports.savePDF = async (req, res) => {
  if (!req.file) {
    return res.status(400).json({ message: 'No PDF file uploaded' });
  }

  try {
    const newDocument = new Document({
      filename: req.file.filename,
      originalName: req.file.originalname,
      path: req.file.path,
      uploadedBy: req.user._id
    });

    await newDocument.save();
    res.status(201).json({ message: 'PDF uploaded successfully', documentId: newDocument._id });
  } catch (error) {
    res.status(500).json({ message: 'Error saving PDF', error: error.message });
  }
};

exports.getPDF = async (req, res) => {
  try {
    const document = await Document.findById(req.params.id);
    if (!document) {
      return res.status(404).json({ message: 'PDF not found' });
    }
    
    const filePath = path.join(__dirname, '..', document.path);
    fs.createReadStream(filePath).pipe(res);
  } catch (error) {
    res.status(500).json({ message: 'Error retrieving PDF', error: error.message });
  }
};

exports.generateSummary = async (req, res) => {
    const { documentId } = req.body;
  
    try {
      // Placeholder logic until AI integration is complete.
      // Retrieve the document content and send it to the AI summarizer.
      res.json({ message: 'Summary generation requested', summary: 'This is a placeholder summary.' });
    } catch (error) {
      res.status(500).json({ message: 'Error generating summary', error });
    }
  };
  