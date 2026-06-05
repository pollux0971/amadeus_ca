import React from "react";
import { createRoot } from "react-dom/client";

function Login() {
  const user = { token: "" };
  const token = user?.token ?? "";
  return <div>Login token: {token}</div>;
}

createRoot(document.getElementById("root")).render(<Login />);
