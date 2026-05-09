const express = require('express');
const { checkout } = require('../controllers/checkoutController');

const router = express.Router();

router.post('/', async (req, res, next) => {
  try {
    const result = await checkout({
      name: req.body.usr,
      email: req.body.eml,
      password: req.body.pwd,
      courseId: req.body.c_id,
      card: req.body.card,
    });
    res.status(200).json(result);
  } catch (err) {
    next(err);
  }
});

module.exports = router;
