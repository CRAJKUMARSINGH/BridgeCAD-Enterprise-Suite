const { proxyDrawing } = require("../lib/drawing-proxy.cjs");

exports.handler = (event) => proxyDrawing(event, "/package", { method: event.httpMethod || "GET" });
