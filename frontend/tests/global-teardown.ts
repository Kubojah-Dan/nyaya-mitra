import { existsSync, readFileSync, unlinkSync } from "node:fs";
import { spawnSync } from "node:child_process";

async function globalTeardown() {
  if (!existsSync(".next-test-server.pid")) {
    return;
  }

  const pid = Number(readFileSync(".next-test-server.pid", "utf8"));
  if (Number.isInteger(pid) && pid > 0) {
    if (process.platform === "win32") {
      spawnSync("taskkill", ["/PID", String(pid), "/T", "/F"], { stdio: "ignore" });
    } else {
      try {
        process.kill(-pid, "SIGTERM");
      } catch {
        process.kill(pid, "SIGTERM");
      }
    }
  }

  unlinkSync(".next-test-server.pid");
}

export default globalTeardown;
