import psycopg2
import psycopg2.extras
import os
from dotenv import load_dotenv

load_dotenv(encoding='utf-8')

DB_CONFIG = {
    'host':     os.getenv('DB_HOST', 'localhost'),
    'port':     int(os.getenv('DB_PORT', 5432)),
    'dbname':   os.getenv('DB_NAME', 'BDhotel'),
    'user':     os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', '')
}

def get_db_connection():
    conn = psycopg2.connect(os.getenv('DATABASE_URL'), **DB_CONFIG)
    conn.autocommit = False
    return conn

def query_db(sql, params=None, fetchone=False):
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, params or ())
            return cur.fetchone() if fetchone else cur.fetchall()
    finally:
        conn.close()

def execute_db(sql, params=None):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params or ())
            result = None
            if cur.description:
                result = cur.fetchone()[0]
            conn.commit()
            return result
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()