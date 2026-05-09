class AppError extends Error {
  constructor(message, statusCode = 500) {
    super(message);
    this.statusCode = statusCode;
  }
}

class NotFoundError extends AppError {
  constructor(message) { super(message, 404); }
}

class ValidationError extends AppError {
  constructor(message) { super(message, 400); }
}

class PaymentDeniedError extends AppError {
  constructor(message = 'Pagamento recusado') { super(message, 400); }
}

function errorHandler(err, req, res, _next) {
  const status = err.statusCode || 500;
  if (status >= 500) console.error(err);
  res.status(status).json({ error: err.message || 'Internal server error' });
}

module.exports = { AppError, NotFoundError, ValidationError, PaymentDeniedError, errorHandler };
