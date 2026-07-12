import fs from 'fs';
import Database from 'better-sqlite3';

const data = JSON.parse(fs.readFileSync('smilai_db.json', 'utf-8'));
const db = new Database('smilai.db');

for (const [tableName, rows] of Object.entries(data)) {
    if (rows.length === 0) continue;
    const cols = Object.keys(rows[0]);
    let createSql = `CREATE TABLE IF NOT EXISTS ${tableName} (\n`;
    createSql += cols.map(c => `  ${c} TEXT`).join(',\n');
    createSql += `\n);`;
    db.exec(createSql);

    const insertSql = `INSERT INTO ${tableName} (${cols.join(', ')}) VALUES (${cols.map(() => '?').join(', ')})`;
    const stmt = db.prepare(insertSql);
    for (const row of rows) {
        const values = cols.map(c => row[c] === undefined ? null : String(row[c]));
        stmt.run(...values);
    }
}
console.log("Migration complete.");
