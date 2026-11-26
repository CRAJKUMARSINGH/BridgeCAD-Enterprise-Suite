const { proxyDrawing } = require("../lib/drawing-proxy.cjs");

exports.handler = (event) => proxyDrawing(event, "/template", { method: event.httpMethod || "GET" });
