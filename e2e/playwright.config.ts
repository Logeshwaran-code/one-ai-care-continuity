import { defineConfig } from "@playwright/test";
export default defineConfig({ testDir: ".", use: { baseURL: process.env.BASE_URL || "http://localhost:8000" }, timeout: 30000 });
