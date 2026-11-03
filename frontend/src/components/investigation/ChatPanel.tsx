import React, { useState, useRef, useEffect } from 'react';
import { 
  Send, Bot, User, Sparkles, RefreshCw, AlertCircle, HelpCircle, 
  MapPin, CheckCircle, ChevronRight, CornerDownLeft, Loader2 
} from 'lucide-react';
import { ChatMessage } from '../../types/investigation';

interface ChatPanelProps {
  messages: ChatMessage[];
  isInvestigating: boolean;
  onSendMessage: (text: string) => void;
  onResetSession: () => void;
  sessionId: string;
}

export const ChatPanel: React.FC<ChatPanelProps> = ({
  messages,
  isInvestigating,
  onSendMessage,
  onResetSession,
  sessionId
}) => {
  const [inputText, setInputText] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isInvestigating]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputText.trim() || isInvestigating) return;
    onSendMessage(inputText.trim());
    setInputText('');
  };

  const handleSuggestionClick = (query: string) => {
    if (isInvestigating) return;
    onSendMessage(query);
  };

  const suggestedQueries = [
    "Why are thousands of fish dying in Bellandur Lake?",
    "Why is pollution increasing around Chennai?",
    "What will happen to PM2.5 in Bengaluru in the next 5 years?",
    "Investigate toxic white froth in Varthur Lake"
  ];

  return (
    <div className="flex flex-col h-full bg-[#050b1a]/95 border-r border-cyan-500/20 backdrop-blur-xl">
      {/* Panel Header */}
      <div className="p-3.5 border-b border-cyan-500/20 flex items-center justify-between bg-[#030612]/90">
        <div className="flex items-center space-x-2.5">
          <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center shadow-lg shadow-cyan-500/20 border border-cyan-400/40">
            <Bot className="w-4 h-4 text-white" />
          </div>
          <div>
            <div className="text-xs font-bold font-mono text-white flex items-center gap-1.5">
              <span>Strands Investigator</span>
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
            </div>
            <div className="text-[10px] text-cyan-400/70 font-mono">
              Session: <span className="text-slate-300">{sessionId.slice(0, 14)}...</span>
            </div>
          </div>
        </div>

        <button
          onClick={onResetSession}
          title="Reset investigation conversation"
          className="p-1.5 rounded-md hover:bg-slate-800 text-slate-400 hover:text-cyan-400 transition-colors"
        >
          <RefreshCw className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* Messages Scroll Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && (
          <div className="py-6 space-y-4 text-center">
            <div className="w-12 h-12 mx-auto rounded-xl bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400 shadow-inner">
              <Sparkles className="w-6 h-6 animate-pulse" />
            </div>
            <div className="space-y-1">
              <h3 className="text-sm font-semibold text-white">AI Environmental Investigator</h3>
              <p className="text-xs text-slate-400 max-w-xs mx-auto">
                Ask environmental questions in natural language. The investigator searches academic literature, inspects sensor telemetry, runs causal analysis, and models future scenarios.
              </p>
            </div>

            {/* Quick Action Suggestions */}
            <div className="pt-2 space-y-1.5 text-left">
              <div className="text-[10px] uppercase font-mono tracking-wider text-slate-500 px-1">
                Suggested Inquiries:
              </div>
              {suggestedQueries.map((sq, i) => (
                <button
                  key={i}
                  onClick={() => handleSuggestionClick(sq)}
                  className="w-full text-left p-2 rounded-lg bg-[#070e24] hover:bg-cyan-950/40 border border-cyan-500/15 hover:border-cyan-400/50 text-xs text-slate-300 hover:text-cyan-200 transition-all flex items-center justify-between group shadow-sm"
                >
                  <span className="truncate mr-2">{sq}</span>
                  <ChevronRight className="w-3.5 h-3.5 text-slate-500 group-hover:text-cyan-400 shrink-0" />
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex flex-col ${msg.sender === 'user' ? 'items-end' : 'items-start'}`}
          >
            <div className="flex items-center gap-1.5 text-[10px] text-slate-500 mb-1 font-mono">
              {msg.sender === 'user' ? (
                <>
                  <span>You</span>
                  <User className="w-3 h-3 text-cyan-400" />
                </>
              ) : (
                <>
                  <Bot className="w-3 h-3 text-cyan-400" />
                  <span className="text-cyan-400 font-semibold">Investigator AI</span>
                </>
              )}
              <span>•</span>
              <span>{msg.timestamp}</span>
            </div>

            <div
              className={`p-3.5 rounded-2xl max-w-[92%] text-xs leading-relaxed shadow-lg ${
                msg.sender === 'user'
                  ? 'bg-gradient-to-r from-cyan-600 to-blue-600 text-white rounded-tr-none'
                  : 'bg-[#09122c] border border-cyan-500/25 text-slate-200 rounded-tl-none font-sans whitespace-pre-wrap'
              }`}
            >
              {msg.text}

              {/* Slot Clarification Cards */}
              {msg.clarification && (
                <div className="mt-3 pt-2.5 border-t border-amber-500/30 bg-amber-500/5 -mx-1 px-2.5 py-2 rounded-lg">
                  <div className="flex items-center gap-1.5 text-amber-400 font-semibold text-xs mb-1.5">
                    <HelpCircle className="w-3.5 h-3.5" />
                    <span>Clarification Needed: {msg.clarification.slot.toUpperCase()}</span>
                  </div>
                  <p className="text-slate-300 text-[11px] mb-2">{msg.clarification.question}</p>
                  
                  {msg.clarification.options && msg.clarification.options.length > 0 && (
                    <div className="flex flex-wrap gap-1.5">
                      {msg.clarification.options.map((opt, idx) => (
                        <button
                          key={idx}
                          onClick={() => handleSuggestionClick(opt)}
                          className="px-2.5 py-1 rounded-md bg-amber-500/20 hover:bg-amber-500/40 border border-amber-500/40 text-amber-200 text-[11px] transition-colors flex items-center gap-1"
                        >
                          <CornerDownLeft className="w-3 h-3 text-amber-300" />
                          <span>{opt}</span>
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        ))}

        {isInvestigating && (
          <div className="flex items-start gap-2 text-xs text-cyan-400 bg-[#070e24]/90 p-3 rounded-xl border border-cyan-500/30 animate-pulse">
            <Loader2 className="w-4 h-4 animate-spin text-cyan-400 shrink-0 mt-0.5" />
            <div className="space-y-0.5">
              <span className="font-semibold">Synthesizing evidence...</span>
              <p className="text-[11px] text-slate-400">
                Coordinating multi-source literature, spatial IDW models, and Bradford Hill criteria.
              </p>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Message Input Form */}
      <form onSubmit={handleSubmit} className="p-3 border-t border-cyan-500/20 bg-[#030612]/95">
        <div className="relative flex items-center">
          <input
            type="text"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            placeholder={isInvestigating ? "Investigating..." : "Ask an environmental question (e.g. fish deaths, smog)..."}
            disabled={isInvestigating}
            className="w-full pl-3.5 pr-11 py-2.5 bg-[#070e24] border border-cyan-500/25 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-400 focus:ring-1 focus:ring-cyan-400/50 disabled:opacity-50 transition-all font-sans"
          />
          <button
            type="submit"
            disabled={!inputText.trim() || isInvestigating}
            className="absolute right-1.5 p-1.5 rounded-lg bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white disabled:opacity-30 disabled:hover:from-cyan-500 disabled:hover:to-blue-600 transition-all shadow-md shadow-cyan-500/20"
          >
            <Send className="w-3.5 h-3.5" />
          </button>
        </div>
      </form>
    </div>
  );
};

