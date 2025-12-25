// src/services/scoreService.js

// Scoring configuration
const SCORING_CONFIG = {
  weights: {
    marketPosition: 1.0,           // Market positioning
    productQuality: 0.9,            // Slightly reduced from uniform weighting
    financialStability: 1.1,        // Reduced from previous version
    revenueGrowth: 1.5,             // Dramatically increased - key for VC interest
    leadershipAndTeam: 1.3,         // Team quality remains paramount
    customerSatisfaction: 1.0,      // Consistent with current implementation
    operationalEfficiency: 0.8,     // Important but not primary driver
    technologyAndIP: 1.1,           // Increased for innovation potential
    scalabilityPotential: 1.3,      // Growth and expansion capability
    legalAndCompliance: 0.9,        // Risk mitigation
    partnershipsAndNetworks: 1.0,   // Ecosystem strength
    sustainabilityAndESG: 1.0       // Growing importance of sustainable practices
  },
  
  // Enhanced validation rules
  validationRules: {
    minValue: 0,
    maxValue: 100,
    requiredFields: [
      'marketPosition', 'productQuality', 'financialStability', 
      'revenueGrowth', 'leadershipAndTeam', 'customerSatisfaction',
      'operationalEfficiency', 'technologyAndIP', 'scalabilityPotential', 
      'legalAndCompliance', 'partnershipsAndNetworks', 'sustainabilityAndESG',
      'regionRiskAdjustmentFactor'
    ]
  }
};

/**
 * Calculate Venture Health Assessment Score (VHAS)
 * @param {Object} data - Comprehensive venture assessment data
 * @param {Object} [customConfig] - Optional custom configuration
 * @returns {Object} Detailed scoring breakdown
 */
const calculateVHASScore = (data, customConfig = {}) => {
  // Merge default and custom configurations
  const config = {
    weights: { ...SCORING_CONFIG.weights, ...(customConfig.weights || {}) },
    validationRules: { 
      ...SCORING_CONFIG.validationRules, 
      ...(customConfig.validationRules || {}) 
    }
  };

  // Validate input data
  const validationErrors = validateInputData(data, config.validationRules);
  if (validationErrors.length > 0) {
    throw new Error(`Validation failed: ${validationErrors.join(', ')}`);
  }

  // Destructure input data
  const {
    marketPosition, productQuality, financialStability, revenueGrowth,
    leadershipAndTeam, customerSatisfaction, operationalEfficiency,
    technologyAndIP, scalabilityPotential, legalAndCompliance,
    partnershipsAndNetworks, sustainabilityAndESG,
    regionRiskAdjustmentFactor
  } = data;

  // Calculate weighted score
  const weightedScore = (
    (marketPosition * config.weights.marketPosition) +
    (productQuality * config.weights.productQuality) +
    (financialStability * config.weights.financialStability) +
    (revenueGrowth * config.weights.revenueGrowth) +
    (leadershipAndTeam * config.weights.leadershipAndTeam) +
    (customerSatisfaction * config.weights.customerSatisfaction) +
    (operationalEfficiency * config.weights.operationalEfficiency) +
    (technologyAndIP * config.weights.technologyAndIP) +
    (scalabilityPotential * config.weights.scalabilityPotential) +
    (legalAndCompliance * config.weights.legalAndCompliance) +
    (partnershipsAndNetworks * config.weights.partnershipsAndNetworks) +
    (sustainabilityAndESG * config.weights.sustainabilityAndESG)
  );

  // Normalize the weighted score
  const totalPossibleWeightedScore = Object.values(config.weights).reduce((a, b) => a + b, 0) * 100;
  const normalizedScore = (weightedScore / totalPossibleWeightedScore) * 1000;

  // Apply region risk adjustment
  const adjustedScore = normalizedScore * (1 - regionRiskAdjustmentFactor);

  // Round and bound the final score
  const finalScore = Math.max(0, Math.min(1000, Math.round(adjustedScore)));

  // Detailed scoring breakdown
  return {
    finalScore,
    weightedScore,
    normalizedScore,
    adjustedScore,
    weightBreakdown: Object.fromEntries(
      Object.entries(config.weights).map(([key, weight]) => [
        key, 
        { 
          rawScore: data[key], 
          weightedContribution: data[key] * weight 
        }
      ])
    ),
    riskAdjustment: {
      regionRiskFactor: regionRiskAdjustmentFactor,
      impactOnScore: normalizedScore - finalScore
    }
  };
};

/**
 * Validate input data against defined rules
 * @param {Object} data - Input data to validate
 * @param {Object} rules - Validation rules
 * @returns {string[]} Array of validation error messages
 */
const validateInputData = (data, rules) => {
  const errors = [];

  // Check for missing required fields
  rules.requiredFields.forEach(field => {
    if (!(field in data)) {
      errors.push(`Missing required field: ${field}`);
    }
  });

  // Validate numeric fields
  rules.requiredFields.forEach(field => {
    const value = data[field];
    if (typeof value !== 'number' || isNaN(value)) {
      errors.push(`Invalid value for ${field}: must be a number`);
    } else if (value < rules.minValue || value > rules.maxValue) {
      errors.push(`${field} must be between ${rules.minValue} and ${rules.maxValue}`);
    }
  });

  return errors;
};

module.exports = {
  calculateVHASScore,
  SCORING_CONFIG
};
