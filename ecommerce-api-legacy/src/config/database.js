const sqlite3 = require('sqlite3').verbose();
const { promisify } = require('util');
const { hashPassword } = require('../services/passwordService');

let db = null;

function wrap(rawDb) {
  return {
    raw: rawDb,
    get: promisify(rawDb.get.bind(rawDb)),
    all: promisify(rawDb.all.bind(rawDb)),
    run(sql, params = []) {
      return new Promise((resolve, reject) =>
        rawDb.run(sql, params, function (err) {
          if (err) return reject(err);
          resolve({ lastID: this.lastID, changes: this.changes });
        })
      );
    },
    exec(sql) {
      return new Promise((resolve, reject) =>
        rawDb.exec(sql, (err) => (err ? reject(err) : resolve()))
      );
    },
  };
}

async function initDb() {
  const raw = new sqlite3.Database(':memory:');
  db = wrap(raw);

  await db.exec('PRAGMA foreign_keys = ON');

  await db.exec(`
    CREATE TABLE users (
      id INTEGER PRIMARY KEY,
      name TEXT NOT NULL,
      email TEXT NOT NULL UNIQUE,
      password_hash TEXT NOT NULL
    );
    CREATE TABLE courses (
      id INTEGER PRIMARY KEY,
      title TEXT NOT NULL,
      price REAL NOT NULL,
      active INTEGER NOT NULL
    );
    CREATE TABLE enrollments (
      id INTEGER PRIMARY KEY,
      user_id INTEGER NOT NULL,
      course_id INTEGER NOT NULL,
      FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
      FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE
    );
    CREATE TABLE payments (
      id INTEGER PRIMARY KEY,
      enrollment_id INTEGER NOT NULL,
      amount REAL NOT NULL,
      status TEXT NOT NULL,
      FOREIGN KEY (enrollment_id) REFERENCES enrollments(id) ON DELETE CASCADE
    );
    CREATE TABLE audit_logs (
      id INTEGER PRIMARY KEY,
      action TEXT NOT NULL,
      created_at DATETIME NOT NULL
    );
  `);

  const adminHash = await hashPassword('123');
  await db.run('INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)',
    ['Leonan', 'leonan@fullcycle.com.br', adminHash]);
  await db.run('INSERT INTO courses (title, price, active) VALUES (?, ?, 1)', ['Clean Architecture', 997.00]);
  await db.run('INSERT INTO courses (title, price, active) VALUES (?, ?, 1)', ['Docker', 497.00]);
  await db.run('INSERT INTO enrollments (user_id, course_id) VALUES (1, 1)');
  await db.run('INSERT INTO payments (enrollment_id, amount, status) VALUES (1, 997.00, ?)', ['PAID']);
}

function getDb() {
  if (!db) throw new Error('Database not initialized — call initDb() first');
  return db;
}

module.exports = { initDb, getDb };
