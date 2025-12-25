// File: src/middleware/tenantMiddleware.js
module.exports = (req, res, next) => {
  // Development logging
  if (process.env.NODE_ENV !== 'production') {
    console.log('\n=== Request Details ===');
    console.log(`${req.method} ${req.originalUrl}`);
    console.log('Headers:', JSON.stringify(req.headers, null, 2));
  }

  // Get tenant ID - Node.js automatically lowercases headers
  const tenantId = req.headers['x-tenant-id'];

  if (!tenantId) {
    // Development logging
    if (process.env.NODE_ENV !== 'production') {
      console.log('No tenant ID found in request');
    }
    return res.status(400).json({ error: 'Tenant ID is required' });
  }

  // Attach tenant ID to request
  req.tenantId = tenantId;
  
  // Initialize/update body with tenant_id
  if (typeof req.body !== 'object') {
    req.body = {};
  }
  req.body.tenant_id = tenantId;

  // Development logging
  if (process.env.NODE_ENV !== 'production') {
    console.log('Request processed:', {
      url: req.originalUrl,
      method: req.method,
      tenantId,
      path: req.path,
      timestamp: new Date().toISOString()
    });
  }

  next();
};