const privateHeaders = { "cache-control": "no-store" };

function jsonFailure(statusCode, error) {
  return {
    statusCode,
    headers: { ...privateHeaders, "content-type": "application/json" },
    body: JSON.stringify({ error }),
  };
}

async function proxyDrawing(event, endpoint, options) {
  const fastApiUrl = process.env.FASTAPI_URL;
  if (!fastApiUrl) {
    return jsonFailure(501, "Live generation is unavailable. You can use live drafting in this browser.");
  }

  try {
    const query = event.rawQuery ? `?${event.rawQuery}` : "";
    const upstream = await fetch(`${fastApiUrl.replace(/\/$/, "")}${endpoint}${query}`, options);
    if (upstream.status >= 500) {
      return jsonFailure(upstream.status, "The drawing service could not complete the request.");
    }
    return {
      statusCode: upstream.status,
      isBase64Encoded: true,
      headers: {
        ...privateHeaders,
        "content-type": upstream.headers.get("content-type") || "application/octet-stream",
        "content-disposition": upstream.headers.get("content-disposition") || "attachment",
      },
      body: Buffer.from(await upstream.arrayBuffer()).toString("base64"),
    };
  } catch {
    return jsonFailure(502, "The drawing service is unavailable.");
  }
}

module.exports = { proxyDrawing };
