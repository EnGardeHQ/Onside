#!/usr/bin/env python3
import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def check_tables():
    database_url = os.getenv('DATABASE_URL', 'postgresql+asyncpg://postgres:onside-password@localhost:5432/onside')
    print(f"Connecting to: {database_url}")
    
    engine = create_async_engine(database_url)
    
    async with engine.connect() as conn:
        print("Connected to database successfully")
        
        # List all tables
        result = await conn.execute(text("SELECT tablename FROM pg_tables WHERE schemaname = 'public'"))
        print('Tables in database:')
        for row in result:
            print(f"- {row[0]}")
        
        # Check companies table structure
        try:
            result = await conn.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'companies'"))
            print('\nCompanies table columns:')
            for row in result:
                print(f"- {row[0]} ({row[1]})")
        except Exception as e:
            print(f"Error checking companies table: {e}")
        
        # Check competitors table structure
        try:
            result = await conn.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'competitors'"))
            print('\nCompetitors table columns:')
            for row in result:
                print(f"- {row[0]} ({row[1]})")
        except Exception as e:
            print(f"Error checking competitors table: {e}")

if __name__ == "__main__":
    asyncio.run(check_tables())
