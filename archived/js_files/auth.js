const jwt = require('jsonwebtoken');
const config = require('config');

const authMiddleware = {
  /**
   * Authenticate JWT token
   * @param {Object} req - Express request object
   * @param {Object} res - Express response object
   * @param {Function} next - Express next middleware function
   */
  authenticateToken: (req, res, next) => {
    const authHeader = req.headers['authorization'];
    const token = authHeader && authHeader.split(' ')[1];

    if (token == null) return res.sendStatus(401);

    jwt.verify(token, config.get('auth.jwt.secret'), (err, user) => {
      if (err) return res.sendStatus(403);
      req.user = user;
      next();
    });
  },

  /**
   * Generate JWT token for user
   * @param {Object} user - User object
   * @returns {string} JWT token
   */
  generateToken: (user) => {
    return jwt.sign(
      { 
        id: user.id, 
        email: user.email 
      }, 
      config.get('auth.jwt.secret'), 
      { expiresIn: config.get('auth.jwt.expiresIn') }
    );
  },

  /**
   * Role-based access control
   * @param {string[]} allowedRoles - Roles allowed to access the route
   */
  roleAuthorization: (allowedRoles) => {
    return (req, res, next) => {
      if (!req.user || !allowedRoles.includes(req.user.role)) {
        return res.status(403).json({ message: 'Access denied' });
      }
      next();
    };
  }
};

module.exports = authMiddleware;
