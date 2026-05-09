const express = require('express');
const { deleteUser } = require('../controllers/userController');

const router = express.Router();

router.delete('/:id', async (req, res, next) => {
  try {
    await deleteUser(req.params.id);
    res.status(200).send('Usuário deletado');
  } catch (err) {
    next(err);
  }
});

module.exports = router;
