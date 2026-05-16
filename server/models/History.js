const mongoose = require("mongoose");

const historySchema = new mongoose.Schema({
  userId:    { type: String, required: true },
  fileName:  { type: String, required: true },
  platform:  { type: String, default: "unknown" },
  quality:   { type: String, default: "unknown" },
  sizeMb:    { type: Number, default: 0 },
  url:       { type: String },
  date:      { type: String },
  createdAt: { type: Date, default: Date.now },
});

module.exports = mongoose.model("History", historySchema);