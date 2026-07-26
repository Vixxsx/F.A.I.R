import os
import mysql.connector
from typing import List, Dict, Optional
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

class DatabaseHelper:
    def __init__(self):
        self.config = {
            'host':     os.getenv('MYSQL_HOST', 'localhost'),
            'port':     int(os.getenv('MYSQL_PORT', 3306)),
            'user':     os.getenv('MYSQL_USER', 'root'),
            'password': os.getenv('MYSQL_PASSWORD', ''),
            'database': os.getenv('MYSQL_DATABASE', 'aira')
        }
        self._ensure_database()
        self.create_tables()

    def _ensure_database(self):
        try:
            config_without_db = {k: v for k, v in self.config.items() if k != 'database'}
            conn = mysql.connector.connect(**config_without_db)
            cursor = conn.cursor()
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self.config['database']}")
            conn.commit()
            cursor.close()
            conn.close()
            print(f"✅ Database '{self.config['database']}' ready")
        except Exception as e:
            print(f"❌ Database creation error: {e}")
            raise

    def get_connection(self):
        return mysql.connector.connect(**self.config)

    def create_tables(self):
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id         INT AUTO_INCREMENT PRIMARY KEY,
                    username   VARCHAR(100) NOT NULL UNIQUE,
                    email      VARCHAR(150) NOT NULL UNIQUE,
                    phone      VARCHAR(15),
                    dob        VARCHAR(20),
                    password   VARCHAR(255) NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_username (username),
                    INDEX idx_email (email)
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS interviews (
                    id                 INT AUTO_INCREMENT PRIMARY KEY,
                    interview_id       VARCHAR(100) NOT NULL,
                    user_id            INT,
                    username           VARCHAR(100) NOT NULL,
                    timestamp          VARCHAR(50),
                    job_role           VARCHAR(100),
                    grade              VARCHAR(5),
                    overall_score      INT,
                    questions_answered INT DEFAULT 0,
                    created_at         DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
                    INDEX idx_username (username),
                    INDEX idx_user_id (user_id),
                    INDEX idx_timestamp (timestamp)
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS question_history (
                    id            INT AUTO_INCREMENT PRIMARY KEY,
                    user_id       INT,
                    username      VARCHAR(100),
                    question_text TEXT NOT NULL,
                    category      VARCHAR(50),
                    job_role      VARCHAR(100),
                    asked_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
                    INDEX idx_username (username),
                    INDEX idx_user_id (user_id)
                )
            """)

            conn.commit()
            cursor.close()
            conn.close()
            print("✅ Tables created/verified")

        except Exception as e:
            print(f"❌ Table creation error: {e}")
            raise

    # ==================== USERS ====================

    def create_user(self, data: Dict) -> bool:
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO users (username, email, phone, dob, password)
                VALUES (%s, %s, %s, %s, %s)
            """, (data['username'], data['email'], data['phone'], data['dob'], data['password']))
            conn.commit()
            cursor.close()
            conn.close()
            print(f"✅ User created: {data['username']}")
            return True
        except mysql.connector.IntegrityError as e:
            print(f"❌ Duplicate user: {e}")
            return False
        except Exception as e:
            print(f"❌ Create user error: {e}")
            return False

    def get_user_by_username(self, username: str) -> Optional[Dict]:
        try:
            conn = self.get_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT * FROM users WHERE LOWER(username) = LOWER(%s)", (username,)
            )
            user = cursor.fetchone()
            cursor.close()
            conn.close()
            return user
        except Exception as e:
            print(f"❌ Get user error: {e}")
            return None

    def get_user_by_email(self, email: str) -> Optional[Dict]:
        try:
            conn = self.get_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT * FROM users WHERE LOWER(email) = LOWER(%s)", (email,)
            )
            user = cursor.fetchone()
            cursor.close()
            conn.close()
            return user
        except Exception as e:
            print(f"❌ Get user by email error: {e}")
            return None

    def get_all_users(self) -> List[Dict]:
        try:
            conn = self.get_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT id, username, email, phone, dob, created_at FROM users")
            users = cursor.fetchall()
            cursor.close()
            conn.close()
            return users
        except Exception as e:
            print(f"❌ Get all users error: {e}")
            return []

    # ==================== INTERVIEWS ====================

    def save_interview(self, data: Dict) -> bool:
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            user = self.get_user_by_username(data['username'])
            user_id = user['id'] if user else None

            cursor.execute("""
                INSERT INTO interviews
                (interview_id, user_id, username, timestamp, job_role, grade, overall_score, questions_answered)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                data['interview_id'],
                user_id,
                data['username'],
                data['timestamp'],
                data['job_role'],
                data['grade'],
                data['overall_score'],
                data.get('questions_answered', 0)
            ))
            conn.commit()
            cursor.close()
            conn.close()
            print(f"✅ Interview saved for {data['username']}")
            return True
        except Exception as e:
            print(f"❌ Save interview error: {e}")
            return False

    def get_recent_interviews(self, username: str, limit: int = 5) -> List[Dict]:
        try:
            conn = self.get_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT interview_id, username, timestamp, job_role, grade, overall_score, questions_answered
                FROM interviews
                WHERE LOWER(username) = LOWER(%s)
                ORDER BY timestamp DESC
                LIMIT %s
            """, (username, limit))
            results = cursor.fetchall()
            cursor.close()
            conn.close()
            return results
        except Exception as e:
            print(f"❌ Fetch interviews error: {e}")
            return []

    def get_user_stats(self, username: str) -> Dict:
        try:
            conn = self.get_connection()
            cursor = conn.cursor(dictionary=True)

            cursor.execute("""
                SELECT
                    COUNT(*)           AS total_interviews,
                    AVG(overall_score) AS average_score,
                    MAX(overall_score) AS best_score,
                    MIN(overall_score) AS worst_score
                FROM interviews
                WHERE LOWER(username) = LOWER(%s)
            """, (username,))
            stats = cursor.fetchone()

            cursor.execute("""
                SELECT grade, COUNT(*) AS count
                FROM interviews
                WHERE LOWER(username) = LOWER(%s)
                GROUP BY grade
            """, (username,))
            grade_dist = {row['grade']: row['count'] for row in cursor.fetchall()}

            cursor.close()
            conn.close()

            return {
                "total_interviews":   stats['total_interviews'] or 0,
                "average_score":      round(float(stats['average_score'] or 0), 1),
                "best_score":         stats['best_score'] or 0,
                "worst_score":        stats['worst_score'] or 0,
                "grade_distribution": grade_dist
            }
        except Exception as e:
            print(f"❌ Stats error: {e}")
            return {}

    def clear_user_interviews(self, username: str) -> bool:
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM interviews WHERE LOWER(username) = LOWER(%s)", (username,)
            )
            conn.commit()
            cursor.close()
            conn.close()
            return True
        except Exception as e:
            print(f"❌ Clear error: {e}")
            return False

    # ==================== QUESTION HISTORY ====================

    def save_questions(self, username: str, questions: List[str], category: str = None, job_role: str = None) -> bool:
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            user = self.get_user_by_username(username)
            user_id = user['id'] if user else None

            for question in questions:
                cursor.execute("""
                    INSERT INTO question_history (user_id, username, question_text, category, job_role)
                    VALUES (%s, %s, %s, %s, %s)
                """, (user_id, username, question, category, job_role))

            conn.commit()
            cursor.close()
            conn.close()
            return True
        except Exception as e:
            print(f"❌ Save questions error: {e}")
            return False

    def get_recent_questions(self, username: str, limit: int = 30) -> List[str]:
        try:
            conn = self.get_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT question_text FROM question_history
                WHERE LOWER(username) = LOWER(%s)
                ORDER BY asked_at DESC
                LIMIT %s
            """, (username, limit))
            results = cursor.fetchall()
            cursor.close()
            conn.close()
            return [r['question_text'] for r in results]
        except Exception as e:
            print(f"❌ Get questions error: {e}")
            return []


db = DatabaseHelper()