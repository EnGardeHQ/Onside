/**
 * Capilytics API - JavaScript SEO Services Examples
 */

const axios = require('axios');
const CapilyticsAuthClient = require('./authentication');

class SEOServicesClient {
  constructor(authClient) {
    this.authClient = authClient;
    this.baseUrl = authClient.baseUrl;
  }

  /**
   * Perform Google Custom Search
   */
  async googleSearch(query, options = {}) {
    try {
      const response = await axios.post(
        `${this.baseUrl}/seo/google-search`,
        {
          query,
          max_results: options.maxResults || 10,
          language: options.language || 'en',
          date_restrict: options.dateRestrict,
          site_search: options.siteSearch,
          exclude_site: options.excludeSite
        },
        { headers: this.authClient.getHeaders() }
      );
      return response.data;
    } catch (error) {
      throw this.authClient.handleError(error);
    }
  }

  /**
   * Track brand mentions
   */
  async trackBrandMentions(brandName, options = {}) {
    try {
      const response = await axios.post(
        `${this.baseUrl}/seo/brand-mentions`,
        {
          brand_name: brandName,
          keywords: options.keywords || [],
          competitors: options.competitors || [],
          date_restrict: options.dateRestrict || 'm1',
          max_results: options.maxResults || 50
        },
        { headers: this.authClient.getHeaders() }
      );
      return response.data;
    } catch (error) {
      throw this.authClient.handleError(error);
    }
  }

  /**
   * Analyze content performance
   */
  async analyzeContentPerformance(url, competitors = [], metrics = []) {
    try {
      const response = await axios.post(
        `${this.baseUrl}/seo/content-performance`,
        {
          url,
          competitors,
          metrics
        },
        { headers: this.authClient.getHeaders() }
      );
      return response.data;
    } catch (error) {
      throw this.authClient.handleError(error);
    }
  }

  /**
   * Search YouTube videos
   */
  async searchYouTubeVideos(query, options = {}) {
    try {
      const response = await axios.post(
        `${this.baseUrl}/seo/youtube/search`,
        {
          query,
          max_results: options.maxResults || 10,
          order: options.order || 'relevance',
          published_after: options.publishedAfter,
          video_duration: options.videoDuration,
          video_type: options.videoType || 'video'
        },
        { headers: this.authClient.getHeaders() }
      );
      return response.data;
    } catch (error) {
      throw this.authClient.handleError(error);
    }
  }

  /**
   * Get YouTube channel statistics
   */
  async getYouTubeChannelStats(channelId) {
    try {
      const response = await axios.get(
        `${this.baseUrl}/seo/youtube/channel/${channelId}/stats`,
        { headers: this.authClient.getHeaders() }
      );
      return response.data;
    } catch (error) {
      throw this.authClient.handleError(error);
    }
  }

  /**
   * Get YouTube video analytics
   */
  async getYouTubeVideoAnalytics(videoId) {
    try {
      const response = await axios.get(
        `${this.baseUrl}/seo/youtube/video/${videoId}/analytics`,
        { headers: this.authClient.getHeaders() }
      );
      return response.data;
    } catch (error) {
      throw this.authClient.handleError(error);
    }
  }

  /**
   * Track competitor YouTube videos
   */
  async trackCompetitorVideos(competitorId, channelId, options = {}) {
    try {
      const response = await axios.post(
        `${this.baseUrl}/seo/youtube/competitor/${competitorId}/videos`,
        {
          channel_id: channelId,
          max_videos: options.maxVideos || 20,
          published_after: options.publishedAfter
        },
        { headers: this.authClient.getHeaders() }
      );
      return response.data;
    } catch (error) {
      throw this.authClient.handleError(error);
    }
  }
}

// Example usage
async function main() {
  // Authenticate
  const authClient = new CapilyticsAuthClient();
  await authClient.login(
    process.env.CAPILYTICS_EMAIL || 'user@example.com',
    process.env.CAPILYTICS_PASSWORD || 'password'
  );

  const seoClient = new SEOServicesClient(authClient);

  try {
    // Example 1: Google Custom Search
    console.log('Performing Google search...');
    const searchResults = await seoClient.googleSearch(
      'competitive intelligence tools',
      {
        maxResults: 10,
        language: 'en',
        dateRestrict: 'd7'  // Last 7 days
      }
    );
    console.log(`Found ${searchResults.total_results} results`);
    console.log(`\nTop 3 results:`);
    searchResults.results.slice(0, 3).forEach((result, index) => {
      console.log(`${index + 1}. ${result.title}`);
      console.log(`   ${result.link}`);
      console.log(`   ${result.snippet}\n`);
    });

    // Example 2: Track brand mentions
    console.log('\nTracking brand mentions...');
    const mentions = await seoClient.trackBrandMentions('Capilytics', {
      keywords: ['analytics', 'competitive intelligence'],
      competitors: ['CompetitorA', 'CompetitorB'],
      dateRestrict: 'w1',  // Last week
      maxResults: 50
    });
    console.log(`Brand mentions found: ${mentions.mentions_found}`);
    console.log('Sentiment distribution:');
    Object.entries(mentions.sentiment_distribution).forEach(([sentiment, count]) => {
      console.log(`  ${sentiment}: ${count}`);
    });

    // Example 3: Analyze content performance
    console.log('\nAnalyzing content performance...');
    const performance = await seoClient.analyzeContentPerformance(
      'https://mycompany.com/blog/article',
      ['https://competitor1.com', 'https://competitor2.com'],
      ['ranking', 'backlinks', 'social_shares']
    );
    console.log(`Ranking position: ${performance.ranking_position}`);
    console.log(`Backlinks: ${performance.backlink_estimate}`);
    console.log(`Social shares: ${performance.social_shares}`);

    // Example 4: YouTube video search
    console.log('\nSearching YouTube videos...');
    const videos = await seoClient.searchYouTubeVideos(
      'competitive analysis tutorial',
      {
        maxResults: 5,
        order: 'relevance',
        videoDuration: 'medium'
      }
    );
    console.log(`Found ${videos.total_results} videos`);
    console.log('\nTop 3 videos:');
    videos.videos.slice(0, 3).forEach((video, index) => {
      console.log(`${index + 1}. ${video.title}`);
      console.log(`   Channel: ${video.channel_title}`);
      console.log(`   Published: ${video.published_at}\n`);
    });

    // Example 5: Get YouTube channel statistics
    console.log('Getting YouTube channel stats...');
    const channelId = 'UCabc123xyz';
    const channelStats = await seoClient.getYouTubeChannelStats(channelId);
    console.log(`Channel: ${channelStats.title}`);
    console.log(`Subscribers: ${channelStats.subscriber_count.toLocaleString()}`);
    console.log(`Total views: ${channelStats.view_count.toLocaleString()}`);
    console.log(`Videos: ${channelStats.video_count}`);
    console.log(`Upload frequency: ${channelStats.upload_frequency}`);

    // Example 6: Get video analytics
    console.log('\nGetting video analytics...');
    const videoId = 'abc123xyz';
    const videoAnalytics = await seoClient.getYouTubeVideoAnalytics(videoId);
    console.log(`Video: ${videoAnalytics.title}`);
    console.log(`Views: ${videoAnalytics.view_count.toLocaleString()}`);
    console.log(`Likes: ${videoAnalytics.like_count.toLocaleString()}`);
    console.log(`Comments: ${videoAnalytics.comment_count.toLocaleString()}`);
    console.log(`Engagement rate: ${videoAnalytics.engagement_rate.toFixed(2)}%`);

    // Example 7: Track competitor videos
    console.log('\nTracking competitor videos...');
    const tracking = await seoClient.trackCompetitorVideos(
      1,  // competitor_id
      'UCcompetitor123',
      {
        maxVideos: 20,
        publishedAfter: '2025-01-01T00:00:00Z'
      }
    );
    console.log(`Channel: ${tracking.channel_title}`);
    console.log(`Videos analyzed: ${tracking.videos_analyzed}`);
    console.log(`Total views: ${tracking.total_views.toLocaleString()}`);
    console.log(`Avg engagement rate: ${tracking.avg_engagement_rate.toFixed(2)}%`);
    console.log(`Upload frequency: ${tracking.upload_frequency}`);
    console.log(`\nTop topics: ${tracking.trending_topics.join(', ')}`);

  } catch (error) {
    console.error('Error:', error.message);
  }
}

// Run if executed directly
if (require.main === module) {
  main();
}

module.exports = SEOServicesClient;
