const crypto = require('crypto');
const { promisify } = require('util');

const scrypt = promisify(crypto.scrypt);
const SALT_BYTES = 16;
const KEY_LEN = 64;

async function hashPassword(plain) {
  const salt = crypto.randomBytes(SALT_BYTES).toString('hex');
  const derived = await scrypt(plain, salt, KEY_LEN);
  return `${salt}:${derived.toString('hex')}`;
}

async function verifyPassword(plain, stored) {
  if (!stored || !stored.includes(':')) return false;
  const [salt, hex] = stored.split(':');
  const derived = await scrypt(plain, salt, KEY_LEN);
  const expected = Buffer.from(hex, 'hex');
  if (expected.length !== derived.length) return false;
  return crypto.timingSafeEqual(expected, derived);
}

module.exports = { hashPassword, verifyPassword };
