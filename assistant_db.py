import sqlite3

from openai import OpenAI


class AssistantDatabase:
    def __init__(self, db_file="assistants.db"):
        self.db_file = db_file
        self.conn = sqlite3.connect(self.db_file)
        self.create_table()

    def create_table(self):
        """Create table if it doesn't exist"""
        query = """
        CREATE TABLE IF NOT EXISTS assistants (
            name TEXT PRIMARY KEY,
            assistant_id TEXT NOT NULL,
            thread_id TEXT NOT NULL
        )"""
        self.conn.execute(query)
        self.conn.commit()

    def get_assistant(self, name):
        """Retrieve assistant ID and thread ID from the database"""
        cursor = self.conn.cursor()
        query = """SELECT assistant_id, thread_id FROM assistants WHERE name = ?"""
        cursor.execute(query, (name,))  # Use parameterized query to prevent SQL injection
        return cursor.fetchone()

    def save_assistant(self, name, assistant_id, thread_id):
        """Insert or update an assistant's ID and thread ID"""
        query = """INSERT OR REPLACE INTO assistants (name, assistant_id, thread_id) 
                   VALUES (?, ?, ?)"""
        self.conn.execute(query, (name, assistant_id, thread_id))  # Use parameterized query
        self.conn.commit()

    def delete_assistant(self, assistant_id):
        query = "DELETE FROM assistants WHERE assistant_id = ?"
        self.conn.execute(query, (assistant_id,))
        self.conn.commit()

    def health_check(self):
        client = OpenAI()
        cursor = self.conn.cursor()
        query = "SELECT name, assistant_id FROM assistants"
        cursor.execute(query)
        all_assistants = cursor.fetchall()

        alive_assistants = client.beta.assistants.list().data
        alive_ids = {assistant.id for assistant in alive_assistants}

        for name, assistant_id in all_assistants:
            if assistant_id not in alive_ids:
                print(f"Removing missing assistant from DB: {name} {assistant_id}")
                self.delete_assistant(assistant_id)

        print("Health check completed")
