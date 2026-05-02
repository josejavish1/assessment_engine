'use client';

import React, { useState, KeyboardEvent as ReactKeyboardEvent, useRef, useEffect } from 'react';
import { Send, Bot, User, Loader2 } from 'lucide-react';
import { ScrollArea } from '@/components/ui/scroll-area';
import { readLiveTrace } from '../actions/trace';
import TextareaAutosize from 'react-textarea-autosize';

export type Message = {
  id: string;
  role: 'user' | 'assistant';
  content: string;
};

interface AgentChatProps {
  messages: Message[];
  isSubmitting: boolean;
  onSendMessage: (content: string) => void;
}

export function AgentChat({ messages, isSubmitting, onSendMessage }: AgentChatProps) {
  const [inputValue, setInputValue] = useState('');
  const [traceMsg, setTraceMsg] = useState('Analizando contexto y rediseñando el plan...');
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isSubmitting, traceMsg]);

  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (isSubmitting) {
      interval = setInterval(async () => {
        const msg = await readLiveTrace();
        setTraceMsg(msg);
      }, 800);
    }
    return () => clearInterval(interval);
  }, [isSubmitting]);

  const handleSend = () => {
    if (inputValue.trim() === '' || isSubmitting) return;
    onSendMessage(inputValue);
    setInputValue('');
  };

  const handleKeyDown = (e: ReactKeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex flex-col h-full bg-muted/10 border-r border-border/50">
      <div className="p-4 border-b border-border/50 bg-background/50 backdrop-blur">
        <h3 className="text-sm font-semibold flex items-center gap-2">
          <Bot className="h-4 w-4 text-primary" /> Architect Agent
        </h3>
      </div>
      
      <div className="flex-1 overflow-y-auto p-4 space-y-6" ref={scrollRef}>
        {messages.map((msg) => (
          <div key={msg.id} className={`flex gap-3 ${msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
            <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 ${msg.role === 'user' ? 'bg-primary text-primary-foreground' : 'bg-muted border border-border text-foreground'}`}>
              {msg.role === 'user' ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
            </div>
            <div className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm ${msg.role === 'user' ? 'bg-primary text-primary-foreground rounded-tr-sm' : 'bg-card border border-border/50 text-foreground rounded-tl-sm shadow-sm'}`}>
              <p className="whitespace-pre-wrap leading-relaxed">{msg.content}</p>
            </div>
          </div>
        ))}
        {isSubmitting && (
          <div className="flex gap-3 flex-row">
            <div className="w-8 h-8 rounded-full flex items-center justify-center shrink-0 bg-muted border border-border text-foreground">
              <Bot className="h-4 w-4" />
            </div>
            <div className="max-w-[85%] rounded-2xl px-4 py-3 text-xs font-mono bg-card border border-border/50 text-muted-foreground rounded-tl-sm shadow-sm flex flex-col gap-2 overflow-hidden">
              <div className="flex items-center gap-2">
                <Loader2 className="h-3 w-3 animate-spin text-primary shrink-0" />
                <span className="font-sans font-medium text-foreground">Razonando...</span>
              </div>
              <p className="truncate opacity-80">{traceMsg}</p>
            </div>
          </div>
        )}
      </div>

      <div className="p-4 bg-background border-t border-border/50">
        <div className="bg-popover border border-border shadow-sm rounded-xl flex items-end p-2 focus-within:ring-2 focus-within:ring-primary/50 transition-all">
          <TextareaAutosize
            className="flex-1 bg-transparent border-none outline-none text-foreground placeholder:text-muted-foreground px-2 py-2 min-h-[44px] max-h-[250px] resize-none text-sm"
            placeholder="Sugiere cambios (ej. Falta añadir un test de seguridad...)"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isSubmitting}
            autoFocus
            minRows={1}
            maxRows={8}
          />
          <button 
            onClick={handleSend}
            disabled={isSubmitting || inputValue.trim() === ''}
            className="bg-primary text-primary-foreground p-2.5 rounded-lg hover:bg-primary/90 disabled:opacity-50 transition-colors mb-0.5 mr-0.5"
          >
            <Send className="h-4 w-4" />
          </button>
        </div>
        <p className="text-[10px] text-center text-muted-foreground mt-2">
          Presiona <kbd className="font-mono bg-muted px-1 rounded">Enter</kbd> para enviar, <kbd className="font-mono bg-muted px-1 rounded">Shift+Enter</kbd> para nueva línea.
        </p>
      </div>
    </div>
  );
}