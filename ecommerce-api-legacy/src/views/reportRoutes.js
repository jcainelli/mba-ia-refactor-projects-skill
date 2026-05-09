const express = require('express');
const { getFinancialReport } = require('../controllers/reportController');

const router = express.Router();

router.get('/financial-report', async (req, res, next) => {
  try {
    const report = await getFinancialReport();
    res.status(200).json(report);
  } catch (err) {
    next(err);
  }
});

module.exports = router;
