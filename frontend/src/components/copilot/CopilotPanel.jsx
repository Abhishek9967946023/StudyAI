/**
 * =============================================================================
 * StudyAI — Floating AI Study Copilot
 * =============================================================================
 * Answers questions strictly grounded in the uploaded material.
 * Includes source attribution chips (section and page) and supporting excerpts.
 * Quick actions: "Explain simply", "Quiz me on this".
 * =============================================================================
 */

import React, { useState, useRef, useEffect } from 'react';
import { 
  Sparkles, 
  X, 
  Send, 
  BookOpen, 
  HelpCircle, 
  Lightbulb, 
  ExternalLink 
} from 'lucide-react';
import { askCopilot } from '../../services/copilotService';
import { Chip } from '../ui/Chip';

export function CopilotPanel({ isOpen, onClose, materialId }) {
  const [messages, setMessages] = useState([
    {
      id: 'msg-0',
      sender: 'assistant',
      text: 'Hello! I am your Study Copilot. Ask me anything about your uploaded study material. I will cite exact sections and pages.',
      sources: []
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async (textToSend = null) => {
    const q = textToSend || input;
    if (!q.trim() || loading) return;

    const userMsg = { id: `msg-${Date.now()}`, sender: 'user', text: q, sources: [] };
    setMessages(prev => [...prev, userMsg]);
    if (!textToSend) setInput('');
    setLoading(true);

    try {
      const response = await askCopilot(q, materialId);
      const botMsg = {
        id: `msg-bot-${Date.now()}`,
        sender: 'assistant',
        text: response.answer,
        sources: response.sources || []
      };
      setMessages(prev => [...prev, botMsg]);
    } catch {
      setMessages(prev => [...prev, {
        id: `msg-err-${Date.now()}`,
        sender: 'assistant',
        text: 'I could not find reference to that in the uploaded material. StudyAI only responds with verified content from your study text.',
        sources: []
      }]);
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div 
      className="sa-card sa-copilot-panel fade-in"
      style={{
        position: 'fixed',
        bottom: '84px',
        right: '24px',
        width: '380px',
        maxWidth: 'calc(100vw - 32px)',
        height: '520px',
        zIndex: 1000,
        boxShadow: 'var(--shadow-lg)',
        display: 'flex',
        flexDirection: 'column',
        padding: '0',
        overflow: 'hidden',
        border: '1px solid var(--border)'
      }}
    >
      {/* Header */}
      <div style={{
        padding: '14px 18px',
        backgroundColor: 'var(--surface)',
        borderBottom: '1px solid var(--border)',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div style={{
            width: '28px',
            height: '28px',
            borderRadius: '8px',
            backgroundColor: 'var(--indigo-tint)',
            color: 'var(--indigo)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            <Sparkles size={16} />
          </div>
          <div>
            <h4 style={{ fontSize: '0.95rem', fontWeight: 700, margin: 0 }}>Study Copilot</h4>
            <span style={{ fontSize: '0.68rem', color: 'var(--muted)' }}>Grounded in Uploaded Material</span>
          </div>
        </div>

        <button 
          onClick={onClose} 
          style={{ background: 'transparent', border: 'none', cursor: 'pointer', color: 'var(--muted)' }}
          aria-label="Close Study Copilot"
        >
          <X size={18} />
        </button>
      </div>

      {/* Chat Messages */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '16px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
        {messages.map(m => (
          <div 
            key={m.id}
            style={{
              alignSelf: m.sender === 'user' ? 'flex-end' : 'flex-start',
              maxWidth: '85%',
              backgroundColor: m.sender === 'user' ? 'var(--indigo)' : 'var(--bg)',
              color: m.sender === 'user' ? '#FFFFFF' : 'var(--ink)',
              padding: '10px 14px',
              borderRadius: '14px',
              fontSize: '0.85rem',
              lineHeight: '1.45'
            }}
          >
            <div>{m.text}</div>

            {/* Source Citations Chips */}
            {m.sources && m.sources.length > 0 && (
              <div style={{ marginTop: '8px', paddingTop: '6px', borderTop: '1px solid rgba(0,0,0,0.06)' }}>
                {m.sources.map((src, sIdx) => (
                  <div key={sIdx} style={{ marginTop: '4px' }}>
                    <Chip variant="teal" icon={<BookOpen size={11} />} style={{ fontSize: '0.65rem', marginBottom: '4px' }}>
                      {src.section} (p. {src.page})
                    </Chip>
                    <div style={{ fontSize: '0.72rem', color: 'var(--muted)', fontStyle: 'italic', paddingLeft: '4px' }}>
                      "{src.excerpt}"
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}
        {loading && (
          <div style={{ alignSelf: 'flex-start', fontSize: '0.75rem', color: 'var(--muted)', fontStyle: 'italic' }}>
            Consulting material text...
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Quick Actions */}
      <div style={{ padding: '8px 14px', borderTop: '1px solid var(--border)', display: 'flex', gap: '6px', overflowX: 'auto' }}>
        <button
          type="button"
          onClick={() => handleSend('Explain the core concepts simply.')}
          style={{
            fontSize: '0.72rem',
            padding: '4px 10px',
            borderRadius: 'var(--radius-pill)',
            border: '1px solid var(--border)',
            backgroundColor: 'var(--surface)',
            color: 'var(--ink)',
            cursor: 'pointer',
            whiteSpace: 'nowrap'
          }}
        >
          💡 Explain simply
        </button>
        <button
          type="button"
          onClick={() => handleSend('Quiz me on key principles.')}
          style={{
            fontSize: '0.72rem',
            padding: '4px 10px',
            borderRadius: 'var(--radius-pill)',
            border: '1px solid var(--border)',
            backgroundColor: 'var(--surface)',
            color: 'var(--ink)',
            cursor: 'pointer',
            whiteSpace: 'nowrap'
          }}
        >
          ❓ Quiz me on this
        </button>
      </div>

      {/* Input Field */}
      <div style={{ padding: '12px 14px', borderTop: '1px solid var(--border)', display: 'flex', gap: '8px' }}>
        <input
          type="text"
          placeholder="Ask a question on this material..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSend()}
          style={{
            flex: 1,
            padding: '8px 12px',
            borderRadius: 'var(--radius-btn)',
            border: '1px solid var(--border)',
            backgroundColor: 'var(--bg)',
            color: 'var(--ink)',
            fontSize: '0.85rem',
            outline: 'none'
          }}
        />
        <button
          type="button"
          onClick={() => handleSend()}
          disabled={!input.trim() || loading}
          style={{
            width: '36px',
            height: '36px',
            borderRadius: 'var(--radius-btn)',
            backgroundColor: 'var(--indigo)',
            color: '#FFFFFF',
            border: 'none',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            cursor: 'pointer'
          }}
          aria-label="Send query"
        >
          <Send size={15} />
        </button>
      </div>
    </div>
  );
}

export function CopilotFab({ onClick, isOpen }) {
  return (
    <button
      type="button"
      onClick={onClick}
      style={{
        position: 'fixed',
        bottom: '24px',
        right: '24px',
        width: '52px',
        height: '52px',
        borderRadius: '50%',
        backgroundColor: 'var(--indigo)',
        color: '#FFFFFF',
        border: 'none',
        boxShadow: 'var(--shadow-lg), 0 0 20px rgba(79, 63, 240, 0.4)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        cursor: 'pointer',
        zIndex: 900,
        transition: 'transform 0.2s cubic-bezier(0.16, 1, 0.3, 1)'
      }}
      aria-label="Open AI Study Copilot"
    >
      <Sparkles size={22} />
    </button>
  );
}
