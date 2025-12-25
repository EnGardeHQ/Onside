// src/services/valuationService.js

const calculateDCF = (financialData, assumptions) => {
  const { discountRate, growthRate } = assumptions;

  // Calculate projected cash flows and discount them to the present value
  let totalDCFValue = 0;
  financialData.forEach((yearData, index) => {
    const cashFlow = yearData.cash_flow || 0;
    const discountFactor = Math.pow(1 + discountRate, index + 1);
    totalDCFValue += cashFlow / discountFactor;
  });

  return totalDCFValue;
};

const calculateCCA = (comparableCompanies, financialData) => {
  const { revenue, ebitda } = financialData[financialData.length - 1]; // Use latest financial data
  const averageRevenueMultiple = comparableCompanies.reduce((sum, company) => sum + company.revenue_multiple, 0) / comparableCompanies.length;
  const averageEbitdaMultiple = comparableCompanies.reduce((sum, company) => sum + company.ebitda_multiple, 0) / comparableCompanies.length;

  const valuationFromRevenue = revenue * averageRevenueMultiple;
  const valuationFromEbitda = ebitda * averageEbitdaMultiple;

  return (valuationFromRevenue + valuationFromEbitda) / 2;
};

const calculateHybridValuation = (financialData, comparableCompanies, assumptions, weights) => {
  const dcfValue = calculateDCF(financialData, assumptions);
  const ccaValue = calculateCCA(comparableCompanies, financialData);

  // Weighted average of DCF and CCA valuations
  return (dcfValue * weights.dcf) + (ccaValue * weights.cca);
};

const generateValuationReport = (valuationData) => {
  const {
    financialData,
    comparableCompanies,
    assumptions,
    modelType,
    weights,
  } = valuationData;

  let valuationResult;
  switch (modelType) {
    case 'DCF':
      valuationResult = calculateDCF(financialData, assumptions);
      break;
    case 'CCA':
      valuationResult = calculateCCA(comparableCompanies, financialData);
      break;
    case 'Hybrid':
      valuationResult = calculateHybridValuation(financialData, comparableCompanies, assumptions, weights);
      break;
    default:
      throw new Error("Invalid valuation model type.");
  }

  // Additional risk factor adjustments or sensitivity analysis can be applied here

  return {
    valuationResult,
    confidenceInterval: [valuationResult * 0.95, valuationResult * 1.05], // +/- 5% confidence interval as an example
    assumptions,
    modelType,
  };
};

module.exports = {
  generateValuationReport,
  calculateDCF,
  calculateCCA,
  calculateHybridValuation,
};
