/**
=============================================================================
StudyAI — High-Fidelity Pedagogical Markdown & Math Engine
=============================================================================
Features:
- KaTeX LaTeX math equation rendering ($...$ inline, $$...$$ display)
- Mermaid dynamic interactive diagram embedding (```mermaid ... ```)
- Anchor-linked headings (#, ##, ###) for Table of Contents navigation
- Glassmorphic comparison tables with alternating row glow
- Semantic callouts (Definitions, Theorems, Important Traps, Exam Tips)
- Code blocks with one-click clipboard copy
- Clean typographic scale with comfortable line height and paragraph rhythm
=============================================================================
*/

import React, { useState, useMemo } from 'react';
import katex from 'katex';
import { 
  Copy, 
  Check, 
  Bookmark, 
  ShieldCheck, 
  AlertTriangle, 
  Lightbulb, 
  Info,
  ChevronRight,
  ExternalLink
} from 'lucide-react';
import { MermaidDiagram } from './MermaidDiagram';

// Utility to normalize Unicode mathematical symbols to standard LaTeX before KaTeX
function normalizeLatex(str) {
  if (!str) return '';
  let s = str.trim();

  // Normalize align to aligned for universal KaTeX compatibility
  s = s.replace(/\\begin\{align\*?\}/g, '\\begin{aligned}');
  s = s.replace(/\\end\{align\*?\}/g, '\\end{aligned}');

  // Unescape excessive backslashes if present
  s = s.replace(/\\\\([a-zA-Z]+)/g, '\\$1');

  const symbolMap = [
    [/∅/g, '\\emptyset '],
    [/ε/g, '\\epsilon '],
    [/∪/g, '\\cup '],
    [/∩/g, '\\cap '],
    [/⊆/g, '\\subseteq '],
    [/∈/g, '\\in '],
    [/∉/g, '\\notin '],
    [/→/g, '\\to '],
    [/←/g, '\\leftarrow '],
    [/⇒/g, '\\implies '],
    [/⇔/g, '\\iff '],
    [/≤/g, '\\le '],
    [/≥/g, '\\ge '],
    [/≠/g, '\\ne '],
    [/≈/g, '\\approx '],
    [/⋯/g, '\\cdots '],
    [/…/g, '\\dots '],
    [/×/g, '\\times '],
    [/∑/g, '\\sum '],
    [/∏/g, '\\prod '],
    [/∞/g, '\\infty '],
    [/Σ/g, '\\Sigma '],
    [/α/g, '\\alpha '],
    [/β/g, '\\beta '],
    [/γ/g, '\\gamma '],
    [/δ/g, '\\delta '],
    [/λ/g, '\\lambda ']
  ];

  for (const [re, rep] of symbolMap) {
    s = s.replace(re, rep);
  }

  // Ensure Kleene star exponents like R* or L* inside math mode are formatted as R^* or L^* (without double exponentiating)
  s = s.replace(/([a-zA-Z0-9\)])(?<!\^)\*/g, '$1^{*}');

  return s;
}

// Utility to render inline/display LaTeX math and bold/italic/code spans
function renderInlineContent(text) {
  if (!text) return null;

  // Split on display math ($$...$$, \[...\]) and inline math ($...$, \(...\))
  const mathRegex = /(?<!\\)\$\$([^\$]+?)\$\$|\\\[([\s\S]+?)\\\]|(?<!\\)\$([^\$]+?)\$|\\\(([\s\S]+?)\\\)/;
  const parts = [];
  let remaining = text;
  let keyIdx = 0;

  while (remaining.length > 0) {
    const mathMatch = remaining.match(mathRegex);
    if (!mathMatch) {
      // Process remaining non-math text for bold, italics, code, etc.
      parts.push(renderFormattedSpans(remaining, keyIdx++));
      break;
    }

    const startIdx = mathMatch.index;
    if (startIdx > 0) {
      const before = remaining.substring(0, startIdx);
      parts.push(renderFormattedSpans(before, keyIdx++));
    }

    const isDisplay = Boolean(mathMatch[1] || mathMatch[2]);
    const mathCode = mathMatch[1] || mathMatch[2] || mathMatch[3] || mathMatch[4];
    
    let renderedHtml = '';
    try {
      renderedHtml = katex.renderToString(normalizeLatex(mathCode), {
        displayMode: isDisplay,
        throwOnError: false
      });
    } catch (e) {
      renderedHtml = `<span class="katex-error">${mathCode}</span>`;
    }

    if (isDisplay) {
      parts.push(
        <span 
          key={`math-disp-${keyIdx++}`} 
          className="block my-3 py-1 overflow-x-auto text-center text-slate-900 dark:text-slate-100"
          dangerouslySetInnerHTML={{ __html: renderedHtml }} 
        />
      );
    } else {
      parts.push(
        <span 
          key={`math-inl-${keyIdx++}`} 
          className="inline-math text-indigo-600 dark:text-indigo-300 font-medium px-0.5"
          dangerouslySetInnerHTML={{ __html: renderedHtml }} 
        />
      );
    }

    remaining = remaining.substring(startIdx + mathMatch[0].length);
  }

  return parts;
}

// Utility to render bold, italic, code spans inside text
function renderFormattedSpans(text, baseKey) {
  if (!text) return null;

  // Replace source page citations *(Source: ...)* with subtle inline text
  const sourceMatch = text.match(/\*\((Source:[^\)]+)\)\*/i);
  if (sourceMatch) {
    const parts = text.split(sourceMatch[0]);
    return (
      <span key={`span-${baseKey}`}>
        {renderFormattedSpans(parts[0], `${baseKey}-0`)}
        <span className="text-xs text-slate-500 dark:text-slate-400 italic mx-1">
          ({sourceMatch[1]})
        </span>
        {renderFormattedSpans(parts[1], `${baseKey}-1`)}
      </span>
    );
  }

  // Handle inline `code`
  const codeRegex = /`([^`]+)`/g;
  const segments = [];
  let lastIndex = 0;
  let match;

  while ((match = codeRegex.exec(text)) !== null) {
    if (match.index > lastIndex) {
      segments.push(parseBoldItalics(text.substring(lastIndex, match.index), `${baseKey}-${lastIndex}`));
    }
    segments.push(
      <code 
        key={`${baseKey}-code-${match.index}`}
        className="px-1.5 py-0.5 rounded bg-slate-100 dark:bg-slate-800/80 border border-slate-300 dark:border-slate-700/60 font-mono text-xs text-indigo-700 dark:text-cyan-300"
      >
        {match[1]}
      </code>
    );
    lastIndex = match.index + match[0].length;
  }

  if (lastIndex < text.length) {
    segments.push(parseBoldItalics(text.substring(lastIndex), `${baseKey}-${lastIndex}`));
  }

  return <span key={`formatted-${baseKey}`}>{segments}</span>;
}

function parseBoldItalics(text, key) {
  // Simple bold **text** and italic *text*
  const parts = [];
  let rem = text;
  let k = 0;

  while (rem.length > 0) {
    const boldMatch = rem.match(/\*\*([^\*]+?)\*\*/);
    if (!boldMatch) {
      // Check for italics *text*
      const italicMatch = rem.match(/(?<!\*)\*([^\*]+?)\*(?!\*)/);
      if (!italicMatch) {
        parts.push(rem);
        break;
      }
      if (italicMatch.index > 0) {
        parts.push(rem.substring(0, italicMatch.index));
      }
      parts.push(<em key={`em-${key}-${k++}`} className="italic text-slate-700 dark:text-slate-300">{italicMatch[1]}</em>);
      rem = rem.substring(italicMatch.index + italicMatch[0].length);
      continue;
    }

    if (boldMatch.index > 0) {
      parts.push(rem.substring(0, boldMatch.index));
    }
    parts.push(<strong key={`b-${key}-${k++}`} className="font-bold text-slate-900 dark:text-white">{boldMatch[1]}</strong>);
    rem = rem.substring(boldMatch.index + boldMatch[0].length);
  }

  return <span key={key}>{parts}</span>;
}

// Code block with copy button
function CodeBlock({ language, code }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="relative group my-4 rounded-xl overflow-hidden border border-slate-800 bg-slate-950/90 shadow-lg">
      <div className="flex items-center justify-between px-4 py-2 border-b border-slate-800 bg-slate-900/60 text-xs font-mono text-slate-400">
        <span className="uppercase tracking-wider">{language || 'text'}</span>
        <button
          onClick={handleCopy}
          className="flex items-center gap-1.5 px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors"
        >
          {copied ? <Check size={13} className="text-emerald-400" /> : <Copy size={13} />}
          <span>{copied ? 'Copied' : 'Copy'}</span>
        </button>
      </div>
      <pre className="p-4 overflow-x-auto font-mono text-sm text-cyan-200/90 leading-relaxed">
        <code>{code}</code>
      </pre>
    </div>
  );
}

// Natural Markdown Blockquote / Academic Callout Component (Phase 5 Visual Design System)
function CalloutBlock({ lines }) {
  const fullText = lines.map(l => l.replace(/^>\s*/, '')).join(' ').trim();
  
  // Detect Phase 5 academic callout type
  let calloutType = 'NOTE';
  let badgeLabel = '';
  let borderClass = 'border-indigo-500 bg-indigo-50/40 dark:bg-indigo-950/20 text-slate-700 dark:text-slate-300';
  let badgeClass = 'text-indigo-600 dark:text-indigo-400 bg-indigo-100/60 dark:bg-indigo-900/40';

  if (/^(?:\[!NOTE\]|\*\*Definition:?\*\*|Definition:)/i.test(fullText)) {
    calloutType = 'DEFINITION';
    badgeLabel = 'Definition';
    borderClass = 'border-indigo-500 bg-indigo-50/50 dark:bg-indigo-950/20 text-indigo-950 dark:text-indigo-100';
    badgeClass = 'text-indigo-700 dark:text-indigo-300 bg-indigo-100 dark:bg-indigo-900/50 border-indigo-200 dark:border-indigo-800';
  } else if (/^(?:\[!EXAMPLE\]|\*\*Example:?\*\*|Example:)/i.test(fullText)) {
    calloutType = 'EXAMPLE';
    badgeLabel = 'Example';
    borderClass = 'border-slate-400 bg-slate-50 dark:bg-slate-900/40 text-slate-800 dark:text-slate-200';
    badgeClass = 'text-slate-700 dark:text-slate-300 bg-slate-100 dark:bg-slate-800 border-slate-200 dark:border-slate-700';
  } else if (/^(?:\[!IMPORTANT\]|\*\*Important:?\*\*|Important:|\*\*Key Takeaway:?\*\*)/i.test(fullText)) {
    calloutType = 'IMPORTANT';
    badgeLabel = 'Important';
    borderClass = 'border-amber-500 bg-amber-50/50 dark:bg-amber-950/20 text-amber-950 dark:text-amber-100';
    badgeClass = 'text-amber-700 dark:text-amber-300 bg-amber-100 dark:bg-amber-900/50 border-amber-200 dark:border-amber-800';
  } else if (/^(?:\[!FORMULA\]|\*\*Formula:?\*\*|Formula:)/i.test(fullText)) {
    calloutType = 'FORMULA';
    badgeLabel = 'Formula';
    borderClass = 'border-purple-500 bg-purple-50/50 dark:bg-purple-950/20 text-purple-950 dark:text-purple-100';
    badgeClass = 'text-purple-700 dark:text-purple-300 bg-purple-100 dark:bg-purple-900/50 border-purple-200 dark:border-purple-800';
  } else if (/^(?:\[!TIP\]|\*\*Exam Tip:?\*\*|Exam Tip:|\*\*Tip:?\*\*)/i.test(fullText)) {
    calloutType = 'EXAM_TIP';
    badgeLabel = 'Exam Tip';
    borderClass = 'border-emerald-500 bg-emerald-50/50 dark:bg-emerald-950/20 text-emerald-950 dark:text-emerald-100';
    badgeClass = 'text-emerald-700 dark:text-emerald-300 bg-emerald-100 dark:bg-emerald-900/50 border-emerald-200 dark:border-emerald-800';
  }

  return (
    <blockquote className={`my-4 pl-4 border-l-4 py-3 pr-4 rounded-r-xl ${borderClass} text-sm sm:text-base leading-relaxed space-y-1.5 shadow-sm`}>
      {badgeLabel && (
        <div className="mb-1.5">
          <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold uppercase tracking-wider border ${badgeClass}`}>
            {badgeLabel}
          </span>
        </div>
      )}
      {lines.map((line, idx) => {
        let cleanLine = line.replace(/^>\s*/, '');
        if (idx === 0 && badgeLabel) {
          cleanLine = cleanLine.replace(/^(?:\[!(?:NOTE|EXAMPLE|IMPORTANT|FORMULA|TIP)\]|\*\*(?:Definition|Example|Important|Formula|Exam Tip|Key Takeaway):?\*\*|(?:Definition|Example|Important|Formula|Exam Tip):)\s*/i, '');
        }
        if (!cleanLine.trim()) return null;
        return (
          <p key={idx} className="my-1">
            {renderInlineContent(cleanLine)}
          </p>
        );
      })}
    </blockquote>
  );
}

// Table Component with Phase 5 Column Alignment & Overflow Prevention
function MarkdownTable({ lines }) {
  if (lines.length < 2) return null;

  const headerLine = lines[0];
  const headers = headerLine
    .split('|')
    .map(h => h.trim())
    .filter(Boolean);

  // Filter out divider line (|---|---|)
  const bodyLines = lines.slice(2);
  const rows = bodyLines.map(rowLine => {
    return rowLine
      .split('|')
      .map(cell => cell.trim())
      .filter((_, idx, arr) => idx > 0 && idx < arr.length - 1 || arr.length === headers.length);
  });

  return (
    <div className="my-5 overflow-x-auto rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/40 shadow-sm">
      <table className="w-full text-left text-sm text-slate-800 dark:text-slate-200">
        <thead className="bg-slate-900 text-white dark:bg-slate-900/90 border-b border-slate-700 text-xs uppercase tracking-wider font-semibold">
          <tr>
            {headers.map((h, i) => (
              <th key={i} className="px-4 py-3 text-left">
                {renderInlineContent(h)}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100 dark:divide-slate-800/60">
          {rows.map((row, rIdx) => (
            <tr key={rIdx} className={`${rIdx % 2 === 1 ? 'bg-slate-50/60 dark:bg-slate-800/20' : 'bg-transparent'} hover:bg-slate-100/60 dark:hover:bg-slate-800/40 transition-colors`}>
              {row.map((cell, cIdx) => {
                const isNumeric = /^\s*[\$€£]?\s*-?\d+(?:\.\d+)?%?\s*$/.test(cell);
                const isShort = cell.trim().length <= 4;
                const alignClass = isNumeric ? 'text-right' : (isShort ? 'text-center' : 'text-left');
                return (
                  <td key={cIdx} className={`px-4 py-2.5 leading-relaxed ${alignClass}`}>
                    {renderInlineContent(cell)}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function isShortFragment(str) {
  if (!str) return false;
  const t = str.trim();
  if (t.length === 1) return true;
  // Common 2-4 character tokens that appear when formulas or text are vertically stacked
  if (/^(\.{2,4}|…|⋯|->|=>|<=|>=|!=|==|\b[a-zA-Z]\d\b|[a-zA-Z]\*)$/.test(t)) return true;
  return false;
}

function destackVerticalLines(lines) {
  const result = [];
  let i = 0;
  const n = lines.length;

  while (i < n) {
    if (isShortFragment(lines[i])) {
      const run = [];
      let j = i;
      while (j < n) {
        if (isShortFragment(lines[j])) {
          run.push(lines[j].trim());
          j++;
        } else if (lines[j].trim() === '') {
          if (j + 1 < n && isShortFragment(lines[j + 1])) {
            run.push(' ');
            j++;
          } else {
            break;
          }
        } else {
          break;
        }
      }

      const realChars = run.filter(c => c !== ' ');
      if (realChars.length >= 3) {
        let joined = run.join('').replace(/\s+/g, ' ').trim();
        if (joined.includes('=')) {
          joined = joined.replace(/\s*=\s*/g, ' = ');
        }
        result.push(joined);
        i = j;
        continue;
      }
    }
    result.push(lines[i]);
    i++;
  }
  return result;
}

function parseMarkdownContent(content) {
  if (!content) return [];

  // Split lines into structured blocks and destack any vertical runs
  const rawLines = content.split(/\r?\n/);
  const lines = destackVerticalLines(rawLines);
  const elements = [];
  let i = 0;

  while (i < lines.length) {
    const line = lines[i];
    const trimmed = line.trim();

    // 1. Empty lines
    if (!trimmed) {
      i++;
      continue;
    }

    // 2. Multiline LaTeX display equations ($$ ... $$, \[ ... \], \begin{...})
    if (
      trimmed.startsWith('$$') || 
      trimmed.startsWith('\\[') || 
      trimmed.startsWith('\\begin{')
    ) {
      let mathCode = '';

      if (trimmed.startsWith('$$')) {
        // Single line display equation ($$...$$)
        if (trimmed.endsWith('$$') && trimmed.length > 4) {
          mathCode = trimmed.substring(2, trimmed.length - 2);
          i++;
        } else {
          i++;
          const mathLines = [];
          let searchDepth = 0;
          while (i < lines.length && searchDepth < 45) {
            const cur = lines[i].trim();
            searchDepth++;
            if (cur.endsWith('$$') || cur === '$$') {
              const content = cur.replace(/\$\$$/, '');
              if (content) mathLines.push(content);
              i++;
              break;
            }
            mathLines.push(lines[i]);
            i++;
          }
          mathCode = mathLines.join('\n');
        }
      } else if (trimmed.startsWith('\\[')) {
        // Single line \[ ... \]
        if (trimmed.endsWith('\\]') && trimmed.length > 4) {
          mathCode = trimmed.substring(2, trimmed.length - 2);
          i++;
        } else {
          i++;
          const mathLines = [];
          let searchDepth = 0;
          while (i < lines.length && searchDepth < 45) {
            const cur = lines[i].trim();
            searchDepth++;
            if (cur.endsWith('\\]') || cur === '\\]') {
              const content = cur.replace(/\\\]$/, '');
              if (content) mathLines.push(content);
              i++;
              break;
            }
            mathLines.push(lines[i]);
            i++;
          }
          mathCode = mathLines.join('\n');
        }
      } else {
        // \begin{any_environment} e.g. aligned, equation, bmatrix, pmatrix, cases
        const envMatch = trimmed.match(/^\\begin\{([a-zA-Z*]+)\}/);
        const envName = envMatch ? envMatch[1] : 'equation';
        const endTag = `\\end{${envName}}`;
        const mathLines = [trimmed];
        i++;
        let searchDepth = 0;
        while (i < lines.length && searchDepth < 45) {
          const cur = lines[i].trim();
          mathLines.push(lines[i]);
          i++;
          searchDepth++;
          if (cur.includes(endTag)) {
            break;
          }
        }
        mathCode = mathLines.join('\n');
      }

      let renderedHtml = '';
      try {
        renderedHtml = katex.renderToString(normalizeLatex(mathCode.trim()), {
          displayMode: true,
          throwOnError: false
        });
      } catch (err) {
        renderedHtml = `<div class="katex-error text-amber-500 font-mono text-sm py-1">${mathCode}</div>`;
      }

      elements.push(
        <div 
          key={`display-math-${i}`} 
          className="my-5 py-2 overflow-x-auto text-center text-slate-900 dark:text-slate-100"
          dangerouslySetInnerHTML={{ __html: renderedHtml }} 
        />
      );
      continue;
    }

    // 3. Code & Mermaid blocks (``` ... ```)
    if (trimmed.startsWith('```')) {
      const language = trimmed.substring(3).trim().toLowerCase();
      i++;
      const codeLines = [];
      let searchDepth = 0;
      while (i < lines.length && !lines[i].trim().startsWith('```') && searchDepth < 500) {
        codeLines.push(lines[i]);
        i++;
        searchDepth++;
      }
      if (i < lines.length && lines[i].trim().startsWith('```')) {
        i++; // skip closing ```
      }
      const fullCode = codeLines.join('\n');

      if (language === 'mermaid') {
        elements.push(
          <div key={`mermaid-${i}`} className="my-6">
            <MermaidDiagram chart={fullCode} code={fullCode} />
          </div>
        );
      } else {
        elements.push(
          <CodeBlock key={`code-${i}`} language={language} code={fullCode} />
        );
      }
      continue;
    }

    // 4. Blockquotes / Callouts (> ...)
    if (trimmed.startsWith('>')) {
      const quoteLines = [];
      while (i < lines.length && lines[i].trim().startsWith('>')) {
        quoteLines.push(lines[i].trim());
        i++;
      }
      elements.push(<CalloutBlock key={`quote-${i}`} lines={quoteLines} />);
      continue;
    }

    // 5. Tables (| ... |)
    if (trimmed.startsWith('|') && trimmed.endsWith('|')) {
      const tableLines = [];
      while (i < lines.length && lines[i].trim().startsWith('|') && lines[i].trim().endsWith('|')) {
        tableLines.push(lines[i].trim());
        i++;
      }
      elements.push(<MarkdownTable key={`table-${i}`} lines={tableLines} />);
      continue;
    }

    // 6. Horizontal Rules (--- or ***)
    if (/^(\-{3,}|\*{3,})$/.test(trimmed)) {
      elements.push(
        <hr key={`hr-${i}`} className="my-8 border-t border-slate-800/80" />
      );
      i++;
      continue;
    }

    // 7. Headings (must be followed by whitespace, e.g. '# ', '## ')
    const headingMatch = trimmed.match(/^(#{1,6})\s+(.*)$/);
    if (headingMatch) {
      const level = headingMatch[1].length;
      const headingText = headingMatch[2];
      const headingId = headingText
        .toLowerCase()
        .replace(/[^\w\s-]/g, '')
        .replace(/\s+/g, '-');

      if (level === 1) {
        elements.push(
          <h1 
            key={`h1-${i}`} 
            id={headingId} 
            className="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white mt-8 mb-4 tracking-tight border-b border-slate-200 dark:border-slate-800 pb-3"
          >
            {renderInlineContent(headingText)}
          </h1>
        );
      } else if (level === 2) {
        elements.push(
          <h2 
            key={`h2-${i}`} 
            id={headingId} 
            className="text-xl sm:text-2xl font-bold text-slate-900 dark:text-slate-100 mt-8 mb-3 tracking-tight border-b border-slate-200 dark:border-slate-800/40 pb-1"
          >
            {renderInlineContent(headingText)}
          </h2>
        );
      } else if (level === 3) {
        elements.push(
          <h3 
            key={`h3-${i}`} 
            id={headingId} 
            className="text-lg font-semibold text-slate-800 dark:text-slate-200 mt-6 mb-2 tracking-tight"
          >
            {renderInlineContent(headingText)}
          </h3>
        );
      } else {
        elements.push(
          <h4 
            key={`h4-${i}`} 
            id={headingId} 
            className="text-base font-medium text-slate-700 dark:text-slate-300 mt-4 mb-2 tracking-tight"
          >
            {renderInlineContent(headingText)}
          </h4>
        );
      }
      i++;
      continue;
    }

    // 8. Unordered Lists & Checklists (- or * )
    if (/^[-*]\s+/.test(trimmed)) {
      const listItems = [];
      while (i < lines.length && /^[-*]\s+/.test(lines[i].trim())) {
        const itemLine = lines[i].trim().replace(/^[-*]\s+/, '');
        listItems.push(itemLine);
        i++;
      }

      elements.push(
        <ul key={`ul-${i}`} className="my-3 space-y-2 pl-2">
          {listItems.map((item, idx) => {
            const isCheckbox = /^\[([ xX])\]\s+(.*)$/.exec(item);
            if (isCheckbox) {
              const isChecked = isCheckbox[1].toLowerCase() === 'x';
              const checkLabel = isCheckbox[2];
              return (
                <li key={idx} className="flex items-start gap-2.5 text-sm text-slate-800 dark:text-slate-200">
                  <div className={`mt-0.5 w-4 h-4 rounded border flex items-center justify-center shrink-0 ${isChecked ? 'bg-indigo-600 border-indigo-500' : 'bg-slate-100 dark:bg-slate-900 border-slate-300 dark:border-slate-700'}`}>
                    {isChecked && <Check size={12} className="text-white" />}
                  </div>
                  <span>{renderInlineContent(checkLabel)}</span>
                </li>
              );
            }
            return (
              <li key={idx} className="flex items-start gap-2 text-sm text-slate-800 dark:text-slate-200 leading-relaxed">
                <span className="w-1.5 h-1.5 rounded-full bg-indigo-500 dark:bg-indigo-400 mt-2 shrink-0" />
                <span>{renderInlineContent(item)}</span>
              </li>
            );
          })}
        </ul>
      );
      continue;
    }

    // 9. Numbered Lists (1. 2. 3.)
    if (/^\d+\.\s+/.test(trimmed)) {
      const numItems = [];
      while (i < lines.length && /^\d+\.\s+/.test(lines[i].trim())) {
        const itemMatch = lines[i].trim().match(/^(\d+)\.\s+(.*)$/);
        if (itemMatch) {
          numItems.push({ num: itemMatch[1], text: itemMatch[2] });
        }
        i++;
      }

      elements.push(
        <ol key={`ol-${i}`} className="my-4 space-y-2.5 pl-1 list-none">
          {numItems.map((item, idx) => (
            <li key={idx} className="flex items-start gap-3 text-sm text-slate-800 dark:text-slate-200 leading-relaxed">
              <span className="flex items-center justify-center w-5 h-5 rounded-full bg-indigo-50 dark:bg-indigo-950 border border-indigo-300 dark:border-indigo-500/40 text-xs font-mono font-bold text-indigo-700 dark:text-indigo-300 shrink-0 mt-0.5">
                {item.num}
              </span>
              <span>{renderInlineContent(item.text)}</span>
            </li>
          ))}
        </ol>
      );
      continue;
    }

    // 10. Normal Paragraph (Collects regular prose, code lines without backticks like #include, etc.)
    const paraLines = [];
    while (
      i < lines.length && 
      lines[i].trim() && 
      !/^(#{1,6})\s+/.test(lines[i].trim()) &&
      !lines[i].trim().startsWith('```') &&
      !lines[i].trim().startsWith('$$') &&
      !lines[i].trim().startsWith('\\[') &&
      !lines[i].trim().startsWith('\\begin{') &&
      !lines[i].trim().startsWith('>') &&
      !lines[i].trim().startsWith('|') &&
      !/^(\-{3,}|\*{3,})$/.test(lines[i].trim()) &&
      !/^[-*]\s+/.test(lines[i].trim()) &&
      !/^\d+\.\s+/.test(lines[i].trim())
    ) {
      paraLines.push(lines[i].trim());
      i++;
    }

    if (paraLines.length > 0) {
      const fullPara = paraLines.join(' ');
      elements.push(
        <p key={`p-${i}`} className="my-3 text-slate-800 dark:text-slate-200 text-sm sm:text-base leading-relaxed">
          {renderInlineContent(fullPara)}
        </p>
      );
    } else {
      // Safety guarantee: If no handler consumed this line, always advance i to prevent any infinite stall
      i++;
    }
  }

  return elements;
}

export const StudyMarkdown = React.memo(function StudyMarkdown({ content, onNavigateHeading }) {
  if (!content) return null;

  // Memoize markdown elements so re-renders of parent don't re-parse or re-render KaTeX
  const elements = useMemo(() => {
    const t0 = typeof performance !== 'undefined' ? performance.now() : Date.now();
    const parsed = parseMarkdownContent(content);
    const elapsed = ((typeof performance !== 'undefined' ? performance.now() : Date.now()) - t0).toFixed(1);
    console.log(`[StudyAI] StudyMarkdown parsed ${content.length} chars into ${parsed.length} elements in ${elapsed}ms.`);
    return parsed;
  }, [content]);

  return <div className="study-markdown-content space-y-1">{elements}</div>;
});
