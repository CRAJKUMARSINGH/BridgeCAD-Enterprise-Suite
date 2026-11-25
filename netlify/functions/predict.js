exports.handler = async (event) => {
  const privateHeaders = { "cache-control": "no-store" };
  const jsonFailure = (statusCode, error) => ({
    statusCode,
    headers: { ...privateHeaders, "content-type": "application/json" },
    body: JSON.stringify({ error }),
  });
  const fastApiUrl = process.env.FASTAPI_URL;
  if (!fastApiUrl) {
    return jsonFailure(501, "Live generation is unavailable. You can use live drafting in this browser.");
  }

  try {
    const query = new URLSearchParams(event.rawQuery || "");
    const endpoint = query.get("output_format") === "ga_pdf" ? "/draw/ga" : "/predict";
    const upstream = await fetch(`${fastApiUrl.replace(/\/$/, "")}${endpoint}${event.rawQuery ? `?${event.rawQuery}` : ""}`, {
      method: event.httpMethod,
      headers: { "content-type": event.headers["content-type"] || event.headers["Content-Type"] || "" },
      body: event.body ? Buffer.from(event.body, event.isBase64Encoded ? "base64" : "utf8") : undefined,
    });
    if (upstream.status >= 500) return jsonFailure(upstream.status, "The drawing service could not complete the request.");
    const arrayBuffer = await upstream.arrayBuffer();
    return {
      statusCode: upstream.status,
      isBase64Encoded: true,
      headers: {
        ...privateHeaders,
        "content-type": upstream.headers.get("content-type") || "application/octet-stream",
        "content-disposition": upstream.headers.get("content-disposition") || "attachment",
      },
      body: Buffer.from(arrayBuffer).toString("base64"),
    };
  } catch {
    return jsonFailure(502, "The drawing service is unavailable.");
  }
};
