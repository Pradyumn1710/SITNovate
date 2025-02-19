const express = require('express');
const router = express.Router();
const chatController = require('../controllers/chatController');
const { isAuthenticated } = require('../middleware/auth');


router.post('/send', isAuthenticated, chatController.sendMessage);


module.exports = router;
