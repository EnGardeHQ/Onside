const Corporation = require('../models/Corporation');

// Create a new corporation
async function createCorporation(corporationData) {
  const corporation = new Corporation(corporationData);
  return await corporation.save();
}

// Get all corporations
async function getAllCorporations() {
  return await Corporation.find();
}

// Get a corporation by ID
async function getCorporationById(id) {
  return await Corporation.findById(id);
}

// Update a corporation by ID
async function updateCorporation(id, updateData) {
  return await Corporation.findByIdAndUpdate(id, updateData, { new: true });
}

// Delete a corporation by ID
async function deleteCorporation(id) {
  return await Corporation.findByIdAndDelete(id);
}

module.exports = {
  createCorporation,
  getAllCorporations,
  getCorporationById,
  updateCorporation,
  deleteCorporation
};
