# Start SoilSync locally

1. Install Node.js 22.12 or later and Python 3.12. Clone this repository and open the `SoilSync-Remake` folder in VS Code.
2. For first-time setup, copy `backend/.env.example` to `backend/.env`. Get the team's connection details privately and fill in `DATABASE_URL` for Neon and `MONGODB_RECIPE_URI` for Atlas. Add `GEMINI_API_KEY` if you need live AI. Keep this file out of Git.
3. Open the VS Code terminal in the project folder and run:

   ```powershell
   npm.cmd run dev:setup
   ```

   On macOS or Linux, use `npm run dev:setup`.

The command installs the JavaScript and Python dependencies and starts React and FastAPI. FastAPI connects to the existing cloud databases. Open [SoilSync](http://127.0.0.1:5173/) once the terminal says it is ready. Keep the terminal open and press **Ctrl+C** to stop.
