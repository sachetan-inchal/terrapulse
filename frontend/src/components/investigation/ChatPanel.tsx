import React, { useState, useRef, useEffect } from 'react';
import { 
  Send, Bot, User, Sparkles, RefreshCw, AlertCircle, HelpCircle, 
  MapPin, CheckCircle, ChevronRight, CornerDownLeft, Loader2,
  ExternalLink, BookOpen, TrendingUp, ShieldCheck, ChevronDown, 
  ChevronUp, Square, RotateCcw, FileText, Layers
} from 'lucide-react';
import { ChatMessage } from '../../types/investigation';

interface ChatPanelProps {
  messages: ChatMessage[];
  isInvestigating: boolean;
  onSendMessage: (text: string) => void;
  onResetSession: () => void;
  onStopGeneration?: () => void;
  sessionId: string;
  currentLocationName?: string;
}

// ---------------------------------------------------------------------------
// Markdown & Rich Content Inline Parser
// ---------------------------------------------------------------------------
function renderInlineContent(text: string): React.ReactNode {
  // Regex to split by links [text](url), bold **text**, italic *text*, and code `code`
  const regex = /(\[[^\]]+\]\([^)]+\)|\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`)/g;
  const parts = text.split(regex);

  return parts.map((part, index) => {
    // 1. Link [label](url)
    const linkMatch = part.match(/^\[([^\]]+)\]\(([^)]+)\)$/);
    if (linkMatch) {
      const [, label, url] = linkMatch;
      const isDoi = label.toLowerCase().includes('doi') || url.includes('doi.org');
      return (
        <a
          key={index}
          href={url}
          target="_blank"
          rel="noopener noreferrer"
          className={`inline-flex items-center gap-0.5 font-mono underline transition-colors ${
            isDoi 
              ? 'text-cyan-300 hover:text-cyan-100 font-semibold bg-cyan-950/60 px-1 py-0.2 rounded border border-cyan-500/30' 
              : 'text-blue-400 hover:text-blue-200'
          }`}
        >
          <span>{label}</span>
          <ExternalLink className="w-2.5 h-2.5 inline-block opacity-80 shrink-0" />
        </a>
      );
    }

    // 2. Bold **text**
    if (part.startsWith('**') && part.endsWith('**') && part.length >= 4) {
      return (
        <strong key={index} className="font-semibold text-white">
          {part.slice(2, -2)}
        </strong>
      );
    }

    // 3. Italic *text*
    if (part.startsWith('*') && part.endsWith('*') && part.length >= 2 && !part.startsWith('**')) {
      return (
        <em key={index} className="italic text-slate-300">
          {part.slice(1, -1)}
        </em>
      );
    }

    // 4. Inline code `text`
    if (part.startsWith('`') && part.endsWith('`') && part.length >= 2) {
      return (
        <code key={index} className="px-1 py-0.5 rounded bg-[#030612] text-cyan-300 border border-cyan-500/30 font-mono text-[10px]">
          {part.slice(1, -1)}
        </code>
      );
    }

    // Standard plain text
    return <span key={index}>{part}</span>;
  });
}

export const FormattedMessage: React.FC<{ content: string }> = ({ content }) => {
  const lines = content.split('\n');
  const elements: React.ReactNode[] = [];
  let inList = false;
  let listItems: React.ReactNode[] = [];
  let tableRows: string[][] = [];
  let inTable = false;

  const flushList = () => {
    if (inList && listItems.length > 0) {
      elements.push(
        <ul key={`ul_${elements.length}`} className="my-2 space-y-1 pl-1">
          {listItems}
        </ul>
      );
      listItems = [];
      inList = false;
    }
  };

  const flushTable = () => {
    if (inTable && tableRows.length > 0) {
      elements.push(
        <div key={`table_${elements.length}`} className="my-2.5 overflow-x-auto rounded-lg border border-cyan-500/20 bg-[#030612]/80">
          <table className="w-full text-left border-collapse text-[11px]">
            <tbody>
              {tableRows.map((row, rIdx) => (
                <tr key={rIdx} className={rIdx === 0 ? 'bg-cyan-950/40 border-b border-cyan-500/30 font-semibold text-cyan-200' : 'border-b border-slate-800/60 hover:bg-slate-800/20'}>
                  {row.map((cell, cIdx) => (
                    <td key={cIdx} className="px-2.5 py-1.5 font-sans">
                      {renderInlineContent(cell.trim())}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      );
      tableRows = [];
      inTable = false;
    }
  };

  for (let i = 0; i < lines.length; i++) {
    const rawLine = lines[i];
    const trimmed = rawLine.trim();

    if (!trimmed) {
      flushList();
      flushTable();
      continue;
    }

    // Table Row detection (| a | b |)
    if (trimmed.startsWith('|') && trimmed.endsWith('|')) {
      flushList();
      if (trimmed.includes('---')) {
        // Divider row, skip
        continue;
      }
      inTable = true;
      const cells = trimmed.slice(1, -1).split('|');
      tableRows.push(cells);
      continue;
    } else {
      flushTable();
    }

    // Heading 3: ###
    if (trimmed.startsWith('### ')) {
      flushList();
      elements.push(
        <h3 key={`h3_${i}`} className="text-xs font-bold text-white font-mono uppercase tracking-wide text-cyan-300 mt-3 mb-1 flex items-center gap-1.5 border-b border-cyan-500/20 pb-1">
          <Sparkles className="w-3 h-3 text-cyan-400 shrink-0" />
          <span>{trimmed.slice(4)}</span>
        </h3>
      );
      continue;
    }

    // Heading 4: ####
    if (trimmed.startsWith('#### ')) {
      flushList();
      elements.push(
        <h4 key={`h4_${i}`} className="text-[11px] font-bold text-slate-200 font-mono mt-2 mb-1 text-cyan-400 flex items-center gap-1">
          <span>{trimmed.slice(5)}</span>
        </h4>
      );
      continue;
    }

    // Blockquote / Scientific Integrity Rule (> )
    if (trimmed.startsWith('> ')) {
      flushList();
      elements.push(
        <div key={`bq_${i}`} className="my-2 p-2.5 rounded-lg bg-cyan-950/20 border-l-2 border-cyan-400 text-slate-300 text-[11px] leading-relaxed shadow-sm">
          {renderInlineContent(trimmed.slice(2))}
        </div>
      );
      continue;
    }

    // Bullet list item (- or *)
    if (trimmed.startsWith('- ') || trimmed.startsWith('* ')) {
      inList = true;
      listItems.push(
        <li key={`li_${i}`} className="flex items-start gap-1.5 text-slate-300 text-[11px] leading-relaxed">
          <span className="text-cyan-400 select-none mt-0.5">•</span>
          <span className="flex-1">{renderInlineContent(trimmed.slice(2))}</span>
        </li>
      );
      continue;
    }

    // Numbered list item (1. , 2. )
    const numMatch = trimmed.match(/^(\d+)\.\s+(.*)$/);
    if (numMatch) {
      flushList();
      elements.push(
        <div key={`num_${i}`} className="flex items-start gap-2 my-1.5 text-slate-300 text-[11px] leading-relaxed">
          <span className="px-1.5 py-0.2 rounded bg-cyan-500/20 text-cyan-300 font-mono text-[9px] font-bold shrink-0 mt-0.5 border border-cyan-500/30">
            {numMatch[1]}
          </span>
          <span className="flex-1">{renderInlineContent(numMatch[2])}</span>
        </div>
      );
      continue;
    }

    // Standard paragraph
    flushList();
    elements.push(
      <p key={`p_${i}`} className="my-1.5 text-slate-300 text-[11px] leading-relaxed font-sans">
        {renderInlineContent(trimmed)}
      </p>
    );
  }

  flushList();
  flushTable();

  return <div className="space-y-1">{elements}</div>;
};

// ---------------------------------------------------------------------------
// Main Conversational Assistant Panel
// ---------------------------------------------------------------------------
export const ChatPanel: React.FC<ChatPanelProps> = ({
  messages,
  isInvestigating,
  onSendMessage,
  onResetSession,
  onStopGeneration,
  sessionId,
  currentLocationName = "Bengaluru, Karnataka, India"
}) => {
  const [inputText, setInputText] = useState('');
  const [expandedEvidenceId, setExpandedEvidenceId] = useState<string | null>(null);
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
    "Which is the highest mountain in India?",
    "Why is air pollution increasing in Chennai?",
    "What is NDVI?",
    "Analyze vegetation changes in the Amazon rainforest.",
    "Find scientific research about groundwater contamination."
  ];

  const lastMessage = messages.length > 0 ? messages[messages.length - 1] : null;

  return (
    <div className="flex flex-col h-full bg-[#050b1a]/95 border-r border-cyan-500/20 backdrop-blur-xl">
      {/* 1. Panel Header with Active Location Context Pill */}
      <div className="p-3 border-b border-cyan-500/20 flex items-center justify-between bg-[#030612]/90">
        <div className="flex items-center space-x-2.5 overflow-hidden">
          <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center shadow-lg shadow-cyan-500/20 border border-cyan-400/40 shrink-0">
            <Bot className="w-4 h-4 text-white" />
          </div>
          <div className="truncate">
            <div className="text-xs font-bold font-mono text-white flex items-center gap-1.5 truncate">
              <span>AI Environmental Investigator</span>
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse shrink-0"></span>
            </div>
            <div className="text-[10px] text-cyan-400/80 font-mono flex items-center gap-1 truncate">
              <MapPin className="w-2.5 h-2.5 text-cyan-400 shrink-0" />
              <span className="truncate">{currentLocationName || 'Global Investigation Space'}</span>
            </div>
          </div>
        </div>

        <button
          onClick={onResetSession}
          title="New Investigation (Reset session context)"
          className="flex items-center gap-1 px-2 py-1 rounded bg-[#070e24] hover:bg-cyan-950/40 border border-cyan-500/20 hover:border-cyan-400/50 text-[10px] font-mono text-slate-300 hover:text-cyan-300 transition-colors shadow-sm shrink-0"
        >
          <RotateCcw className="w-3 h-3 text-cyan-400" />
          <span>New</span>
        </button>
      </div>

      {/* 2. Messages Scroll Area */}
      <div className="flex-1 overflow-y-auto p-3.5 space-y-4">
        {messages.length === 0 && (
          <div className="py-6 space-y-3.5 text-center">
            <div className="w-11 h-11 mx-auto rounded-xl bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400 shadow-inner">
              <Sparkles className="w-5 h-5 animate-pulse" />
            </div>
            <div className="space-y-1">
              <h3 className="text-xs font-bold font-mono uppercase tracking-wider text-white">
                Conversational Investigation Assistant
              </h3>
              <p className="text-[11px] text-slate-400 max-w-xs mx-auto leading-relaxed">
                Ask any question in natural language about environmental changes, pollution causes, research literature, or 5-year forecasts.
              </p>
            </div>

            {/* Suggested Inquiry Pills */}
            <div className="pt-2 space-y-1.5 text-left">
              <div className="text-[10px] uppercase font-mono tracking-wider text-slate-500 px-1">
                Suggested Questions:
              </div>
              {suggestedQueries.map((sq, i) => (
                <button
                  key={i}
                  onClick={() => handleSuggestionClick(sq)}
                  className="w-full text-left p-2 rounded-lg bg-[#070e24] hover:bg-cyan-950/40 border border-cyan-500/15 hover:border-cyan-400/50 text-xs text-slate-300 hover:text-cyan-200 transition-all flex items-center justify-between group shadow-sm"
                >
                  <span className="truncate mr-2 font-sans">{sq}</span>
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
            {/* Message Sender & Timestamp Header */}
            <div className="flex items-center gap-1.5 text-[10px] text-slate-500 mb-1 font-mono">
              {msg.sender === 'user' ? (
                <>
                  <span className="text-slate-400 font-semibold">You</span>
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

            {/* Message Bubble Container */}
            <div
              className={`p-3.5 rounded-2xl max-w-[94%] text-xs leading-relaxed shadow-lg ${
                msg.sender === 'user'
                  ? 'bg-gradient-to-r from-blue-600 to-cyan-600 text-white rounded-tr-none'
                  : 'bg-[#081026] border border-cyan-500/25 text-slate-200 rounded-tl-none font-sans'
              }`}
            >
              {msg.sender === 'user' ? (
                <p className="whitespace-pre-wrap">{msg.text}</p>
              ) : (
                <FormattedMessage content={msg.text} />
              )}

              {/* Expandable Evidence & Citations Tray if available */}
              {msg.investigationData && (
                <div className="mt-3 pt-2.5 border-t border-cyan-500/20">
                  <button
                    onClick={() => setExpandedEvidenceId(expandedEvidenceId === msg.id ? null : msg.id)}
                    className="flex items-center justify-between w-full px-2.5 py-1.5 rounded-md bg-[#040816] hover:bg-cyan-950/30 border border-cyan-500/20 text-[10px] font-mono text-cyan-300 transition-colors"
                  >
                    <span className="flex items-center gap-1.5">
                      <BookOpen className="w-3 h-3 text-cyan-400" />
                      <span>Evaluated Causal Evidence & Telemetry</span>
                    </span>
                    {expandedEvidenceId === msg.id ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                  </button>

                  {expandedEvidenceId === msg.id && (
                    <div className="mt-2 p-2.5 rounded-lg bg-[#030612] border border-cyan-500/20 space-y-2">
                      <div className="text-[10px] text-slate-400">
                        <strong className="text-cyan-300">Target Symptom:</strong> {msg.investigationData.symptom_key}
                      </div>
                      {msg.investigationData.hypotheses_ranked && (
                        <div className="space-y-1">
                          {msg.investigationData.hypotheses_ranked.map((h: any, idx: number) => (
                            <div key={idx} className="p-1.5 rounded bg-slate-900/60 border border-slate-800 text-[10px]">
                              <div className="flex items-center justify-between text-white font-semibold">
                                <span>{h.cause_name}</span>
                                <span className="px-1 py-0.2 rounded bg-cyan-500/20 text-cyan-300 text-[9px] font-mono">
                                  {h.support_tier}
                                </span>
                              </div>
                              <p className="text-slate-400 text-[9px] mt-0.5">{h.mechanistic_summary}</p>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}

              {/* Slot Clarification Interactive Buttons */}
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
                          className="px-2.5 py-1 rounded-md bg-amber-500/20 hover:bg-amber-500/40 border border-amber-500/40 text-amber-200 text-[11px] transition-colors flex items-center gap-1 shadow-sm"
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

        {/* Live Investigation Loading State */}
        {isInvestigating && (
          <div className="flex items-start gap-2.5 text-xs text-cyan-400 bg-[#070e24]/90 p-3 rounded-xl border border-cyan-500/30 shadow-lg">
            <Loader2 className="w-4 h-4 animate-spin text-cyan-400 shrink-0 mt-0.5" />
            <div className="space-y-0.5 flex-1">
              <span className="font-semibold font-mono text-cyan-300 flex items-center gap-1.5">
                <span>Executing Strands Tools</span>
                <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-ping"></span>
              </span>
              <p className="text-[11px] text-slate-400 leading-tight">
                Evaluating multi-source scientific literature, satellite bi-temporal indices, and spatial IDW telemetry.
              </p>
            </div>
            {onStopGeneration && (
              <button
                onClick={onStopGeneration}
                title="Stop generation"
                className="px-2 py-1 rounded bg-rose-500/20 hover:bg-rose-500/30 border border-rose-500/40 text-rose-300 text-[10px] font-mono flex items-center gap-1 transition-colors"
              >
                <Square className="w-2.5 h-2.5 fill-current" />
                <span>Stop</span>
              </button>
            )}
          </div>
        )}

        {/* Dynamic Follow-up Suggestions after Assistant Response */}
        {!isInvestigating && lastMessage && lastMessage.sender === 'agent' && (
          <div className="pt-2 space-y-1.5">
            <div className="text-[10px] uppercase font-mono tracking-wider text-slate-500 px-1">
              Recommended Follow-ups:
            </div>
            <div className="flex flex-wrap gap-1.5">
              <button
                onClick={() => handleSuggestionClick("Why are these changes happening?")}
                className="px-2.5 py-1 rounded-lg bg-[#070e24] hover:bg-cyan-950/50 border border-cyan-500/20 hover:border-cyan-400/50 text-[11px] text-cyan-300 transition-colors shadow-sm"
              >
                🔍 Why are these changes happening?
              </button>
              <button
                onClick={() => handleSuggestionClick("Show me scientific research supporting this.")}
                className="px-2.5 py-1 rounded-lg bg-[#070e24] hover:bg-cyan-950/50 border border-cyan-500/20 hover:border-cyan-400/50 text-[11px] text-cyan-300 transition-colors shadow-sm"
              >
                📚 Show me scientific research
              </button>
              <button
                onClick={() => handleSuggestionClick("What are the likely environmental effects over the next five years?")}
                className="px-2.5 py-1 rounded-lg bg-[#070e24] hover:bg-cyan-950/50 border border-cyan-500/20 hover:border-cyan-400/50 text-[11px] text-cyan-300 transition-colors shadow-sm"
              >
                📈 What will happen in five years?
              </button>
              <button
                onClick={() => handleSuggestionClick("Explain your findings in simple language.")}
                className="px-2.5 py-1 rounded-lg bg-[#070e24] hover:bg-cyan-950/50 border border-cyan-500/20 hover:border-cyan-400/50 text-[11px] text-cyan-300 transition-colors shadow-sm"
              >
                💡 Explain in simple language
              </button>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* 3. Message Input Composer Form */}
      <form onSubmit={handleSubmit} className="p-3 border-t border-cyan-500/20 bg-[#030612]/95">
        <div className="relative flex items-center">
          <input
            type="text"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            placeholder={isInvestigating ? "Investigating..." : "Ask any environmental question (e.g. vegetation loss, fish deaths)..."}
            disabled={isInvestigating}
            className="w-full pl-3.5 pr-12 py-2.5 bg-[#070e24] border border-cyan-500/25 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-400 focus:ring-1 focus:ring-cyan-400/50 disabled:opacity-50 transition-all font-sans"
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
