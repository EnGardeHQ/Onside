const pgClient = require('../config/dbConfig');

const logDataset = async (datasetName, description, storageLocation) => {
  try {
    const query = `
      INSERT INTO datasets (dataset_name, description, storage_location, creation_time, last_modified_time)
      VALUES ($1, $2, $3, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
      RETURNING dataset_id;
    `;
    const values = [datasetName, description, storageLocation];

    const result = await pgClient.query(query, values);
    return result.rows[0].dataset_id;
  } catch (error) {
    console.error('Error logging dataset:', error);
    throw error;
  }
};

module.exports = {
  logDataset,
};
