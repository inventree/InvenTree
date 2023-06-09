import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react({
    babel: {
      plugins: ["macros"],
    },
  }),
  ],
  build: {
    manifest: true,
    outDir: "../../InvenTree/web/static/web",
  },
});
