const { getDb } = require('../config/database');
const userModel = require('../models/userModel');
const courseModel = require('../models/courseModel');
const enrollmentModel = require('../models/enrollmentModel');
const paymentModel = require('../models/paymentModel');
const auditModel = require('../models/auditModel');
const { authorize } = require('../services/paymentService');
const { hashPassword } = require('../services/passwordService');
const {
  NotFoundError,
  PaymentDeniedError,
  ValidationError,
} = require('../middlewares/errorHandler');

async function checkout({ name, email, password, courseId, card }) {
  if (!name || !email || !courseId || !card) {
    throw new ValidationError('Bad Request');
  }
  if (typeof card !== 'string') {
    throw new ValidationError('Campo card deve ser string');
  }

  const course = await courseModel.findActiveById(courseId);
  if (!course) throw new NotFoundError('Curso não encontrado');

  const status = authorize(card);
  if (status === 'DENIED') throw new PaymentDeniedError();

  const db = getDb();
  await db.run('BEGIN');
  try {
    let user = await userModel.findByEmail(email);
    if (!user) {
      const passwordHash = await hashPassword(password || '123456');
      user = await userModel.create({ name, email, passwordHash });
    }

    const enrollment = await enrollmentModel.create({ userId: user.id, courseId });
    await paymentModel.create({
      enrollmentId: enrollment.id,
      amount: course.price,
      status,
    });
    await auditModel.log(`Checkout curso ${courseId} por ${user.id}`);

    await db.run('COMMIT');
    return { msg: 'Sucesso', enrollment_id: enrollment.id };
  } catch (err) {
    await db.run('ROLLBACK');
    throw err;
  }
}

module.exports = { checkout };
