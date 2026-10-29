exports.handler = async (event) => {
  const fastApiUrl = process.env.FASTAPI_URL;
  if (!fastApiUrl) {
    return {
      statusCode: 501,
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ error: "Live Python generation is not configured. Use the review catalogue or set FASTAPI_URL." }),
    };
  }

  try {
    const upstream = await fetch(`${fastApiUrl.replace(/\/$/, "")}/template${event.rawQuery ? `?${event.rawQuery}` : ""}`, {
      method: event.httpMethod || "GET",
    });
    const arrayBuffer = await upstream.arrayBuffer();
    return {
      statusCode: upstream.status,
      isBase64Encoded: true,
      headers: {
        "content-type": upstream.headers.get("content-type") || "application/octet-stream",
        "content-disposition": upstream.headers.get("content-disposition") || "attachment",
      },
      body: Buffer.from(arrayBuffer).toString("base64"),
    };
  } catch (error) {
    return { statusCode: 502, body: JSON.stringify({ error: error instanceof Error ? error.message : "FastAPI proxy failed" }) };
  }
};
