// Server-side proxy to the real ABFINI API.
// ABFINI_API_KEY lives only in this Vercel serverless function's environment
// and is never sent to, or readable by, the browser.
module.exports = async (req, res) => {
  if (req.method !== "POST") {
    res.status(405).json({ detail: "Method not allowed" });
    return;
  }

  const apiUrl = process.env.ABFINI_API_URL;
  const apiKey = process.env.ABFINI_API_KEY;
  if (!apiUrl || !apiKey) {
    res.status(503).json({ detail: "ABFINI_API_URL / ABFINI_API_KEY is not configured on Vercel" });
    return;
  }

  const message = req.body && typeof req.body === "object" ? req.body.message : undefined;
  if (typeof message !== "string" || !message.trim()) {
    res.status(422).json({ detail: "message is required" });
    return;
  }

  try {
    const upstream = await fetch(`${apiUrl.replace(/\/$/, "")}/v1/chat`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${apiKey}`,
      },
      body: JSON.stringify({ message }),
    });
    const body = await upstream.json();
    res.status(upstream.status).json(body);
  } catch (err) {
    res.status(502).json({ detail: "ABFINI backend unavailable" });
  }
};
