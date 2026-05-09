const { getDb } = require('../config/database');

async function findByEmail(email) {
  return getDb().get('SELECT id, name, email FROM users WHERE email = ?', [email]);
}

async function create({ name, email, passwordHash }) {
  const result = await getDb().run(
    'INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)',
    [name, email, passwordHash]
  );
  return { id: result.lastID, name, email };
}

async function deleteById(id) {
  const result = await getDb().run('DELETE FROM users WHERE id = ?', [id]);
  return result.changes > 0;
}

module.exports = { findByEmail, create, deleteById };
