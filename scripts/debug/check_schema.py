#!/usr/bin/env python
"""
Database Schema Inspection Tool
"""
import asyncio
import asyncpg

async def check_schema():
    """Check the schema of the competitor_metrics table"""
    try:
        # Connect to the database using the verified PostgreSQL configuration
        conn = await asyncpg.connect(
            user='tobymorning',
            database='onside',
            host='localhost'
        )
        
        # Get column names for competitor_metrics table
        query = """
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'competitor_metrics'
        """
        result = await conn.fetch(query)
        
        print('Columns in competitor_metrics table:')
        if result:
            for row in result:
                print(f'- {row["column_name"]}')
        else:
            print("No columns found. Table might not exist.")
        
        await conn.close()
    
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(check_schema())
