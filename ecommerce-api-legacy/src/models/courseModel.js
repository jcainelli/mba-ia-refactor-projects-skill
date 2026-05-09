const { getDb } = require('../config/database');

async function findActiveById(id) {
  return getDb().get('SELECT id, title, price FROM courses WHERE id = ? AND active = 1', [id]);
}

module.exports = { findActiveById };
