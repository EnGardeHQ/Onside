const Tenant = require('../models/Tenant'); // Assuming a Tenant model exists

const createTenant = async (tenantData) => {
  try {
    const tenant = new Tenant(tenantData);
    await tenant.save();
    return tenant;
  } catch (error) {
    throw new Error(`Error creating tenant: ${error.message}`);
  }
};

const getTenantById = async (tenantId) => {
  try {
    const tenant = await Tenant.findById(tenantId);
    return tenant;
  } catch (error) {
    throw new Error(`Error fetching tenant: ${error.message}`);
  }
};

const updateTenant = async (tenantId, updateData) => {
  try {
    const updatedTenant = await Tenant.findByIdAndUpdate(tenantId, updateData, { new: true });
    return updatedTenant;
  } catch (error) {
    throw new Error(`Error updating tenant: ${error.message}`);
  }
};

module.exports = {
  createTenant,
  getTenantById,
  updateTenant,
};
