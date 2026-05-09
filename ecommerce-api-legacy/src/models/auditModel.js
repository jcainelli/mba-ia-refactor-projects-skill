const { getDb } = require('../config/database');

async function log(action) {
  await getDb().run(
    "INSERT INTO audit_logs (action, created_at) VALUES (?, datetime('now'))",
    [action]
  );
}

module.exports = { log };
