export default {
  server: {
    host: "127.0.0.1", port: 5173, strictPort: true,
    proxy: { "/api": { target: "http://127.0.0.1:8001", changeOrigin: true } },
    // Generated native assets must not reload an in-progress phone capture.
    watch: { ignored: ["**/android/**"] },
  },
  // Keep the exact Figma SVGs as local files instead of inlining the asset
  // catalogue into the initial JavaScript bundle.
  build: { assetsInlineLimit: 0 },
};
