const express  = require("express");
const router   = express.Router();
const fs       = require("fs");
const path     = require("path");
const History  = require("../models/History");
const Download = require("../models/Download");

// GET /api/history/:userId — get last 5 downloads
router.get("/:userId", async (req, res) => {
  try {
    const { userId } = req.params;
    const history = await History.find({ userId })
      .sort({ createdAt: -1 })
      .limit(5);

    res.json({ history });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// POST /api/history — save a download record
router.post("/", async (req, res) => {
  try {
    const { userId, fileName, platform, quality, sizeMb, url } = req.body;

    const date = new Date().toLocaleString("en-IN", {
      day: "2-digit", month: "short",
      hour: "2-digit", minute: "2-digit"
    });

    const record = await History.create({
      userId, fileName, platform,
      quality, sizeMb, url, date
    });

    res.json({ success: true, record });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// DELETE /api/history/:userId — clear user history
router.delete("/:userId", async (req, res) => {
  try {
    const { userId } = req.params;
    await History.deleteMany({ userId });
    res.json({ success: true, message: "History cleared" });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// GET /api/stats — admin stats
router.get("/admin/stats", async (req, res) => {
  try {
    const totalDownloads = await History.countDocuments();
    const totalUsers     = await History.distinct("userId").then(u => u.length);
    const activeLinks    = await Download.countDocuments({ expiresAt: { $gt: new Date() } });

    // Today's downloads
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const todayDownloads = await History.countDocuments({ createdAt: { $gte: today } });

    // Storage used
    const downloadsPath = process.env.DOWNLOADS_PATH || "../downloads";
    let storageMb = 0;
    try {
      const files = fs.readdirSync(downloadsPath);
      const totalBytes = files.reduce((acc, file) => {
        const filePath = path.join(downloadsPath, file);
        return acc + fs.statSync(filePath).size;
      }, 0);
      storageMb = Math.round(totalBytes / 1024 / 1024 * 100) / 100;
    } catch (e) {}

    res.json({ totalDownloads, todayDownloads, totalUsers, activeLinks, storageMb });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

module.exports = router;