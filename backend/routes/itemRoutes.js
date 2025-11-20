const express = require('express');
const {
  createItem,
  getItems,
  getItemById,
  getUserItems,
  updateItemStatus,
  deleteItem,
  searchItems,
  getSimilarItems,
} = require('../controllers/itemController');
const { protect } = require('../middleware/auth');

const router = express.Router();

router.post('/', protect, createItem);
router.get('/', getItems);
router.get('/my-items', protect, getUserItems);
router.post('/search', searchItems);
router.get('/:id/similar', getSimilarItems);
router.get('/:id', getItemById);
router.patch('/:id/status', protect, updateItemStatus);
router.delete('/:id', protect, deleteItem);

module.exports = router;