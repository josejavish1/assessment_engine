'use server';

import { EventSource } from 'eventsource';
// Polyfill for Node.js environment
if (typeof global !== 'undefined' && !global.EventSource) {
  (global as any).EventSource = EventSource;
}

import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { SSEClientTransport } from "@modelcontextprotocol/sdk/client/sse.js";

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
  let mcp;
  try {
    mcp = await createClient();
    
    const result = await mcp.client.callTool({
      name: "start_plan_generation",
      arguments: { request_text: requestText }
    }, undefined, { timeout: 30000 });
    
    const textContent = (result as any).content[0].text;
    const data = JSON.parse(textContent);
    return { success: true, jobId: data.job_id };
  } catch (error: any) {
    console.error("Error starting plan generation:", error);
    return { success: false, error: error.message };
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
    
    const textContent = (result as any).content[0].text;
    const data = JSON.parse(textContent);
    return { success: true, status: data.status, result: data.result };
  } catch (error: any) {
    console.error("Error checking plan status:", error);
    return { success: false, error: error.message };
  } finally {
    if (mcp) await mcp.client.close();
  }
}

export async function startPlanExecution(requestDir: string, altIndex: number = 0) {
  let mcp;
  try {
    mcp = await createClient();
    
    const result = await mcp.client.callTool({
      name: "start_plan_execution",
      arguments: { request_dir: requestDir, alt_index: altIndex }
    }, undefined, { timeout: 30000 });
    
    const textContent = (result as any).content[0].text;
    const data = JSON.parse(textContent);
    return { success: true, jobId: data.job_id };
  } catch (error: any) {
    console.error("Error starting plan execution:", error);
    return { success: false, error: error.message };
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
    
    const textContent = (result as any).content[0].text;
    const data = JSON.parse(textContent);
    return { success: true, status: data.status, result: data.result };
  } catch (error: any) {
    console.error("Error checking execution status:", error);
    return { success: false, error: error.message };
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
    
    const textContent = (result as any).content[0].text;
    const data = JSON.parse(textContent);
    return { success: true, data };
  } catch (error: any) {
    console.error("Error aborting:", error);
    return { success: false, error: error.message };
  } finally {
    if (mcp) await mcp.client.close();
  }
}
