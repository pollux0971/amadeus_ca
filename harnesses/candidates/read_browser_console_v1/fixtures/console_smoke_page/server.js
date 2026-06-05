// Minimal localhost page that emits known console output (no uncaught error),
// so the console collector has deterministic log/warn/error/info to classify.
const http = require("http");

const PAGE = `<!doctype html>
<html>
  <head><title>Console Smoke</title></head>
  <body>
    <h1>console smoke</h1>
    <script>
      console.log("hello");
      console.info("info msg");
      console.warn("warn message");
      console.error("boom error");
    </script>
  </body>
</html>`;

const server = http.createServer((req, res) => {
  res.statusCode = 200;
  res.setHeader("Content-Type", "text/html; charset=utf-8");
  res.end(PAGE);
});

server.listen(0, "127.0.0.1", () => {
  console.log("Local: http://127.0.0.1:" + server.address().port + "/");
});
