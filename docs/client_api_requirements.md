# API Requirements for OnSide Integration Testing

**Date:** May 10, 2025  
**To:** OnSide Client Team  
**From:** NorthBound Dev Team
**Subject:** API Key Requirements for Final Integration Testing  

Dear OnSide Team,

As we approach the final stages of the OnSide platform development, I'm writing to request API credentials needed for our integration testing phase. We've successfully integrated the core LLM functionality using OpenAI and Anthropic APIs, and now need to complete testing for the competitive intelligence components.

## API Requirements

We require access to **either** of these two options:

### Option 1: Premium Enterprise APIs (Preferred)
* **Meltwater API**: For media monitoring and competitor mentions tracking
* **SEMrush API**: For SEO analytics and competitor keyword intelligence

These enterprise APIs provide the most comprehensive data and will maximize the platform's competitive intelligence capabilities. However, both require setting up paid accounts upfront:

1. **Meltwater**: Requires a business subscription, typically starting at $5,000+ per year
2. **SEMrush**: Business subscription with API access starts at approximately $450 per month

### Option 2: Google API Alternatives (Cost-Effective Alternative)
If Meltwater and SEMrush are outside the current budget, we can implement the following Google APIs as alternatives:

* **Google Custom Search JSON API**: For news monitoring (replacing Meltwater)
* **Google Search Console API**: For SEO analytics (replacing SEMrush)
* **YouTube Data API**: For video content monitoring
* **Google PageSpeed Insights API**: For website performance analysis

These Google alternatives would require:
1. A Google Cloud Platform account
2. Setting up a project and enabling these specific APIs
3. Creating API credentials
4. (For Search Console) Verification of website ownership

## Additional API Integrations

In addition to the APIs mentioned above, we're implementing these specialized APIs to enhance the platform's capabilities:

1. **GNews API**: Provides targeted news aggregation focused specifically on business and industry news, with better filtering options than general news APIs.

2. **IP Info API**: Enables geographic analysis of website visitors and competitor audience distributions, providing insights into regional market penetration opportunities.

3. **SERP API**: Offers detailed search engine results page analysis, including featured snippets, knowledge panels, and local pack data that isn't available through Google's official APIs.

4. **WhoAPI**: Provides comprehensive domain intelligence, including technology stack identification, helping identify which technologies competitors are adopting.

For these additional APIs, we've already registered for developer tiers which are sufficient for integration testing. However, for production deployment, you may want to consider upgraded plans based on usage volume.

## Important Notes

* This API integration work falls within our existing Statement of Work and does not change the project scope or timeline.
* We only need these API keys for the final stage of integration testing.
* All API keys will be securely stored in environment variables, never in source code.
* We can assist with the API registration process if needed.

## Next Steps

To proceed with integration testing, we kindly request either:

1. Meltwater and SEMrush API credentials if you already have subscriptions or wish to proceed with these premium options, OR
2. Permission to set up the Google API alternatives using a Google account that you designate.

Please let us know your preference by May 15th so we can finalize the integration work according to schedule.

Thank you for your assistance. We're excited to be nearing completion of this phase and look forward to demonstrating the enhanced competitive intelligence capabilities of the OnSide platform.

Best regards,

NorthBound Development Team

---

**Contact Information:**  
Email: toby@rely.ventures
Phone: (831) 295-0562
