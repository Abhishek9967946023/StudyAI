import React, { useState, useEffect, useMemo } from 'react';
import {
  Layers,
  BookOpen,
  Folder,
  FileText,
  Sparkles,
  ChevronRight,
  ChevronDown,
  Search,
  CheckCircle2,
  Clock,
  ArrowRight,
  RefreshCw,
  AlertCircle,
  ExternalLink
} from 'lucide-react';
import { getSyllabusTree } from '../../services/materialsService';

function getNodeIcon(nodeType) {
  switch (nodeType) {
    case 'knowledge_area':
      return <Layers size={15} className="text-indigo-400 shrink-0" />;
    case 'chapter':
      return <BookOpen size={15} className="text-cyan-400 shrink-0" />;
    case 'section':
      return <Folder size={14} className="text-amber-400 shrink-0" />;
    case 'topic':
      return <FileText size={14} className="text-emerald-400 shrink-0" />;
    case 'concept':
    default:
      return <Sparkles size={13} className="text-purple-400 shrink-0" />;
  }
}

function getNodeBadge(nodeType) {
  const map = {
    knowledge_area: 'bg-indigo-950/80 text-indigo-300 border-indigo-500/30',
    chapter: 'bg-cyan-950/80 text-cyan-300 border-cyan-500/30',
    section: 'bg-amber-950/80 text-amber-300 border-amber-500/30',
    topic: 'bg-emerald-950/80 text-emerald-300 border-emerald-500/30',
    concept: 'bg-purple-950/80 text-purple-300 border-purple-500/30'
  };
  return map[nodeType] || 'bg-slate-900 text-slate-400 border-slate-800';
}

function TreeNode({
  node,
  level = 0,
  searchQuery = '',
  expandedMap,
  toggleExpand,
  onSelectTopic
}) {
  const hasChildren = node.subtopics && node.subtopics.length > 0;
  const isExpanded = expandedMap[node.id] !== false; // Default expanded

  const matchesSearch = useMemo(() => {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    const nameMatch = node.name?.toLowerCase().includes(q);
    const descMatch = node.description?.toLowerCase().includes(q);
    const pathMatch = node.hierarchy_path?.toLowerCase().includes(q);
    return nameMatch || descMatch || pathMatch;
  }, [node, searchQuery]);

  // Recursively check if any children match
  const childrenMatch = useMemo(() => {
    if (!hasChildren || !searchQuery) return false;
    const checkChild = (n) => {
      const q = searchQuery.toLowerCase();
      if (n.name?.toLowerCase().includes(q) || n.description?.toLowerCase().includes(q)) return true;
      return n.subtopics?.some(checkChild);
    };
    return node.subtopics.some(checkChild);
  }, [node, searchQuery, hasChildren]);

  if (searchQuery && !matchesSearch && !childrenMatch) {
    return null;
  }

  const isTeachingReady = ['EXTRACTED', 'TEACHING_READY', 'VERIFIED'].includes(node.coverage_status);

  return (
    <div className="select-none">
      <div
        className={`group flex items-center justify-between gap-3 px-3 py-2.5 rounded-xl transition-all border ${
          matchesSearch && searchQuery
            ? 'bg-indigo-950/40 border-indigo-500/40'
            : 'bg-slate-950/40 hover:bg-slate-900/60 border-slate-900 hover:border-slate-800'
        }`}
        style={{ marginLeft: `${Math.min(level * 20, 100)}px` }}
      >
        <div className="flex items-center gap-2.5 min-w-0 flex-1">
          {hasChildren ? (
            <button
              onClick={() => toggleExpand(node.id)}
              className="w-5 h-5 rounded flex items-center justify-center text-slate-400 hover:text-white transition-colors"
            >
              {isExpanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
            </button>
          ) : (
            <span className="w-5" />
          )}

          {getNodeIcon(node.node_type)}

          <span className="text-[11px] font-mono text-slate-500 shrink-0">
            {node.hierarchy_path}
          </span>

          <span className="text-xs sm:text-sm font-semibold text-slate-200 group-hover:text-white truncate">
            {node.name}
          </span>

          <span className={`text-[10px] font-medium uppercase px-1.5 py-0.5 rounded border shrink-0 hidden sm:inline-block ${getNodeBadge(node.node_type)}`}>
            {node.node_type.replace('_', ' ')}
          </span>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          {node.page_start && (
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-900 border border-slate-800 text-slate-400">
              p.{node.page_start}{node.page_end && node.page_end !== node.page_start ? `–${node.page_end}` : ''}
            </span>
          )}

          {isTeachingReady ? (
            <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-emerald-950/80 border border-emerald-500/40 text-emerald-300 flex items-center gap-1">
              <CheckCircle2 size={11} />
              <span className="hidden md:inline">{node.coverage_status === 'EXTRACTED' ? 'Source notes' : 'AI notes'}</span>
            </span>
          ) : (
            <span className="text-[10px] font-medium px-2 py-0.5 rounded-full bg-slate-900 border border-slate-800 text-slate-500 flex items-center gap-1">
              <Clock size={11} />
              <span className="hidden md:inline">Discovered</span>
            </span>
          )}

          <button
            onClick={() => onSelectTopic && onSelectTopic(node.id)}
            className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-indigo-600/30 hover:bg-indigo-600 border border-indigo-500/40 text-indigo-300 hover:text-white text-xs font-semibold transition-all shadow-sm"
            title="Read deep contextual teaching notes for this topic"
          >
            <span>Teach</span>
            <ArrowRight size={12} />
          </button>
        </div>
      </div>

      {hasChildren && isExpanded && (
        <div className="mt-1 space-y-1">
          {node.subtopics.map((child) => (
            <TreeNode
              key={child.id}
              node={child}
              level={level + 1}
              searchQuery={searchQuery}
              expandedMap={expandedMap}
              toggleExpand={toggleExpand}
              onSelectTopic={onSelectTopic}
            />
          ))}
        </div>
      )}
    </div>
  );
}

export function SyllabusTreeTab({ documentId, onSelectTopic }) {
  const [syllabus, setSyllabus] = useState([]);
  const [totalTopics, setTotalTopics] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [expandedMap, setExpandedMap] = useState({});

  useEffect(() => {
    async function load() {
      if (!documentId) return;
      setLoading(true);
      setError(null);
      try {
        const res = await getSyllabusTree(documentId, false);
        setSyllabus(res?.syllabus || []);
        setTotalTopics(res?.total_topics || 0);
      } catch (err) {
        console.error('Failed to load syllabus tree:', err);
        setError('Failed to load hierarchical syllabus tree.');
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [documentId]);

  const toggleExpand = (nodeId) => {
    setExpandedMap(prev => ({
      ...prev,
      [nodeId]: prev[nodeId] === false ? true : false
    }));
  };

  const handleExpandAll = () => {
    setExpandedMap({});
  };

  const handleCollapseAll = () => {
    const collapsed = {};
    const collapseRec = (nodes) => {
      nodes.forEach(n => {
        collapsed[n.id] = false;
        if (n.subtopics) collapseRec(n.subtopics);
      });
    };
    collapseRec(syllabus);
    setExpandedMap(collapsed);
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center p-12 text-slate-400">
        <RefreshCw size={28} className="animate-spin text-cyan-400 mb-3" />
        <p className="text-sm font-medium">Building complete 6-level syllabus tree...</p>
      </div>
    );
  }

  if (error || syllabus.length === 0) {
    return (
      <div className="max-w-2xl mx-auto rounded-2xl bg-slate-900/80 border border-slate-800 p-8 text-center">
        <AlertCircle size={32} className="text-amber-400 mx-auto mb-3" />
        <h3 className="text-base font-bold text-white mb-2">Syllabus Tree Empty</h3>
        <p className="text-sm text-slate-400 mb-4">{error || 'No topics discovered yet.'}</p>
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto space-y-6 animate-fade-in">
      {/* Header and Controls */}
      <div className="rounded-2xl bg-slate-900/80 backdrop-blur-md border border-slate-800 p-6 flex flex-col sm:flex-row items-center justify-between gap-4 shadow-xl">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-lg font-bold text-white">Hierarchical Syllabus Explorer</h2>
            <span className="text-xs font-mono px-2 py-0.5 rounded-full bg-indigo-950 border border-indigo-500/30 text-indigo-300">
              {totalTopics} Discovered Nodes
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Complete multi-tiered curriculum tree: Knowledge Area → Chapter → Section → Topic → Concept.
          </p>
        </div>

        <div className="flex items-center gap-2 w-full sm:w-auto">
          {/* Search Box */}
          <div className="relative flex-1 sm:w-64">
            <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search topics, formulas..."
              className="w-full pl-9 pr-3 py-1.5 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition-colors"
            />
          </div>

          <button
            onClick={handleExpandAll}
            className="px-2.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium transition-colors"
          >
            Expand
          </button>
          <button
            onClick={handleCollapseAll}
            className="px-2.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium transition-colors"
          >
            Collapse
          </button>
        </div>
      </div>

      {/* Tree View Container */}
      <div className="rounded-2xl bg-slate-900/60 backdrop-blur-md border border-slate-800 p-4 sm:p-6 shadow-2xl space-y-1.5">
        {syllabus.map((rootNode) => (
          <TreeNode
            key={rootNode.id}
            node={rootNode}
            level={0}
            searchQuery={searchQuery}
            expandedMap={expandedMap}
            toggleExpand={toggleExpand}
            onSelectTopic={onSelectTopic}
          />
        ))}
      </div>
    </div>
  );
}

