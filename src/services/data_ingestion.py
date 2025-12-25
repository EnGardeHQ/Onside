from fastapi import HTTPException
from sqlalchemy.orm import Session
import pandas as pd
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from src.models.content import Content
import aiohttp
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

logger = logging.getLogger(__name__)

class DataIngestionService:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    async def ingest_csv_data(
        self,
        file_path: str,
        user_id: str,
        db: AsyncSession,
        batch_size: int = 100
    ) -> List[Content]:
        """Ingest data from a CSV file"""
        try:
            df = pd.read_csv(file_path)
            contents = []
            
            # Process in batches
            for i in range(0, len(df), batch_size):
                batch = df.iloc[i:i + batch_size]
                for _, row in batch.iterrows():
                    content_data = self.transform_data(row.to_dict(), user_id)
                    if self.validate_data(content_data):
                        content = Content(**content_data)
                        db.add(content)
                        contents.append(content)
                
                await db.commit()
            
            return contents
            
        except Exception as e:
            logger.error(f"Error ingesting CSV data: {str(e)}")
            await db.rollback()
            raise HTTPException(status_code=500, detail=f"Error ingesting CSV data: {str(e)}")

    async def ingest_json_data(
        self,
        file_path: str,
        user_id: str,
        db: AsyncSession
    ) -> List[Content]:
        """Ingest data from a JSON file"""
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            contents = []
            for item in data:
                content_data = self.transform_data(item, user_id)
                if self.validate_data(content_data):
                    content = Content(**content_data)
                    db.add(content)
                    contents.append(content)
            
            await db.commit()
            return contents
            
        except Exception as e:
            logger.error(f"Error ingesting JSON data: {str(e)}")
            await db.rollback()
            raise HTTPException(status_code=500, detail=f"Error ingesting JSON data: {str(e)}")

    async def ingest_api_data(
        self,
        api_url: str,
        user_id: str,
        db: AsyncSession
    ) -> List[Content]:
        """Ingest data from an external API"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(api_url) as response:
                    data = await response.json()
            
            contents = []
            for item in data:
                content_data = self.transform_data(item, user_id)
                if self.validate_data(content_data):
                    content = Content(**content_data)
                    db.add(content)
                    contents.append(content)
            
            await db.commit()
            return contents
            
        except Exception as e:
            logger.error(f"Error ingesting API data: {str(e)}")
            await db.rollback()
            raise HTTPException(status_code=500, detail=f"Error ingesting API data: {str(e)}")

    def ingest_csv_data_sync(
        self,
        file_path: str,
        user_id: str,
        db: Session
    ) -> Dict[str, Any]:
        """Ingest data from a CSV file"""
        try:
            # Read CSV file
            df = pd.read_csv(file_path)
            
            # Process each record
            records_processed = 0
            for _, row in df.iterrows():
                content = Content(
                    title=row.get('title', ''),
                    content=row.get('content', ''),
                    content_type=row.get('type', 'text'),
                    published_date=row.get('published_date'),
                    user_id=user_id
                )
                db.add(content)
                records_processed += 1
            
            return {
                "status": "success",
                "records_processed": records_processed
            }
        except Exception as e:
            self.logger.error(f"Error ingesting CSV data: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error ingesting CSV data: {str(e)}"
            )

    def ingest_json_data_sync(
        self,
        file_path: str,
        user_id: str,
        db: Session
    ) -> Dict[str, Any]:
        """Ingest data from a JSON file"""
        try:
            # Read JSON file
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            if not isinstance(data, list):
                data = [data]
            
            return self.process_data(data, user_id, db)
        except Exception as e:
            self.logger.error(f"Error ingesting JSON data: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error ingesting JSON data: {str(e)}"
            )

    def process_data(
        self,
        data: List[Dict[str, Any]],
        user_id: str,
        db: Session
    ) -> Dict[str, Any]:
        """Process a list of content records"""
        try:
            records_processed = 0
            for item in data:
                content = Content(
                    title=item.get('title', ''),
                    content=item.get('content', ''),
                    content_type=item.get('type', 'text'),
                    published_date=item.get('published_date'),
                    user_id=user_id
                )
                db.add(content)
                records_processed += 1
            
            return {
                "status": "success",
                "records_processed": records_processed
            }
        except Exception as e:
            self.logger.error(f"Error processing data: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error processing data: {str(e)}"
            )

    def validate_data(self, data: Dict[str, Any]) -> bool:
        """Validate the data before ingestion"""
        required_fields = ['title', 'content_text']
        
        # Check required fields
        for field in required_fields:
            if field not in data or not data[field]:
                return False
        
        # Validate content length
        if len(data['content_text']) < 10:  # Minimum content length
            return False
        
        return True

    def transform_data(self, data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Transform input data to match Content model"""
        transformed = {
            'user_id': user_id,
            'title': data.get('title', ''),
            'content_text': data.get('content', ''),  # Map 'content' to 'content_text'
            'content_metadata': {}
        }
        
        # Add metadata
        if 'type' in data:
            transformed['content_metadata']['type'] = data['type']
        if 'published_date' in data:
            transformed['content_metadata']['published_date'] = data['published_date']
        
        # Add timestamps
        transformed['created_at'] = datetime.utcnow()
        transformed['updated_at'] = datetime.utcnow()
        
        return transformed

    async def handle_duplicates(
        self,
        content: Content,
        db: AsyncSession,
        strategy: str = 'skip'
    ) -> Optional[Content]:
        """Handle duplicate content based on strategy"""
        stmt = select(Content).where(
            Content.user_id == content.user_id,
            Content.title == content.title
        )
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()
        
        if existing:
            if strategy == 'skip':
                return None
            elif strategy == 'update':
                existing.content_text = content.content_text
                existing.content_metadata = content.content_metadata
                existing.updated_at = datetime.utcnow()
                return existing
            elif strategy == 'version':
                # Create new version
                content.title = f"{content.title} (v{datetime.utcnow().timestamp()})"
                return content
        
        return content
