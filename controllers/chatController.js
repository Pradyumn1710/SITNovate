const axios = require("axios");
const ChatMessage = require("../models/Chat");

exports.sendMessage = async (req, res) => {
  const { message } = req.body;

  try {
    
    const userMessage = new ChatMessage({
      userId: req.user._id,
      message,
      senderType: "user",
    });
    await userMessage.save();

   
    const aiResponse = await axios.post("http://127.0.0.1:5000/ask", { question: message });

   
    const agentResponse = new ChatMessage({
      userId: req.user._id,
      message: aiResponse.data.answer, 
      senderType: "agent",
    });
    await agentResponse.save();

    res.json({ userMessage, agentResponse });
  } catch (error) {
    res.status(500).json({ message: "Error processing message", error: error.message });
  }
};
