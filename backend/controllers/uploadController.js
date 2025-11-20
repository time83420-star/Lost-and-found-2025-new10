const { uploadToCloudinary } = require('../services/storageService');
const { generateImageCaption } = require('../services/mlService');

const uploadImage = async (req, res) => {
  try {
    if (!req.file) {
      return res.status(400).json({ message: 'No file uploaded' });
    }

    const imageUrl = await uploadToCloudinary(req.file.buffer);

    // Generate AI caption in the background (non-blocking)
    let aiCaption = null;
    try {
      aiCaption = await generateImageCaption(req.file.buffer);
    } catch (mlError) {
      console.error('AI caption generation failed:', mlError);
      // Continue without AI caption
    }

    res.json({
      url: imageUrl,
      aiCaption: aiCaption
    });
  } catch (error) {
    res.status(500).json({ message: error.message });
  }
};

module.exports = { uploadImage };
