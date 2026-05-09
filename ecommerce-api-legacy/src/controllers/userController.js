const userModel = require('../models/userModel');
const { ValidationError } = require('../middlewares/errorHandler');

async function deleteUser(id) {
  const userId = parseInt(id, 10);
  if (!Number.isInteger(userId) || userId <= 0) {
    throw new ValidationError('id inválido');
  }
  await userModel.deleteById(userId);
}

module.exports = { deleteUser };
