// This file serves your product list.
const products = require('../../products.json');

exports.handler = async () => {
  return {
    statusCode: 200,
    body: JSON.stringify(products),
  };
};
