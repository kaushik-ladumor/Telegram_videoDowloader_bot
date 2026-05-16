const express = require("express");
const router = express.Router();
const { v4: uuidv4 } = require("uuid");
const path = require("path");
const fs = require("fs");
const Download = require("../models/Download");

const BASE_URL = process.env.BASE_URL || "http://localhost:3000";
const EXPIRY_MINUTES = parseInt(process.env.LINK_EXPIRY_MINUTES) || 10;


// POST /api/create-link
// Called by Python bot after video is downloaded
router.post("/create-link", async (req, res) => {
  try {
    const { filePath, fileName } = req.body;

    if (!filePath || !fileName) {
      return res.status(400).json({ error: "filePath and fileName are required" });
    }

    // Check file actually exists
    if (!fs.existsSync(filePath)) {
      return res.status(404).json({ error: "File not found on server" });
    }

    // Generate unique token
    const token = uuidv4();

    // Calculate expiry time
    const expiresAt = new Date(Date.now() + EXPIRY_MINUTES * 60 * 1000);

    // Save to MongoDB
    await Download.create({
      token,
      filePath,
      fileName,
      expiresAt,
    });

    const downloadUrl = `${BASE_URL}/download/${token}`;

    console.log(`✅ Link created: ${downloadUrl} (expires at ${expiresAt.toLocaleTimeString()})`);

    res.json({
      url: downloadUrl,
      token,
      expiresAt,
      expiryMinutes: EXPIRY_MINUTES,
    });

  } catch (err) {
    console.error("Create link error:", err.message);
    res.status(500).json({ error: "Failed to create download link" });
  }
});


// GET /download/:token
// User clicks this link in Telegram
router.get("/:token", async (req, res) => {
  try {
    const { token } = req.params;

    // Find token in DB
    const record = await Download.findOne({ token });

    // Token not found
    if (!record) {
      return res.status(404).send(`
        <html>
          <body style="font-family:sans-serif;text-align:center;padding:50px;background:#1a1a2e;color:white">
            <h1>❌ Link Not Found</h1>
            <p>This download link is invalid or has already been deleted.</p>
            <p>Go back to the bot and try again.</p>
          </body>
        </html>
      `);
    }

    // Token expired
    if (new Date() > record.expiresAt) {
      // Delete expired record
      await Download.deleteOne({ token });

      // Delete file if exists
      if (fs.existsSync(record.filePath)) {
        fs.unlinkSync(record.filePath);
      }

      return res.status(410).send(`
        <html>
          <body style="font-family:sans-serif;text-align:center;padding:50px;background:#1a1a2e;color:white">
            <h1>⏰ Link Expired</h1>
            <p>This download link has expired (links are valid for ${EXPIRY_MINUTES} minutes).</p>
            <p>Go back to the bot and request a new link.</p>
          </body>
        </html>
      `);
    }

    // Check file exists on disk
    if (!fs.existsSync(record.filePath)) {
      return res.status(404).send(`
        <html>
          <body style="font-family:sans-serif;text-align:center;padding:50px;background:#1a1a2e;color:white">
            <h1>❌ File Missing</h1>
            <p>The file no longer exists on the server.</p>
          </body>
        </html>
      `);
    }

    console.log(`📥 File downloaded: ${record.fileName}`);

    // Serve the file as download
    res.download(record.filePath, record.fileName, (err) => {
      if (err) {
        console.error("Download serve error:", err.message);
      }
    });

  } catch (err) {
    console.error("Download route error:", err.message);
    res.status(500).send("Server error");
  }
});


module.exports = router;