#!/usr/bin/env python
"""
Script to check the schema of the contents table in the OnSide database.
"""

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import text

async def main():
    # Connect to the database
    engine = create_async_engine('postgresql+asyncpg://tobymorning@localhost:5432/onside')
    async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    
    # Query the schema
    async with async_session() as session:
        result = await session.execute(text(
            """
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'contents'
            ORDER BY ordinal_position
            """
        ))
        
        columns = [row[0] for row in result.fetchall()]
        
        print('Contents table columns:')
        for col in columns:
            print(f'- {col}')
    
    await engine.dispose()

# Run the script
if __name__ == "__main__":
    asyncio.run(main())
