function authorize(cardNumber) {
  if (typeof cardNumber !== 'string' || cardNumber.length < 1) return 'DENIED';
  return cardNumber.startsWith('4') ? 'PAID' : 'DENIED';
}

module.exports = { authorize };
