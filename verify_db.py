#!/usr/bin/env python
"""Verify database setup and tables"""

from database import engine
from sqlalchemy import text

def verify_database():
    """Check database connection and tables"""
    try:
        with engine.connect() as conn:
            # Query tables
            result = conn.execute(text(
                "SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename"
            ))
            tables = [row[0] for row in result]
            
            print("\n✅ Database Connection: SUCCESS")
            print("\n📊 Tables Created:")
            for table in tables:
                print(f"   • {table}")
            
            print(f"\n✨ Total Tables: {len(tables)}")
            
            # Check table schemas
            print("\n📋 Table Schemas:")
            for table in tables:
                result = conn.execute(text(
                    f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = '{table}' ORDER BY ordinal_position"
                ))
                print(f"\n   {table}:")
                for col_name, col_type in result:
                    print(f"      - {col_name}: {col_type}")
            
    except Exception as e:
        print(f"\n❌ Database Error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    verify_database()
