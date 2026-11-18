import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ArrowRight,
  BookOpen,
  CheckCircle2,
  FileText,
  Layers,
  Lightbulb,
  Sparkles,
  UploadCloud
} from 'lucide-react';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { Chip } from '../components/ui/Chip';

const learningSteps = [
  {
    number: '01',
    title: 'Start with the subject',
    description: 'Get a short orientation before diving into chapters and terminology.',
    icon: <Lightbulb size={18} />
  },
  {
    number: '02',
    title: 'Map the syllabus',
    description: 'See the topics found in your material and the source pages available for them.',
    icon: <Layers size={18} />
  },
  {
    number: '03',
    title: 'Learn one topic deeply',
    description: 'Choose a small section for a clear explanation, examples, diagrams, and formulas when the source supports them.',
    icon: <BookOpen size={18} />
  }
];

const principles = [
  {
    title: 'Stay close to your material',
    description: 'Study guides use your uploaded notes as their factual source and surface gaps when evidence is missing.',
    icon: <FileText size={20} />,
    color: 'var(--indigo)',
    tint: 'var(--indigo-tint)'
  },
  {
    title: 'Understand, then revise',
    description: 'Move from a subject overview to a syllabus map, then focus on one topic before practicing.',
    icon: <Layers size={20} />,
    color: 'var(--teal)',
    tint: 'var(--teal-tint)'
  },
  {
    title: 'See what needs checking',
    description: 'When extraction or source evidence is uncertain, review the affected content instead of treating it as verified.',
    icon: <CheckCircle2 size={20} />,
    color: 'var(--coral)',
    tint: 'var(--coral-tint)'
  }
];

export function Landing() {
  const navigate = useNavigate();

  return (
    <div className="fade-in" style={{ paddingBottom: '3rem' }}>
      <section style={{
        maxWidth: '900px',
        margin: '0 auto',
        padding: '4.5rem 1rem 3.5rem',
        textAlign: 'center'
      }}>
        <Chip variant="indigo" icon={<Sparkles size={13} />} style={{ marginBottom: '1.25rem' }}>
          Source-guided learning
        </Chip>
        <h1 style={{
          maxWidth: '820px',
          margin: '0 auto 1.25rem',
          fontSize: 'clamp(2.4rem, 6vw, 4.25rem)',
          fontWeight: 800,
          lineHeight: 1.04,
          letterSpacing: '-0.045em'
        }}>
          Understand the subject.
          <br />
          <span style={{ color: 'var(--indigo)' }}>Master one topic at a time.</span>
        </h1>
        <p style={{
          maxWidth: '680px',
          margin: '0 auto 2rem',
          color: 'var(--muted)',
          fontSize: '1.08rem',
          lineHeight: 1.7
        }}>
          Upload your study material, see what it covers, and choose a small topic for a deeper explanation.
          Examples, diagrams, and calculations are included when supported by the source or clearly identified as extra context.
        </p>
        <div style={{ display: 'flex', justifyContent: 'center', gap: '12px', flexWrap: 'wrap' }}>
          <Button
            variant="primary"
            size="lg"
            icon={<UploadCloud size={18} />}
            iconRight={<ArrowRight size={16} />}
            onClick={() => navigate('/upload')}
          >
            Explore your material
          </Button>
          <Button
            variant="secondary"
            size="lg"
            onClick={() => navigate('/dashboard')}
          >
            Open dashboard
          </Button>
        </div>
      </section>

      <section aria-labelledby="learning-flow-title" style={{ maxWidth: '1040px', margin: '0 auto 4rem' }}>
        <div className="sa-card" style={{
          padding: 'clamp(1.25rem, 4vw, 2.5rem)',
          boxShadow: 'var(--shadow-lg)',
          background: 'linear-gradient(180deg, var(--surface) 0%, var(--bg) 100%)'
        }}>
          <div style={{ marginBottom: '1.75rem' }}>
            <p style={{
              color: 'var(--indigo)',
              fontSize: '0.75rem',
              fontWeight: 700,
              letterSpacing: '0.12em',
              textTransform: 'uppercase',
              marginBottom: '0.5rem'
            }}>
              A clearer way to study
            </p>
            <h2 id="learning-flow-title" style={{ fontSize: 'clamp(1.5rem, 3vw, 2rem)' }}>
              From broad context to focused understanding
            </h2>
          </div>
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(min(100%, 230px), 1fr))',
            gap: '1rem'
          }}>
            {learningSteps.map((step) => (
              <article
                key={step.number}
                style={{
                  position: 'relative',
                  minHeight: '190px',
                  padding: '1.25rem',
                  border: '1px solid var(--border)',
                  borderRadius: '16px',
                  background: 'var(--surface)'
                }}
              >
                <div style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  marginBottom: '1.25rem',
                  color: 'var(--indigo)'
                }}>
                  {step.icon}
                  <span style={{
                    color: 'var(--subtle)',
                    fontFamily: 'var(--font-mono)',
                    fontSize: '0.78rem'
                  }}>
                    {step.number}
                  </span>
                </div>
                <h3 style={{ fontSize: '1.08rem', marginBottom: '0.5rem' }}>{step.title}</h3>
                <p style={{ color: 'var(--muted)', fontSize: '0.9rem', lineHeight: 1.6 }}>
                  {step.description}
                </p>
              </article>
            ))}
          </div>
          <p style={{
            marginTop: '1rem',
            color: 'var(--muted)',
            fontSize: '0.82rem',
            lineHeight: 1.5
          }}>
            General subject context and material extracted from your upload are shown as different kinds of information.
          </p>
        </div>
      </section>

      <section aria-labelledby="study-principles-title" style={{ maxWidth: '1040px', margin: '0 auto 4rem' }}>
        <div style={{ marginBottom: '1.5rem' }}>
          <h2 id="study-principles-title" style={{ fontSize: 'clamp(1.5rem, 3vw, 2rem)', marginBottom: '0.5rem' }}>
            Built around real study work
          </h2>
          <p style={{ color: 'var(--muted)', lineHeight: 1.6 }}>
            Use your material to learn, practice, and identify what still needs review.
          </p>
        </div>
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(min(100%, 260px), 1fr))',
          gap: '1rem'
        }}>
          {principles.map((principle) => (
            <Card key={principle.title}>
              <div style={{
                width: '42px',
                height: '42px',
                display: 'grid',
                placeItems: 'center',
                borderRadius: '12px',
                background: principle.tint,
                color: principle.color,
                marginBottom: '1rem'
              }}>
                {principle.icon}
              </div>
              <h3 style={{ fontSize: '1.08rem', marginBottom: '0.5rem' }}>{principle.title}</h3>
              <p style={{ color: 'var(--muted)', fontSize: '0.9rem', lineHeight: 1.65 }}>
                {principle.description}
              </p>
            </Card>
          ))}
        </div>
      </section>

      <footer style={{
        maxWidth: '1040px',
        margin: '0 auto',
        borderTop: '1px solid var(--border)',
        paddingTop: '1.5rem',
        color: 'var(--muted)',
        fontSize: '0.85rem'
      }}>
        StudyAI · A study workspace for understanding and practice.
      </footer>
    </div>
  );
}
