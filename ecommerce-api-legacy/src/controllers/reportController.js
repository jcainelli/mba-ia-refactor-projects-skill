const reportModel = require('../models/reportModel');

function buildFinancialReport(rows) {
  const byCourseId = new Map();
  for (const row of rows) {
    let entry = byCourseId.get(row.course_id);
    if (!entry) {
      entry = { course: row.course_title, revenue: 0, students: [] };
      byCourseId.set(row.course_id, entry);
    }
    if (row.enrollment_id == null) continue;
    if (row.payment_status === 'PAID') {
      entry.revenue += row.payment_amount || 0;
    }
    entry.students.push({
      student: row.user_name || 'Unknown',
      paid: row.payment_amount || 0,
    });
  }
  return Array.from(byCourseId.values());
}

async function getFinancialReport() {
  const rows = await reportModel.fetchFinancialReport();
  return buildFinancialReport(rows);
}

module.exports = { getFinancialReport };
