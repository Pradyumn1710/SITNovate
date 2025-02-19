const express = require('express');
const router = express.Router();
const documentController = require('../controllers/documentController');
const { isAuthenticated } = require('../middleware/auth');

router.post('/upload', isAuthenticated, documentController.uploadPDF, documentController.savePDF);

module.exports = router;
