const mongoose = require('mongoose');

const DocumentSchema = new mongoose.Schema({
  filename: { type: String, required: true },
  originalName: { type: String, required: true },
  path: { type: String, required: true },
  uploadedBy: { type: mongoose.Schema.Types.ObjectId, ref: 'User' },
  uploadedAt: { type: Date, default: Date.now }
});

module.exports = mongoose.model('Document', DocumentSchema);
