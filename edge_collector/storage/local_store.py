import sqlite3
import time
import pickle


class LocalStore:
    def __init__(self, db_path="local_data.db"):
        self.conn = sqlite3.connect(db_path)
        self._setup()

    def _setup(self):
        cur = self.conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL,
                payload BLOB,
                sent INTEGER DEFAULT 0
            )
        """)
        self.conn.commit()

    def save(self, item: dict):
        """Salva payload decodificato, serializzato con pickle"""
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO data (timestamp, payload, sent) VALUES (?, ?, 0)",
            (time.time(), pickle.dumps(item)),
        )
        self.conn.commit()
        print(f"[STORE] saved: {item}")

    def load_all(self):
        """Restituisce tutti gli oggetti salvati (decodificati)"""
        cur = self.conn.cursor()
        cur.execute("SELECT payload FROM data")
        rows = cur.fetchall()
        # restituisce bytes, non dict
        return [row[0] for row in rows]

    def get_unsent(self, limit=10):
        """Restituisce gli oggetti non inviati (decodificati)"""
        cur = self.conn.cursor()
        cur.execute(
            "SELECT id, payload FROM data WHERE sent = 0 LIMIT ?",
            (limit,),
        )
        rows = cur.fetchall()
        return [(row[0], pickle.loads(row[1])) for row in rows]

    def mark_sent(self, row_id: int):
        cur = self.conn.cursor()
        cur.execute(
            "UPDATE data SET sent = 1 WHERE id = ?",
            (row_id,),
        )
        self.conn.commit()

    def clear(self):
        """Svuota tutto il database (per test)"""
        cur = self.conn.cursor()
        cur.execute("DELETE FROM data")
        self.conn.commit()
