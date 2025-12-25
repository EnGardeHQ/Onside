#!/usr/bin/env python

with open('/Volumes/Cody/projects/OnSide/scripts/report_generators/enhanced_tcs_report_with_apis.py', 'r') as file:
    lines = file.readlines()

# Find the start of collect_api_data function
start_index = -1
end_index = -1
for i, line in enumerate(lines):
    if 'async def collect_api_data' in line:
        start_index = i
    elif start_index != -1 and 'async def process_api_data' in line:
        end_index = i
        break

if start_index == -1 or end_index == -1:
    print("Couldn't find the function boundaries")
    exit(1)

# Create a new properly structured function
new_function = """async def collect_api_data(company_name: str = "Tata Consultancy Services") -> Dict[str, Any]:
    \"\"\"
    Collect data from all API sources with proper database integration.
    
    Args:
        company_name: Name of the company to analyze (default: "Tata Consultancy Services")
        
    Returns:
        Dictionary with all API responses and analysis results
    \"\"\"
    # Initialize services
    news_service = NewsService()
    domain_service = DomainService()
    search_service = SearchService()
    location_service = LocationService()
    maps_service = MapsService()
    ai_service = AIService()
    seo_service = SEOService()
    content_service = ContentService()
    keyword_service = KeywordService()
    
    # Initialize data structure
    data = {
        "news_data": {},
        "domain_data": {},
        "search_data": {},
        "location_data": {},
        "maps_data": {},
        "seo_analysis": {},
        "content_analysis": {},
        "visualizations": {},
        "ai_analysis": {}
    }
    
    # Connect to database and get company information
    db_session = None
    report = None
    
    try:
        # Initialize database session
        db_session = AsyncSession(engine)
        
        # Check if a report already exists for this company
        report_query = select(Report).where(Report.company_name == company_name)
        report_result = await db_session.execute(report_query)
        report = report_result.scalar_one_or_none()
        
        # If no report exists, create a new one
        if not report:
            report = Report(
                id=uuid.uuid4(),
                company_name=company_name,
                status=ReportStatus.IN_PROGRESS.value.upper(),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db_session.add(report)
            await db_session.commit()
        else:
            # Update existing report status
            report.status = ReportStatus.IN_PROGRESS.value.upper()
            report.updated_at = datetime.utcnow()
            db_session.add(report)
            await db_session.commit()
            
        # Make API calls in parallel
        tasks = [
            news_service.get_company_news(company_name, days=30),
            news_service.get_industry_news("IT Services", days=30),
            search_service.get_search_insights(company_name),
            search_service.get_company_positioning(company_name, "IT Services"),
            location_service.get_company_locations([f"{company_name.lower().replace(' ', '')}.com"]),
            location_service.get_country_distribution([f"{company_name.lower().replace(' ', '')}.com"])
        ]
        
        # Execute all API calls in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        company_news, industry_news, search_insights, company_positioning, location_data, country_distribution = results
        
        # Add data to the structure
        if not isinstance(company_news, Exception):
            data["news_data"]["company"] = company_news
        
        if not isinstance(industry_news, Exception):
            data["news_data"]["industry"] = industry_news
        
        if not isinstance(search_insights, Exception):
            data["search_data"]["insights"] = search_insights
            
        if not isinstance(company_positioning, Exception):
            data["search_data"]["positioning"] = company_positioning
            
        if not isinstance(location_data, Exception):
            data["location_data"]["locations"] = location_data
            
        if not isinstance(country_distribution, Exception):
            data["location_data"]["distribution"] = country_distribution
        
        # Process results
        api_results = {
            "news": data["news_data"],
            "domain": data["domain_data"],
            "search": data["search_data"],
            "locations": data["location_data"],
            "maps": data["maps_data"],
            "seo_analysis": data["seo_analysis"],
            "content_analysis": data["content_analysis"],
            "visualizations": data["visualizations"],
            "ai_analysis": data["ai_analysis"],
            "metadata": {
                "company_name": company_name,
                "generated_at": datetime.utcnow().isoformat(),
                "report_id": str(report.id)
            }
        }
        
        # Update report status
        report.status = ReportStatus.COMPLETED.value.upper()  # Using the enum value in uppercase
        report.updated_at = datetime.utcnow()
        report.results = data
        db_session.add(report)
        await db_session.commit()
        
        # Return the results with API stats
        return {
            "success": True,
            "data": data,
            "api_stats": {
                "news_api_calls": getattr(news_service, 'api_calls', 0),
                "domain_api_calls": getattr(domain_service, 'api_calls', 0),
                "search_api_calls": getattr(search_service, 'api_calls', 0),
                "location_api_calls": getattr(location_service, 'api_calls', 0),
                "maps_api_calls": getattr(maps_service, 'api_calls', 0),
                "ai_api_calls": getattr(ai_service, 'api_calls', 0)
            }
        }
    except Exception as e:
        # Handle any errors and update report status
        if report:
            report.status = ReportStatus.FAILED.value.upper()
            report.error_message = str(e)
            report.updated_at = datetime.utcnow()
            if db_session:
                await db_session.commit()
        logger.error(f"Error collecting API data: {str(e)}")
        raise
    finally:
        # Ensure database session is properly closed
        if db_session:
            await db_session.close()
"""

# Replace the function in the file
lines[start_index:end_index] = [new_function]

with open('/Volumes/Cody/projects/OnSide/scripts/report_generators/enhanced_tcs_report_with_apis.py', 'w') as file:
    file.writelines(lines)

print("Function successfully replaced with a cleaner structure")
