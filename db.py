import asyncpg
import os

_pool = None

async def get_pool():
    global _pool
    if _pool is None:
        DATABASE_URL = os.getenv("DATABASE_URL")
        _pool = await asyncpg.create_pool(DATABASE_URL, ssl="require")
    return _pool

async def init_db():
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id BIGINT PRIMARY KEY,
                full_name TEXT,
                username TEXT,
                joined_at TIMESTAMP DEFAULT NOW()
            );

            CREATE TABLE IF NOT EXISTS tests (
                id SERIAL PRIMARY KEY,
                test_code TEXT UNIQUE NOT NULL,
                answers TEXT NOT NULL,
                subject TEXT DEFAULT 'Matematika',
                total_questions INT NOT NULL,
                created_by BIGINT NOT NULL,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT NOW(),
                ended_at TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS submissions (
                id SERIAL PRIMARY KEY,
                test_code TEXT NOT NULL,
                user_id BIGINT NOT NULL,
                user_answers TEXT NOT NULL,
                score INT DEFAULT 0,
                total INT DEFAULT 0,
                percentage FLOAT DEFAULT 0,
                submitted_at TIMESTAMP DEFAULT NOW(),
                UNIQUE(test_code, user_id)
            );
        """)
    print("✅ Database initialized")

async def register_user(user_id, full_name, username):
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO users (user_id, full_name, username)
            VALUES ($1, $2, $3)
            ON CONFLICT (user_id) DO UPDATE SET full_name=$2, username=$3
        """, user_id, full_name, username)

async def create_test(test_code, answers, total_questions, created_by, subject="Matematika"):
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO tests (test_code, answers, total_questions, created_by, subject)
            VALUES ($1, $2, $3, $4, $5)
            ON CONFLICT (test_code) DO UPDATE
            SET answers=$2, total_questions=$3, is_active=TRUE, ended_at=NULL
        """, test_code, answers, total_questions, created_by, subject)

async def get_test(test_code):
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetchrow(
            "SELECT * FROM tests WHERE test_code=$1 AND is_active=TRUE", test_code
        )

async def get_all_active_tests(admin_id):
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetch(
            "SELECT * FROM tests WHERE created_by=$1 AND is_active=TRUE ORDER BY created_at DESC",
            admin_id
        )

async def submit_answers(test_code, user_id, user_answers, score, total, percentage):
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO submissions (test_code, user_id, user_answers, score, total, percentage)
            VALUES ($1, $2, $3, $4, $5, $6)
            ON CONFLICT (test_code, user_id) DO UPDATE
            SET user_answers=$3, score=$4, total=$5, percentage=$6, submitted_at=NOW()
        """, test_code, user_id, user_answers, score, total, percentage)

async def end_test(test_code):
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            UPDATE tests SET is_active=FALSE, ended_at=NOW()
            WHERE test_code=$1
        """, test_code)

async def get_test_results(test_code):
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetch("""
            SELECT s.*, u.full_name, u.username
            FROM submissions s
            LEFT JOIN users u ON s.user_id = u.user_id
            WHERE s.test_code=$1
            ORDER BY s.score DESC
        """, test_code)

async def check_already_submitted(test_code, user_id):
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT id FROM submissions WHERE test_code=$1 AND user_id=$2",
            test_code, user_id
        )
        return row is not None

async def get_test_any(test_code):
    """Faol yoki faol bo'lmagan testni ham topadi"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetchrow(
            "SELECT * FROM tests WHERE test_code=$1", test_code
        )
