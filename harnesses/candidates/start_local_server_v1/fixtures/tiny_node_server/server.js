// Minimal dependency-free local server for the start_local_server candidate.
// Binds an OS-assigned port on 127.0.0.1 and prints a localhost URL, mimicking
// a Vite/CRA dev server's "Local: http://..." line.
const http = require("http");

const server = http.createServer((req, res) => {
  res.statusCode = 200;
  res.end("ok");
});

server.listen(0, "127.0.0.1", () => {
  const port = server.address().port;
  console.log("Local: http://127.0.0.1:" + port + "/");
});
