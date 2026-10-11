import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    // EduPath ML/career API (Flask). Run `python app.py` in ../backend.
    proxy: { "/api": "http://127.0.0.1:5000" },
  },
});
