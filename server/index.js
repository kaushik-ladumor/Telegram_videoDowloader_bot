// Load .env — works both locally and on Render
require("dotenv").config({ path: "../.env" });  // local
require("dotenv").config();                       // Render (same folder)

const express  = require("express");
const mongoose = require("mongoose");
const cors     = require("cors");
const path     = require("path");
const fs       = require("fs");

const downloadRoutes = require("./routes/download");
const historyRoutes  = require("./routes/history");
const { startCleanupJob } = require("./jobs/cleanup");

const app  = express();
const PORT = process.env.PORT || 3000;

// Fix downloads path — absolute path
const DOWNLOADS_PATH = path.resolve(process.env.DOWNLOADS_PATH || "./downloads");
process.env.DOWNLOADS_PATH = DOWNLOADS_PATH;

// Create downloads folder if not exists
if (!fs.existsSync(DOWNLOADS_PATH)) {
  fs.mkdirSync(DOWNLOADS_PATH, { recursive: true });
  console.log("📁 Created downloads folder:", DOWNLOADS_PATH);
}

console.log("📁 Downloads path:", DOWNLOADS_PATH);
console.log("🌐 Base URL:", process.env.BASE_URL || `http://localhost:${PORT}`);

// Middleware
app.use(cors());
app.use(express.json());

// Routes
app.use("/api/history", historyRoutes);
app.use("/api/stats",   historyRoutes);
app.use("/api",         downloadRoutes);
app.use("/download",    downloadRoutes);

// Health check
app.get("/", (req, res) => {
  res.json({
    status:   "✅ Telegram Bot Server Running",
    time:     new Date().toISOString(),
    platform: process.env.RENDER ? "Render.com" : "Local",
  });
});

// Connect MongoDB and start server
mongoose
  .connect(process.env.MONGO_URI)
  .then(() => {
    console.log("✅ MongoDB connected");
    startCleanupJob();
    app.listen(PORT, () => {
      console.log(`✅ Server running on port ${PORT}`);
    });
  })
  .catch((err) => {
    console.error("❌ MongoDB error:", err.message);
    process.exit(1);
  });