const { getDb } = require('../config/database');

async function create({ enrollmentId, amount, status }) {
  const result = await getDb().run(
    'INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)',
    [enrollmentId, amount, status]
  );
  return { id: result.lastID, enrollmentId, amount, status };
}

module.exports = { create };
