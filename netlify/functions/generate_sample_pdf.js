const { proxyDrawing } = require("../lib/drawing-proxy.cjs");

exports.handler = (event) => proxyDrawing(event, "/generate_sample_pdf", { method: event.httpMethod || "GET" });
