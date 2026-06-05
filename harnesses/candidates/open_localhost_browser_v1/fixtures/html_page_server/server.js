// Minimal dependency-free server that serves a small HTML page, so the browser
// candidate has a title, link, button, and form to snapshot. Binds an
// OS-assigned port on 127.0.0.1 and prints a localhost URL.
const http = require("http");

const PAGE = `<!doctype html>
<html>
  <head><title>Keep-Alive Demo</title></head>
  <body>
    <h1>Hello from the keep-alive server</h1>
    <p>It works.</p>
    <a href="/about">About</a>
    <button id="go">Go</button>
    <form action="/submit" method="post">
      <input name="q" />
      <input type="submit" value="Send" />
    </form>
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
