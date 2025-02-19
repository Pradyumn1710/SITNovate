const ChatMessage = require('../models/ChatMessage');

exports.sendMessage = async (req, res) => {
  const { message } = req.body;

  try {
    const userMessage = new ChatMessage({
      userId: req.user._id,
      message,
      senderType: 'user'
    });
    await userMessage.save();

    
    const agentResponse = new ChatMessage({
      userId: req.user._id,
      message: `Agent response to "${message}"`,
      senderType: 'agent'
    });
    await agentResponse.save();

    res.json({ userMessage, agentResponse });
  } catch (error) {
    res.status(500).json({ message: 'Error sending message', error });
  }
};
