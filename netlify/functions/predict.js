const { proxyDrawing } = require("../lib/drawing-proxy.cjs");

exports.handler = (event) => {
  const query = new URLSearchParams(event.rawQuery || "");
  const endpoint = query.get("output_format") === "ga_pdf" ? "/draw/ga" : "/predict";
  const headers = event.headers ?? {};
  return proxyDrawing(event, endpoint, {
    method: event.httpMethod,
    headers: { "content-type": headers["content-type"] || headers["Content-Type"] || "" },
    body: event.body ? Buffer.from(event.body, event.isBase64Encoded ? "base64" : "utf8") : undefined,
  });
};
