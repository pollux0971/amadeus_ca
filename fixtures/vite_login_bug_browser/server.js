// Full-browser-e2e fixture page. It logs a console.error (the "login bug" symptom
// captured pre-patch) but never throws — so there is no uncaught/fatal page error.
// The underlying bug + fix lives in login.py (verified by test_login.py); the
// patch fixes that, and the post-patch browser re-open confirms the page still
// loads with NO fatal console error.
const http = require("http");

const PAGE = `<!doctype html>
<html>
  <head><title>Login</title></head>
  <body>
    <h1>Login</h1>
    <p>token: <span id="token"></span></p>
    <script>
      console.log("login page booting");
      console.warn("login token may be empty");
      // Non-fatal symptom of the login bug (no throw -> no fatal page error):
      console.error("login token bug: token computed incorrectly");
      document.getElementById("token").textContent = "(see login.py)";
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
