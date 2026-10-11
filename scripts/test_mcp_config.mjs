import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";
import ts from "../web/node_modules/typescript/lib/typescript.js";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Load and transpile web/lib/mcp-config.ts
const tsFilePath = path.resolve(__dirname, "../web/lib/mcp-config.ts");
const tsCode = fs.readFileSync(tsFilePath, "utf-8");
const jsCode = ts.transpileModule(tsCode, {
  compilerOptions: { module: ts.ModuleKind.CommonJS },
}).outputText;

const mod = {};
const evalModule = new Function("exports", jsCode);
evalModule(mod);

const { buildMcpConfig, validateMcpInputs, maskApiKey } = mod;

console.log("=== Running MCP Config Unit Tests (scripts/test_mcp_config.mjs) ===\n");

let passed = 0;
let failed = 0;

function assert(condition, message) {
  if (condition) {
    console.log(`[PASS] ${message}`);
    passed++;
  } else {
    console.error(`[FAIL] ${message}`);
    failed++;
  }
}

// 1. Test Windows Configuration
console.log("1. Testing Windows Configuration with fake key 'sk-test'...");
const winParams = {
  projectName: "starter_project",
  url: "http://localhost:7860/", // trailing slash to test stripping
  projectId: "6780477b-03c0-46de-a1ba-ceb3b82c5b8c",
  apiKey: "sk-test",
  os: "windows",
};

const winConfig = buildMcpConfig(winParams);
const winJsonStr = JSON.stringify(winConfig, null, 2);

// Check JSON.parse
let winParsed;
try {
  winParsed = JSON.parse(winJsonStr);
  assert(true, "Windows config successfully passed JSON.parse");
} catch (e) {
  assert(false, `Windows config failed JSON.parse: ${e.message}`);
}

// Check server key naming: 'lf-' + name with spaces replaced by underscore
assert(
  winParsed && winParsed.mcpServers["lf-starter_project"] !== undefined,
  "Server key is correctly 'lf-starter_project'"
);

const winServer = winParsed.mcpServers["lf-starter_project"];

// Check command
assert(winServer.command === "cmd", "Windows command is 'cmd'");

// Check args exact match
const expectedWinArgs = [
  "/c",
  "uvx",
  "mcp-proxy",
  "--headers",
  "x-api-key",
  "sk-test",
  "http://localhost:7860/api/v1/mcp/project/6780477b-03c0-46de-a1ba-ceb3b82c5b8c/streamable",
];

assert(
  JSON.stringify(winServer.args) === JSON.stringify(expectedWinArgs),
  "Windows args exactly match specification (/c, uvx, mcp-proxy, --headers, x-api-key, key, endpoint)"
);

// Check no double slash in URL
const endpoint = winServer.args[winServer.args.length - 1];
assert(
  !endpoint.replace("http://", "").includes("//"),
  `URL endpoint has no double slashes: ${endpoint}`
);

// 2. Test macOS / Linux Configuration
console.log("\n2. Testing macOS/Linux Configuration with fake key 'sk-test'...");
const posixParams = {
  projectName: "data pipeline",
  url: "https://langflow.internal.company.com",
  projectId: "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  apiKey: "sk-test",
  os: "posix",
};

const posixConfig = buildMcpConfig(posixParams);
const posixJsonStr = JSON.stringify(posixConfig, null, 2);

let posixParsed;
try {
  posixParsed = JSON.parse(posixJsonStr);
  assert(true, "macOS/Linux config successfully passed JSON.parse");
} catch (e) {
  assert(false, `macOS/Linux config failed JSON.parse: ${e.message}`);
}

assert(
  posixParsed && posixParsed.mcpServers["lf-data_pipeline"] !== undefined,
  "Spaces in project name replaced with underscore: 'lf-data_pipeline'"
);

const posixServer = posixParsed.mcpServers["lf-data_pipeline"];

// Check command is 'uvx' and args omit '/c' and 'uvx'
assert(posixServer.command === "uvx", "macOS/Linux command is 'uvx'");

const expectedPosixArgs = [
  "mcp-proxy",
  "--headers",
  "x-api-key",
  "sk-test",
  "https://langflow.internal.company.com/api/v1/mcp/project/a1b2c3d4-e5f6-7890-abcd-ef1234567890/streamable",
];

assert(
  JSON.stringify(posixServer.args) === JSON.stringify(expectedPosixArgs),
  "macOS/Linux args start directly with mcp-proxy without /c and uvx"
);

// 3. Test Validation Logic
console.log("\n3. Testing Input Validation & Masking...");
const invalidUrl = validateMcpInputs({ url: "ftp://wrong.com", projectId: "uuid", apiKey: "sk-test" });
assert(!invalidUrl.isValid && invalidUrl.errorField === "url", "Rejects URL not starting with http:// or https://");

const invalidPid = validateMcpInputs({ url: "http://localhost:7860", projectId: "invalid-uuid", apiKey: "sk-test" });
assert(!invalidPid.isValid && invalidPid.errorField === "projectId", "Rejects non-UUID Project ID");

const emptyKey = validateMcpInputs({ url: "http://localhost:7860", projectId: "6780477b-03c0-46de-a1ba-ceb3b82c5b8c", apiKey: "   " });
assert(!emptyKey.isValid && emptyKey.errorField === "apiKey", "Rejects empty API key");

const validInputs = validateMcpInputs({ url: "http://localhost:7860", projectId: "6780477b-03c0-46de-a1ba-ceb3b82c5b8c", apiKey: "sk-test" });
assert(validInputs.isValid, "Accepts valid inputs");

const masked = maskApiKey("sk-test-secret-12345");
assert(masked.startsWith("sk-") && masked.includes("••••"), `Key is properly masked: ${masked}`);

console.log("\n=== TEST SUMMARY ===");
console.log(`Passed: ${passed} | Failed: ${failed}`);
if (failed > 0) {
  process.exit(1);
} else {
  console.log("All MCP config tests passed successfully!");
}
