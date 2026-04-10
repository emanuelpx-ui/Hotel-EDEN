import psycopg2
import psycopg2.extras
import os
from dotenv import load_dotenv

load_dotenv(encoding='utf-8')

def get_db_connection():
    database_url = os.getenv('DATABASE_URL')

    if database_url:
        conn = psycopg2.connect(database_url)
    else:
        conn = psycopg2.connect(
            host     = os.getenv('DB_HOST', 'localhost'),
            port     = int(os.getenv('DB_PORT', 5432)),
            dbname   = os.getenv('DB_NAME', 'BDhotel'),
            user     = os.getenv('DB_USER', 'postgres'),
            password = os.getenv('DB_PASSWORD', '')
        )

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
