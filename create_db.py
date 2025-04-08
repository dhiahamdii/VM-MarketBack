import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import os
from dotenv import load_dotenv

load_dotenv()

def create_database():
    # Connect to PostgreSQL server
    conn = psycopg2.connect(
        dbname='postgres',
        user='postgres',
        password='postgres',  # Change this to your PostgreSQL password
        host='localhost',
        port='5432'
    )
    
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()
    
    try:
        # Check if database exists
        cur.execute("SELECT 1 FROM pg_database WHERE datname = 'vm_marketplace'")
        exists = cur.fetchone()
        
        if not exists:
            # Create database
            cur.execute('CREATE DATABASE vm_marketplace')
            print("✅ Database 'vm_marketplace' created successfully!")
        else:
            print("ℹ️ Database 'vm_marketplace' already exists.")
            
    except Exception as e:
        print(f"❌ Error creating database: {str(e)}")
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    create_database() 