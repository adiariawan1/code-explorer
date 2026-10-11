/**
 * Test script for /api/simulate Route Handler
 * Calls /api/simulate for two different nodes and prints status + response fields (without printing keys).
 */

const BASE_URL = process.argv[2] || process.env.BASE_URL || "http://localhost:3000";

async function testNodeSimulation(testName, payload) {
  console.log(`\n========================================`);
  console.log(`TEST: ${testName}`);
  console.log(`Deleted Node: ${payload.deleted_node.name} (${payload.deleted_node.type})`);
  console.log(`Affected Count: ${payload.affected_nodes.length}`);
  console.log(`========================================`);

  const url = `${BASE_URL.replace(/\/$/, "")}/api/simulate`;

  try {
    const res = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });

    console.log(`HTTP Status: ${res.status} ${res.statusText}`);

    const data = await res.json();

    if (data.error) {
      console.log(`[ERROR RESPONSE] message: ${data.message}`);
      return false;
    }

    console.log(`[RESPONSE FIELDS]`);
    console.log(`- narrative:     ${data.narrative}`);
    console.log(`- severity:      ${data.severity}`);
    console.log(`- reason:        ${data.reason}`);
    console.log(`- is_mock / mock: ${Boolean(data.mock || data.is_mock)}`);
    console.log(`- provider:      ${data.provider || "none"}`);
    if (data.key_warning) {
      console.log(`- key_warning:   ${data.key_warning}`);
    }
    if (data.suggested_fix) {
      console.log(`- suggested_fix.description: ${data.suggested_fix.description}`);
      console.log(`- suggested_fix.code:\n${data.suggested_fix.code}`);
    } else {
      console.log(`- suggested_fix: (none)`);
    }

    return true;
  } catch (err) {
    console.error(`Fetch failed for ${testName}:`, err.message);
    return false;
  }
}

async function main() {
  console.log(`Testing /api/simulate against: ${BASE_URL}`);

  // Test Node 1: Function 'calculate_total'
  const payload1 = {
    deleted_node: {
      name: "calculate_total",
      type: "function",
    },
    code_snippet: `def calculate_total(items, discount):\n    total = 0\n    for price in items:\n        total += validate_item(price)\n    return total * (1 - discount)`,
    affected_nodes: [
      { name: "checkout", relation: "calls calculate_total" },
      { name: "main", relation: "calls checkout (indirect)" },
    ],
    model_provider: "gemini",
  };

  const ok1 = await testNodeSimulation("Node 1: Function 'calculate_total'", payload1);

  // Test Node 2: Variable 'amount'
  const payload2 = {
    deleted_node: {
      name: "amount",
      type: "variable",
    },
    code_snippet: `Variable: amount (declared at L15)\nUsages:\nL16 (modified): amount = calculate_total(items, discount)\nL18 (used): return format_currency(amount)`,
    affected_nodes: [
      { name: "calculate_total", relation: "uses amount" },
      { name: "checkout", relation: "calls calculate_total (indirect)" },
    ],
    model_provider: "claude",
  };

  const ok2 = await testNodeSimulation("Node 2: Variable 'amount'", payload2);

  console.log(`\n========================================`);
  console.log(`SUMMARY: Test 1: ${ok1 ? "PASS" : "FAIL"} | Test 2: ${ok2 ? "PASS" : "FAIL"}`);
  console.log(`========================================\n`);

  if (!ok1 || !ok2) {
    process.exit(1);
  }
}

main();
