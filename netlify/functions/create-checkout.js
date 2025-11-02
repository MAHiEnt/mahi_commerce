// This file handles the "BUY NOW" button.
// It now reads from the new database file name.
const stripe = require('stripe')(process.env.STRIPE_SECRET_KEY);
const products = require('../../product-database.json');

exports.handler = async (event) => {
  let productId;
  try {
    const body = JSON.parse(event.body);
    productId = body.product_id;
  } catch (e) {
    return { statusCode: 400, body: JSON.stringify({ error: "Bad request" }) };
  }

  // Find the product in our "database"
  const product = products.find(p => p.product_id === productId);
  if (!product) {
    return { statusCode: 404, body: JSON.stringify({ error: "Product not found" }) };
  }

  const domain = process.env.YOUR_DOMAIN || 'https://floridamanadventures.com';

  try {
    const session = await stripe.checkout.sessions.create({
      payment_method_types: ['card'],
      line_items: [
        {
          price_data: {
            currency: 'usd',
            product_data: {
              name: product.title,
              images: [product.mockup_url]
            },
            unit_amount: Math.round(product.price * 100), // Stripe needs cents
          },
          quantity: 1,
        },
      ],
      mode: 'payment',
      success_url: `${domain}/success.html`,
      cancel_url: `${domain}/`,
    });

    return {
      statusCode: 200,
      body: JSON.stringify({ url: session.url }),
    };

  } catch (error) {
    console.error("Stripe error:", error.message);
    return { statusCode: 500, body: JSON.stringify({ error: "Stripe error." }) };
  }
};
