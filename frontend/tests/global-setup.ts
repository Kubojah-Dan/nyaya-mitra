import { spawn } from "node:child_process";
import { writeFile } from "node:fs/promises";
import http from "node:http";

const SERVER_URL = "http://127.0.0.1:3000";

function canReachServer(): Promise<boolean> {
  return new Promise((resolve) => {
    const request = http.get(SERVER_URL, (response) => {
      response.resume();
      resolve(true);
    });
    request.on("error", () => resolve(false));
    request.setTimeout(1_000, () => {
      request.destroy();
      resolve(false);
    });
  });
}

async function waitForServer(): Promise<void> {
  const deadline = Date.now() + 120_000;
  while (Date.now() < deadline) {
    if (await canReachServer()) {
      return;
    }
    await new Promise((resolve) => setTimeout(resolve, 500));
  }
  throw new Error(`Timed out waiting for ${SERVER_URL}`);
}

async function globalSetup() {
  if (await canReachServer()) {
    return;
  }

  const child = spawn(
    process.execPath,
    ["node_modules/next/dist/bin/next", "start", "--hostname", "127.0.0.1", "--port", "3000"],
    {
      detached: true,
      stdio: "ignore",
      windowsHide: true,
    },
  );

  child.unref();
  await writeFile(".next-test-server.pid", String(child.pid), "utf8");
  await waitForServer();
}

export default globalSetup;
