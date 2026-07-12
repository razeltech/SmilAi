import fs from 'fs';
const data = JSON.parse(fs.readFileSync('smilai_db.json', 'utf-8'));

for (const [tableName, rows] of Object.entries(data)) {
    if (rows.length === 0) continue;
    const cols = Object.keys(rows[0]);
    console.log(`CREATE TABLE IF NOT EXISTS ${tableName} (`);
    const colDefs = cols.map(c => `  ${c} TEXT`).join(',\n');
    console.log(colDefs);
    console.log(`);`);
}
