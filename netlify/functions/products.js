// This file serves your product list.
// It now reads from the new database file name.
const products = require('../../product-database.json');

exports.handler = async () => {
  return {
    statusCode: 200,
    body: JSON.stringify(products),
  };
};
