'use server';

import { EventSource } from 'eventsource';
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { SSEClientTransport } from "@modelcontextprotocol/sdk/client/sse.js";
import { getSessionUser } from "@/lib/auth/session";

// Polyfill for Node.js environment
if (typeof globalThis !== 'undefined' && !(globalThis as unknown as { EventSource: unknown }).EventSource) {
  (globalThis as unknown as { EventSource: unknown }).EventSource = EventSource;
}

interface McpToolTextContent {
  type: string;
  text: string;
}

interface McpToolResult {
  content?: McpToolTextContent[];
}

function extractMcpText(result: unknown): string {
  const toolResult = result as McpToolResult;
  if (toolResult?.content && toolResult.content.length > 0 && toolResult.content[0].text) {
    return toolResult.content[0].text;
  }
  return '{}';
}

function toErrorMessage(err: unknown): string {
  if (err instanceof Error) return err.message;
  return String(err);
}

async function createClient() {
  const transport = new SSEClientTransport(new URL("http://127.0.0.1:8000/sse"));
  const client = new Client(
    { name: "CommandCenter", version: "1.0.0" },
    { capabilities: {} }
  );
  await client.connect(transport);
  return { client, transport };
}

export async function submitProductOwnerRequest(requestText: string) {
  const user = await getSessionUser();
  if (!user) {
    return { success: false, error: "Unauthorized: Authentication session required" };
  }
  if (user.role === 'CLIENT') {
    return { success: false, error: "Forbidden: Product Owner orchestration requires Consultant or Admin privileges" };
  }

  let mcp;
  try {
    mcp = await createClient();

    const result = await mcp.client.callTool({
      name: "start_plan_generation",
      arguments: { request_text: requestText }
    }, undefined, { timeout: 30000 });

    const textContent = extractMcpText(result);
    const data = JSON.parse(textContent);
    return { success: true, jobId: data.job_id };
  } catch (error: unknown) {
    console.error("Error starting plan generation:", error);
    return { success: false, error: toErrorMessage(error) };
  } finally {
    if (mcp) await mcp.client.close();
  }
}

export async function checkPlanStatus(jobId: string) {
  let mcp;
  try {
    mcp = await createClient();

    const result = await mcp.client.callTool({
      name: "check_plan_status",
      arguments: { job_id: jobId }
    }, undefined, { timeout: 10000 });

    const textContent = extractMcpText(result);
    const data = JSON.parse(textContent);
    return { success: true, status: data.status, result: data.result };
  } catch (error: unknown) {
    console.error("Error checking plan status:", error);
    return { success: false, error: toErrorMessage(error) };
  } finally {
    if (mcp) await mcp.client.close();
  }
}

export async function startPlanExecution(requestDir: string, altIndex: number = 0) {
  const user = await getSessionUser();
  if (!user) {
    return { success: false, error: "Unauthorized: Authentication session required" };
  }
  if (user.role === 'CLIENT') {
    return { success: false, error: "Forbidden: Plan execution requires Consultant or Admin privileges" };
  }

  let mcp;
  try {
    mcp = await createClient();

    const result = await mcp.client.callTool({
      name: "start_plan_execution",
      arguments: { request_dir: requestDir, alt_index: altIndex }
    }, undefined, { timeout: 30000 });

    const textContent = extractMcpText(result);
    const data = JSON.parse(textContent);
    return { success: true, jobId: data.job_id };
  } catch (error: unknown) {
    console.error("Error starting plan execution:", error);
    return { success: false, error: toErrorMessage(error) };
  } finally {
    if (mcp) await mcp.client.close();
  }
}

export async function checkExecutionStatus(jobId: string) {
  let mcp;
  try {
    mcp = await createClient();

    const result = await mcp.client.callTool({
      name: "check_execution_status",
      arguments: { job_id: jobId }
    }, undefined, { timeout: 10000 });

    const textContent = extractMcpText(result);
    const data = JSON.parse(textContent);
    return { success: true, status: data.status, result: data.result };
  } catch (error: unknown) {
    console.error("Error checking execution status:", error);
    return { success: false, error: toErrorMessage(error) };
  } finally {
    if (mcp) await mcp.client.close();
  }
}

export async function abortAndRevert() {
  let mcp;
  try {
    mcp = await createClient();

    const result = await mcp.client.callTool({
      name: "abort_and_revert",
      arguments: {}
    }, undefined, { timeout: 30000 });

    const textContent = extractMcpText(result);
    const data = JSON.parse(textContent);
    return { success: true, data };
  } catch (error: unknown) {
    console.error("Error aborting:", error);
    return { success: false, error: toErrorMessage(error) };
  } finally {
    if (mcp) await mcp.client.close();
  }
}

export async function checkActionGate(requestDir: string) {
  let mcp;
  try {
    mcp = await createClient();

    const result = await mcp.client.callTool({
      name: "check_action_gate",
      arguments: { request_dir: requestDir }
    }, undefined, { timeout: 10000 });

    const textContent = extractMcpText(result);
    const data = JSON.parse(textContent);
    return { success: true, data };
  } catch (error: unknown) {
    console.error("Error checking action gate:", error);
    return { success: false, error: toErrorMessage(error) };
  } finally {
    if (mcp) await mcp.client.close();
  }
}

export async function authorizeActionGate(requestDir: string, altIndex: number = 0) {
  let mcp;
  try {
    mcp = await createClient();

    const result = await mcp.client.callTool({
      name: "authorize_action_gate",
      arguments: { request_dir: requestDir, alt_index: altIndex }
    }, undefined, { timeout: 30000 });

    const textContent = extractMcpText(result);
    const data = JSON.parse(textContent);
    return { success: true, data };
  } catch (error: unknown) {
    console.error("Error authorizing action gate:", error);
    return { success: false, error: toErrorMessage(error) };
  } finally {
    if (mcp) await mcp.client.close();
  }
}
