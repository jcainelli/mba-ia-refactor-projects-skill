const { getDb } = require('../config/database');

async function create({ userId, courseId }) {
  const result = await getDb().run(
    'INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)',
    [userId, courseId]
  );
  return { id: result.lastID, userId, courseId };
}

module.exports = { create };
