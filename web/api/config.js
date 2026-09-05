// Public, non-secret configuration for the browser client.
// ABFINI_API_URL is an endpoint address, not a secret — safe to expose.
// ABFINI_API_KEY is NEVER read or returned here.
module.exports = (req, res) => {
  res.setHeader("Cache-Control", "no-store");
  res.status(200).json({
    apiUrl: process.env.ABFINI_API_URL || null,
  });
};
