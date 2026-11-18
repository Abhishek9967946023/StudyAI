import React, { useEffect, useRef, useState } from 'react';
import { Copy, Check, Maximize2, Minimize2, Eye, GitBranch } from 'lucide-react';

export function MermaidDiagram({ code, chart, title, type = 'flowchart', grounding = '' }) {
  const containerRef = useRef(null);
  const [svgHtml, setSvgHtml] = useState('');
  const [error, setError] = useState(false);
  const [copied, setCopied] = useState(false);
  const [expanded, setExpanded] = useState(false);

  const activeCode = (code || chart || '').trim();

  useEffect(() => {
    let isMounted = true;
    if (!activeCode) return;

    const renderDiagram = async () => {
      try {
        setError(false);
        const { default: mermaid } = await import('mermaid');
        mermaid.initialize({
          startOnLoad: false,
          theme: 'neutral',
          securityLevel: 'strict',
          fontFamily: 'Inter, system-ui, -apple-system, sans-serif',
          flowchart: {
            useMaxWidth: true,
            htmlLabels: true,
            curve: 'basis'
          }
        });
        const uniqueId = `mermaid-${Math.random().toString(36).substring(2, 9)}`;
        const { svg } = await mermaid.render(uniqueId, activeCode);
        if (isMounted) {
          setSvgHtml(svg);
        }
      } catch (err) {
        console.warn('Mermaid rendering fallback activated:', err);
        if (isMounted) {
          setError(true);
        }
      }
    };

    renderDiagram();

    return () => {
      isMounted = false;
    };
  }, [activeCode]);

  const handleCopy = () => {
    if (!activeCode) return;
    navigator.clipboard.writeText(activeCode);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div 
      style={{
        margin: '18px 0',
        borderRadius: '12px',
        border: '1px solid var(--border)',
        backgroundColor: 'var(--surface)',
        overflow: 'hidden',
        boxShadow: expanded ? '0 12px 30px rgba(0,0,0,0.12)' : '0 1px 4px rgba(0,0,0,0.04)',
        transition: 'all 0.25s ease'
      }}
    >
      {/* Header bar */}
      <div 
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          padding: '10px 16px',
          borderBottom: '1px solid var(--border)',
          backgroundColor: 'rgba(99, 102, 241, 0.04)',
          flexWrap: 'wrap',
          gap: '8px'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <GitBranch size={16} color="var(--indigo)" />
          <strong style={{ fontSize: '0.875rem', color: 'var(--ink)' }}>
            {title || 'Visual Model & Architecture'}
          </strong>
          {type && (
            <span 
              style={{
                fontSize: '0.72rem',
                fontWeight: 600,
                textTransform: 'uppercase',
                padding: '2px 8px',
                borderRadius: '6px',
                backgroundColor: 'var(--indigo-tint)',
                color: 'var(--indigo-text)'
              }}
            >
              {type}
            </span>
          )}
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <button
            onClick={handleCopy}
            title="Copy Mermaid syntax"
            style={{
              background: 'none',
              border: '1px solid var(--border)',
              borderRadius: '6px',
              padding: '4px 8px',
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
              fontSize: '0.75rem',
              color: 'var(--ink)',
              cursor: 'pointer',
              backgroundColor: 'var(--bg)'
            }}
          >
            {copied ? <Check size={12} color="var(--teal)" /> : <Copy size={12} />}
            {copied ? 'Copied' : 'Copy Code'}
          </button>

          <button
            onClick={() => setExpanded(prev => !prev)}
            title={expanded ? 'Compress View' : 'Expand View'}
            style={{
              background: 'none',
              border: '1px solid var(--border)',
              borderRadius: '6px',
              padding: '4px 8px',
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
              fontSize: '0.75rem',
              color: 'var(--ink)',
              cursor: 'pointer',
              backgroundColor: 'var(--bg)'
            }}
          >
            {expanded ? <Minimize2 size={12} /> : <Maximize2 size={12} />}
            {expanded ? 'Collapse' : 'Expand'}
          </button>
        </div>
      </div>

      {/* Render Canvas */}
      <div 
        ref={containerRef}
        style={{
          padding: expanded ? '32px 24px' : '20px 16px',
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          overflowX: 'auto',
          backgroundColor: '#ffffff',
          minHeight: '140px'
        }}
      >
        {!error && svgHtml ? (
          <div 
            dangerouslySetInnerHTML={{ __html: svgHtml }} 
            style={{
              maxWidth: '100%',
              display: 'flex',
              justifyContent: 'center'
            }}
          />
        ) : error ? (
          <div style={{ width: '100%', padding: '12px' }}>
            <div style={{ color: 'var(--muted)', fontSize: '0.8rem', marginBottom: '8px' }}>
              Structured Visual Workflow (Text Mode):
            </div>
            <pre 
              style={{
                fontFamily: 'var(--font-mono)',
                fontSize: '0.825rem',
                backgroundColor: 'var(--bg)',
                padding: '12px',
                borderRadius: '8px',
                color: 'var(--ink)',
                overflowX: 'auto'
              }}
            >
              {activeCode}
            </pre>
          </div>
        ) : (
          <div style={{ color: 'var(--muted)', fontSize: '0.85rem' }}>
            Synthesizing visual explanation...
          </div>
        )}
      </div>

      {/* Grounding footnote */}
      {grounding && (
        <div 
          style={{
            padding: '6px 16px',
            borderTop: '1px solid var(--border)',
            backgroundColor: 'var(--surface)',
            fontSize: '0.75rem',
            color: 'var(--muted)',
            display: 'flex',
            alignItems: 'center',
            gap: '6px'
          }}
        >
          <Eye size={12} color="var(--indigo)" />
          <span>{grounding}</span>
        </div>
      )}
    </div>
  );
}
