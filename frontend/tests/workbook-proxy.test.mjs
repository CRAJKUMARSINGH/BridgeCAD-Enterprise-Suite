import assert from "node:assert/strict";
import { test } from "node:test";
import exportPackage from "../../netlify/functions/export_package.js";
import generateSamplePdf from "../../netlify/functions/generate_sample_pdf.js";
import predict from "../../netlify/functions/predict.js";
import template from "../../netlify/functions/template.js";

const request = {
  httpMethod: "POST",
  headers: { "content-type": "multipart/form-data; boundary=sample" },
  rawQuery: "output_format=ga_pdf",
  body: "sample workbook",
};

test("workbook proxy protects downloads and hides backend failure details", async (t) => {
  const priorUrl = process.env.FASTAPI_URL;
  process.env.FASTAPI_URL = "https://drawing.example.test";
  t.after(() => {
    if (priorUrl === undefined) delete process.env.FASTAPI_URL;
    else process.env.FASTAPI_URL = priorUrl;
  });

  const upstream = t.mock.method(globalThis, "fetch", async () => new Response("%PDF-example", {
    headers: { "content-type": "application/pdf" },
  }));
  const download = await predict.handler(request);
  assert.equal(upstream.mock.calls[0].arguments[0], "https://drawing.example.test/draw/ga?output_format=ga_pdf");
  assert.equal(download.headers["cache-control"], "no-store");
  assert.equal(Buffer.from(download.body, "base64").toString(), "%PDF-example");

  upstream.mock.mockImplementation(async () => new Response("private/workbook.xlsx", { status: 500 }));
  const failed = await predict.handler(request);
  assert.equal(failed.statusCode, 500);
  assert.equal(failed.headers["cache-control"], "no-store");
  assert.doesNotMatch(failed.body, /private\/workbook/);

  upstream.mock.mockImplementation(async () => { throw new Error("internal backend URL"); });
  const unavailable = await predict.handler(request);
  assert.equal(unavailable.statusCode, 502);
  assert.equal(unavailable.headers["cache-control"], "no-store");
  assert.doesNotMatch(unavailable.body, /internal backend URL/);

  for (const [endpoint, proxy] of [
    ["/package", exportPackage],
    ["/generate_sample_pdf", generateSamplePdf],
    ["/template", template],
  ]) {
    const response = await proxy.handler({ rawQuery: "template_key=sample" });
    assert.equal(upstream.mock.calls.at(-1).arguments[0], `https://drawing.example.test${endpoint}?template_key=sample`);
    assert.equal(response.statusCode, 502);
    assert.equal(response.headers["cache-control"], "no-store");
    assert.doesNotMatch(response.body, /internal backend URL/);
  }
});
