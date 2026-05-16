const cron = require("node-cron");
const fs = require("fs");
const Download = require("../models/Download");


function startCleanupJob() {
  // Run every 1 minute
  cron.schedule("* * * * *", async () => {
    try {
      const now = new Date();

      // Find all expired records
      const expired = await Download.find({ expiresAt: { $lt: now } });

      if (expired.length === 0) return;

      console.log(`🧹 Cleaning up ${expired.length} expired download(s)...`);

      for (const record of expired) {
        // Delete file from disk
        if (fs.existsSync(record.filePath)) {
          fs.unlinkSync(record.filePath);
          console.log(`   🗑️  Deleted file: ${record.fileName}`);
        }

        // Delete record from MongoDB
        await Download.deleteOne({ _id: record._id });
      }

      console.log(`✅ Cleanup done. Removed ${expired.length} expired link(s).`);

    } catch (err) {
      console.error("Cleanup job error:", err.message);
    }
  });

  console.log("✅ Cleanup job started (runs every minute)");
}


module.exports = { startCleanupJob };