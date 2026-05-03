'use server';

import * as fs from 'fs';
import * as path from 'path';

export async function readLiveTrace() {
  try {
    const tracePath = path.resolve(process.cwd(), '../../working/live_trace.txt');
    if (!fs.existsSync(tracePath)) {
      return "Inicializando agente...";
    }
    
    const content = fs.readFileSync(tracePath, 'utf-8');
    const lines = content.split('\n').filter(l => l.trim() !== '');
    if (lines.length > 0) {
      return lines[lines.length - 1]; // Return the last trace event
    }
    return "Analizando contexto y rediseñando el plan...";
  } catch (e) {
    return "Explorando repositorio...";
  }
}
