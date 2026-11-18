/**
 * =============================================================================
 * StudyAI — Mock Academic Dataset (Strictly No Lorem Ipsum)
 * Realistic Domain: Biology — Photosynthesis & Energy Transfer
 * =============================================================================
 */

export const MOCK_MATERIAL_ID = 'mat-bio-photosynthesis-01';

export const MOCK_MATERIAL = {
  id: MOCK_MATERIAL_ID,
  title: 'Chapter 8: Photosynthesis, Photophosphorylation & The Calvin Cycle',
  subject: 'Biological Sciences & Plant Physiology',
  pageCount: 18,
  charCount: 24850,
  uploadedAt: '2026-03-12T10:30:00Z',
  fileType: 'pdf',
  status: 'ready'
};

export const MOCK_ANALYSIS = {
  materialId: MOCK_MATERIAL_ID,
  title: 'Chapter 8: Photosynthesis, Photophosphorylation & The Calvin Cycle',
  pages: 18,
  charCount: 24850,
  estimatedReadTime: '12 min',
  executiveSummary: 'Photosynthesis is the fundamental bioenergetic pathway converting solar radiant flux into chemical potential stored in glyceraldehyde-3-phosphate. The process bifurcates into light-dependent thylakoid reactions driven by photosystems I and II, and light-independent stromatic carbon assimilation catalyzed by RuBisCO.',
  keyConcepts: [
    { title: 'Z-Scheme Photochemistry', text: 'Sequential excitation of P680 and P700 driving non-cyclic electron transport from water to NADP+.' },
    { title: 'Proton-Motive Chemiosmosis', text: 'Cytochrome b6f proton translocation into the thylakoid lumen establishing the pmf driving CF0-CF1 ATP synthase.' },
    { title: 'RuBisCO Oxygenase Competition', text: 'Enzymatic partitioning between carboxylation and wasteful photorespiration (C2 cycle) under heat/drought.' }
  ],
  topics: [
    { id: 't-1', name: 'Light Reactions & Photolysis', importance: 94, category: 'Bioenergetics' },
    { id: 't-2', name: 'Calvin Cycle & Carbon Fixation', importance: 92, category: 'Biochemistry' },
    { id: 't-3', name: 'Chloroplast Structure & Thylakoids', importance: 78, category: 'Cytology' },
    { id: 't-4', name: 'Electron Transport & ATP Synthase', importance: 88, category: 'Biophysics' },
    { id: 't-5', name: 'Photorespiration & C4 Adaptations', importance: 58, category: 'Ecophysiology' },
    { id: 't-6', name: 'Pigment Absorption & Action Spectra', importance: 62, category: 'Photobiology' }
  ],
  knowledgeMap: [
    { source: 'Pigment Absorption', target: 'Light Reactions & Photolysis', relation: 'Feeds excitation energy to' },
    { source: 'Light Reactions & Photolysis', target: 'Electron Transport & ATP Synthase', relation: 'Supplies electrons & protons to' },
    { source: 'Electron Transport & ATP Synthase', target: 'Calvin Cycle & Carbon Fixation', relation: 'Provides ATP and NADPH for' },
    { source: 'Calvin Cycle & Carbon Fixation', target: 'Photorespiration & C4 Adaptations', relation: 'Compromised by O2 during' }
  ]
};

export const MOCK_SUMMARY = {
  materialId: MOCK_MATERIAL_ID,
  sections: [
    {
      id: 'sec-exec',
      title: 'Executive Abstract',
      content: 'Photosynthesis operates as nature\'s solar transducer. In oxygenic organisms, the reaction 6CO2 + 6H2O + light -> C6H12O6 + 6O2 captures electromagnetic energy across the visible spectrum (400–700 nm) and converts it into metabolic currency (ATP & NADPH), which subsequent stroma enzymes employ to reduce carbon dioxide into triose phosphates.'
    },
    {
      id: 'sec-concepts',
      title: 'Core Concepts & Mechanisms',
      items: [
        { term: 'Photosystem II (P680)', definition: 'Multisubunit pigment-protein complex with an oxygen-evolving manganese center that extracts electrons from water: 2H2O -> 4H+ + 4e- + O2.' },
        { term: 'Plastoquinone (PQ) & Cytochrome b6f', definition: 'Mobile lipid-soluble carrier that shuttles electrons to the cytochrome b6f complex, pumping 4 protons per pair of electrons into the thylakoid lumen.' },
        { term: 'Photosystem I (P700) & Ferredoxin', definition: 'Absorbs at 700 nm, directing electrons to ferredoxin-NADP+ reductase (FNR) to generate NADPH in the stroma.' },
        { term: 'RuBisCO (Ribulose-1,5-bisphosphate carboxylase/oxygenase)', definition: 'Hexadecameric enzyme fixing 1 CO2 onto 5-carbon RuBP, producing two molecules of 3-phosphoglycerate (3-PGA).' }
      ]
    },
    {
      id: 'sec-formulas',
      title: 'High-Yield Formulas & Stoichiometries',
      items: [
        { label: 'Overall Equation', formula: '6 CO2 + 6 H2O + photons -> C6H12O6 + 6 O2' },
        { label: 'Water Photolysis', formula: '2 H2O -> 4 H+ + 4 e- + O2 (at Oxygen Evolving Complex)' },
        { label: 'Net Calvin Cycle Output', formula: '3 CO2 + 9 ATP + 6 NADPH -> 1 G3P + 9 ADP + 6 NADP+ + 8 Pi' }
      ]
    },
    {
      id: 'sec-facts',
      title: 'Key Academic Distinctions',
      items: [
        'Protons accumulate inside the thylakoid lumen (pH ~5.0) relative to the alkaline stroma (pH ~8.0), creating a ~3 pH unit gradient.',
        'Cyclic photophosphorylation generates ATP exclusively without producing NADPH or releasing oxygen gas, balancing the ATP:NADPH ratio for carbon fixation.',
        'RuBisCO exhibits a low turnover number (~3 catalytic events per second), requiring leaf tissue to dedicate up to 50% of soluble protein to this single enzyme.'
      ]
    }
  ]
};

export const MOCK_QUESTIONS = [
  {
    id: 'q-1',
    topic: 'Light Reactions & Photolysis',
    difficulty: 'Medium',
    type: 'mcq',
    question: 'What is the precise source of electrons used to reduce oxidized P680+ reaction centers in Photosystem II?',
    options: [
      'Photolysis of water molecules at the manganese cluster',
      'Cyclic electron flow from Ferredoxin',
      'Plastocyanin oxidation in the stroma',
      'Direct absorption of electrons from dissolved carbon dioxide'
    ],
    correctAnswer: 'Photolysis of water molecules at the manganese cluster',
    correctIndex: 0,
    explanation: 'The oxygen-evolving complex (OEC) contains a Mn4CaO5 cluster that catalyzes the oxidation of water (2H2O -> 4H+ + 4e- + O2), donating electrons to tyrosine-Z, which reduces P680+.',
    citation: 'Section 8.2, p. 5: "Electrons lost from P680 are replenished via the photolytic cleavage of water within the thylakoid lumen."'
  },
  {
    id: 'q-2',
    topic: 'Light Reactions & Photolysis',
    difficulty: 'Hard',
    type: 'mcq',
    question: 'During non-cyclic photophosphorylation, what drives the accumulation of protons inside the thylakoid lumen?',
    options: [
      'Water photolysis in the lumen and proton translocation by the Cytochrome b6f complex',
      'Direct diffusion of protons from the outer chloroplast membrane',
      'Hydrolysis of ATP by the CF1 subunit in the stroma',
      'Active transport of protons by RuBisCO during carboxylation'
    ],
    correctAnswer: 'Water photolysis in the lumen and proton translocation by the Cytochrome b6f complex',
    correctIndex: 0,
    explanation: 'Protons accumulate in the lumen from two discrete sources: (1) protons released directly by water oxidation at PSII, and (2) plastoquinol oxidation pumping protons across the Cytochrome b6f complex via the Q-cycle.',
    citation: 'Section 8.3, p. 8: "The proton gradient is established both by luminal water oxidation and the Q-cycle mediated by cytochrome b6f."'
  },
  {
    id: 'q-3',
    topic: 'Calvin Cycle & Carbon Fixation',
    difficulty: 'Easy',
    type: 'mcq',
    question: 'Which enzyme catalyzes the primary step of inorganic carbon fixation in the stroma?',
    options: [
      'RuBisCO (Ribulose-1,5-bisphosphate carboxylase/oxygenase)',
      'ATP Synthase (CF0-CF1)',
      'Phosphoenolpyruvate Carboxylase',
      'Carbonic Anhydrase'
    ],
    correctAnswer: 'RuBisCO (Ribulose-1,5-bisphosphate carboxylase/oxygenase)',
    correctIndex: 0,
    explanation: 'RuBisCO fixes one molecule of CO2 onto ribulose 1,5-bisphosphate (RuBP) to yield two molecules of 3-phosphoglycerate.',
    citation: 'Section 8.5, p. 12: "The entry point of inorganic carbon is catalyzed by the stromatic enzyme RuBisCO."'
  },
  {
    id: 'q-4',
    topic: 'Calvin Cycle & Carbon Fixation',
    difficulty: 'Hard',
    type: 'mcq',
    question: 'How many ATP and NADPH molecules are consumed in the Calvin cycle for the net synthesis of one molecule of glyceraldehyde-3-phosphate (G3P)?',
    options: [
      '9 ATP and 6 NADPH',
      '6 ATP and 6 NADPH',
      '18 ATP and 12 NADPH',
      '3 ATP and 2 NADPH'
    ],
    correctAnswer: '9 ATP and 6 NADPH',
    correctIndex: 0,
    explanation: 'Fixing 3 CO2 requires 6 ATP and 6 NADPH in the reduction phase (3-PGA to G3P) plus 3 additional ATP in the RuBP regeneration phase, totaling 9 ATP and 6 NADPH.',
    citation: 'Section 8.6, p. 15: "Net export of one triose phosphate demands nine molecules of ATP and six of NADPH."'
  },
  {
    id: 'q-5',
    topic: 'Electron Transport & ATP Synthase',
    difficulty: 'Medium',
    type: 'tf',
    question: 'True or False: In cyclic photophosphorylation, electrons pass through Photosystem I only, producing ATP without reducing NADP+.',
    options: ['True', 'False'],
    correctAnswer: 'True',
    correctIndex: 0,
    explanation: 'Cyclic photophosphorylation routes electrons from Ferredoxin back into the Cytochrome b6f complex, generating a proton gradient for ATP synthesis without reducing NADP+ to NADPH.',
    citation: 'Section 8.4, p. 10: "Cyclic flow routes electrons through PSI and cyt b6f, sustaining ATP generation when NADPH levels are saturated."'
  },
  {
    id: 'q-6',
    topic: 'Chloroplast Structure & Thylakoids',
    difficulty: 'Easy',
    type: 'tf',
    question: 'True or False: The enzymatic reactions of the Calvin cycle take place inside the thylakoid lumen.',
    options: ['True', 'False'],
    correctAnswer: 'False',
    correctIndex: 1,
    explanation: 'The Calvin cycle takes place in the aqueous stroma surrounding the thylakoid membranes, whereas the thylakoid lumen hosts light reactions and proton accumulation.',
    citation: 'Section 8.1, p. 3: "While light reactions reside within thylakoid membranes, carbon assimilation enzymes operate in the stroma."'
  },
  {
    id: 'q-7',
    topic: 'Photorespiration & C4 Adaptations',
    difficulty: 'Medium',
    type: 'mcq',
    question: 'Under what environmental conditions does RuBisCO increasingly catalyze its oxygenase reaction rather than carboxylation?',
    options: [
      'High temperatures and closed stomata (elevated O2 : CO2 ratio)',
      'Sub-zero temperatures and high humidity',
      'Excessive darkness with water abundance',
      'High atmospheric carbon dioxide saturation'
    ],
    correctAnswer: 'High temperatures and closed stomata (elevated O2 : CO2 ratio)',
    correctIndex: 0,
    explanation: 'Heat promotes stomatal closure to prevent water loss, depleting CO2 while O2 accumulates. Furthermore, RuBisCO affinity for CO2 declines relative to O2 at higher temperatures.',
    citation: 'Section 8.7, p. 16: "Elevated temperatures diminish the solubility ratio of CO2:O2, shifting RuBisCO kinetic preference toward oxygenation."'
  },
  {
    id: 'q-16',
    topic: 'Calvin Cycle & Carbon Fixation',
    difficulty: 'Easy',
    type: 'fill_blank',
    question: 'Fill in the blank: _____ catalyzes the primary step of inorganic carbon fixation in the stroma.',
    options: [],
    correctAnswer: 'RuBisCO (Ribulose-1,5-bisphosphate carboxylase/oxygenase)',
    correctIndex: null,
    explanation: 'RuBisCO fixes CO2 onto RuBP to begin carbon fixation.',
    citation: 'Section 8.5, p. 12: "The entry point of inorganic carbon is catalyzed by the stromatic enzyme RuBisCO."'
  },
  {
    id: 'q-17',
    topic: 'Light Reactions & Photolysis',
    difficulty: 'Hard',
    type: 'long',
    question: 'Explain how water photolysis and the cytochrome b6f complex contribute to the thylakoid proton gradient.',
    options: [],
    correctAnswer: 'Water oxidation releases protons into the thylakoid lumen. Plastoquinol oxidation at the cytochrome b6f complex also transfers protons into the lumen, helping establish the proton gradient used for ATP synthesis.',
    correctIndex: null,
    explanation: 'Both proton sources are described in the cited study material.',
    citation: 'Section 8.3, p. 8: "The proton gradient is established both by luminal water oxidation and the Q-cycle mediated by cytochrome b6f."'
  },
  {
    id: 'q-8',
    topic: 'Pigment Absorption & Action Spectra',
    difficulty: 'Easy',
    type: 'mcq',
    question: 'Which spectral bands are most strongly absorbed by chlorophyll a in terrestrial vascular plants?',
    options: [
      'Blue-violet (430 nm) and red (660 nm)',
      'Green (520 nm) and yellow (580 nm)',
      'Infrared (850 nm) and ultraviolet (300 nm)',
      'Far-red (730 nm) exclusively'
    ],
    correctAnswer: 'Blue-violet (430 nm) and red (660 nm)',
    correctIndex: 0,
    explanation: 'Chlorophyll a absorption spectra peak sharply in the blue-violet (~430 nm) and red (~660 nm) regions, while transmitting/reflecting green wavelengths.',
    citation: 'Section 8.2, p. 4: "Chlorophyll a absorbs maximally at 430 nm and 662 nm, accounting for the characteristic green reflection."'
  },
  {
    id: 'q-9',
    topic: 'Calvin Cycle & Carbon Fixation',
    difficulty: 'Medium',
    type: 'short',
    question: 'Name the specific 5-carbon acceptor molecule onto which CO2 is fixed by RuBisCO in the Calvin cycle.',
    options: [],
    correctAnswer: 'Ribulose 1,5-bisphosphate (RuBP)',
    explanation: 'RuBisCO fixes carbon dioxide onto ribulose 1,5-bisphosphate (RuBP), generating two molecules of 3-phosphoglycerate.',
    citation: 'Section 8.5, p. 12: "The initial carboxylation fixes CO2 onto the five-carbon acceptor ribulose 1,5-bisphosphate (RuBP)."'
  },
  {
    id: 'q-10',
    topic: 'Light Reactions & Photolysis',
    difficulty: 'Hard',
    type: 'short',
    question: 'What is the primary role of the Cytochrome b6f complex in photosynthetic electron transport?',
    options: [],
    correctAnswer: 'Translocates protons into the thylakoid lumen and shuttles electrons to plastocyanin',
    explanation: 'Cytochrome b6f couples electron transfer between PSII and PSI to proton translocation across the membrane via the Q-cycle, building the proton motive force for ATP synthesis.',
    citation: 'Section 8.3, p. 7: "Cytochrome b6f mediates electron flow from plastoquinol to plastocyanin while pumping protons into the lumen."'
  },
  {
    id: 'q-11',
    topic: 'Pigment Absorption & Action Spectra',
    difficulty: 'Medium',
    type: 'tf',
    question: 'True or False: Carotenoid accessory pigments absorb light in the blue-green spectrum and dissipate excessive radiant energy as heat to protect chlorophyll.',
    options: ['True', 'False'],
    correctAnswer: 'True',
    correctIndex: 0,
    explanation: 'Carotenoids absorb photons in the blue-green wavelengths (400-500 nm) and perform non-photochemical quenching to prevent photo-oxidative damage to chlorophyll.',
    citation: 'Section 8.2, p. 5: "Accessory carotenoids absorb between 400 and 500 nm, dissipating excess energy via photoprotective non-photochemical quenching."'
  },
  {
    id: 'q-12',
    topic: 'Photorespiration & C4 Adaptations',
    difficulty: 'Medium',
    type: 'short',
    question: 'Explain why photorespiration is considered energetically wasteful for C3 plants.',
    options: [],
    correctAnswer: 'Consumes ATP and NADPH while releasing previously fixed CO2 without producing sugar',
    explanation: 'Photorespiration occurs when RuBisCO binds O2 instead of CO2, consuming metabolic ATP and reducing power to salvage phosphoglycolate while dissipating up to 25% of fixed carbon.',
    citation: 'Section 8.7, p. 17: "Photorespiration consumes ATP and reducing equivalents while expelling CO2 without generating ATP or carbohydrates."'
  },
  {
    id: 'q-13',
    topic: 'Light Reactions & Photolysis',
    difficulty: 'Medium',
    type: 'msq',
    question: 'Which statements about water photolysis at Photosystem II are correct?',
    options: [
      'It releases electrons that replenish oxidized P680.',
      'It occurs in the chloroplast stroma.',
      'It releases protons into the thylakoid lumen.',
      'It directly produces NADPH.'
    ],
    correctAnswer: [
      'It releases electrons that replenish oxidized P680.',
      'It releases protons into the thylakoid lumen.'
    ],
    correctIndices: [0, 2],
    marks: 2,
    explanation: 'Water oxidation at the oxygen-evolving complex releases electrons and protons into the lumen; NADPH production occurs downstream at ferredoxin-NADP+ reductase.',
    citation: 'Section 8.2, p. 5: water photolysis replenishes electrons lost from P680 and contributes protons to the thylakoid lumen.'
  }
];

export const MOCK_TOPIC_INTELLIGENCE = [
  {
    topic: 'Light Reactions & Photolysis',
    name: 'Light Reactions & Photolysis',
    importance: 94,
    performance: 35, // Weak (< 60)
    priority: 'CRITICAL',
    source_pages: 'Pages 4–8',
    source_reference: 'Pages 4–8',
    questionsCount: 12,
    recommendation: 'Priority 1: Re-study Z-scheme electron donors and photolysis equations.'
  },
  {
    topic: 'Electron Transport & ATP Synthase',
    name: 'Electron Transport & ATP Synthase',
    importance: 88,
    performance: 55, // Weak (< 60)
    priority: 'CRITICAL',
    source_pages: 'Pages 9–12',
    source_reference: 'Pages 9–12',
    questionsCount: 10,
    recommendation: 'Priority 1: Review proton motive force and Q-cycle mechanisms.'
  },
  {
    topic: 'Calvin Cycle & Carbon Fixation',
    name: 'Calvin Cycle & Carbon Fixation',
    importance: 92,
    performance: 88, // Strong (>= 60)
    priority: 'MAINTAIN',
    source_pages: 'Pages 13–16',
    source_reference: 'Pages 13–16',
    questionsCount: 14,
    recommendation: 'Maintain: High mastery achieved. Schedule quick retention refresher.'
  },
  {
    topic: 'Chloroplast Structure & Thylakoids',
    name: 'Chloroplast Structure & Thylakoids',
    importance: 78,
    performance: 85, // Strong
    priority: 'MAINTAIN',
    source_pages: 'Pages 1–3',
    source_reference: 'Pages 1–3',
    questionsCount: 8,
    recommendation: 'Maintain: Solid structural comprehension.'
  },
  {
    topic: 'Pigment Absorption & Action Spectra',
    name: 'Pigment Absorption & Action Spectra',
    importance: 62,
    performance: 75, // Strong
    priority: 'MAINTAIN',
    source_pages: 'Pages 3–5',
    source_reference: 'Pages 3–5',
    questionsCount: 6,
    recommendation: 'Maintain: Proficient understanding of absorption vs action spectra.'
  },
  {
    topic: 'Photorespiration & C4 Adaptations',
    name: 'Photorespiration & C4 Adaptations',
    importance: 58,
    performance: 45, // Low importance + Weak
    priority: 'PRACTICE',
    source_pages: 'Pages 17–19',
    source_reference: 'Pages 17–19',
    questionsCount: 6,
    recommendation: 'Practice if time permits: Focus on RuBisCO oxygenase reaction after core topics.'
  }
];

export const MOCK_REVISION_PLAN = {
  materialId: MOCK_MATERIAL_ID,
  date: 'Today',
  totalEstimatedMinutes: 24,
  completedItemsCount: 1,
  totalItemsCount: 4,
  items: [
    {
      id: 'rev-1',
      topic: 'Light Reactions & Photolysis',
      importance: 94,
      currentScore: 50,
      priority: 'Critical',
      actionTitle: 'Master Oxygen-Evolving Complex & Z-Scheme',
      estimatedMinutes: 8,
      completed: false,
      notes: [
        'Photolysis splits water at PSII: 2H2O -> 4H+ + 4e- + O2. Oxygen comes strictly from water, not CO2.',
        'Protons are pumped into the lumen, not the stroma. The lumen is acidic (pH ~5.0).'
      ],
      practiceQuestionsCount: 4
    },
    {
      id: 'rev-2',
      topic: 'Electron Transport & ATP Synthase',
      importance: 88,
      currentScore: 55,
      priority: 'Critical',
      actionTitle: 'Chemiosmotic Coupling & Cyclic Flow',
      estimatedMinutes: 6,
      completed: false,
      notes: [
        'Plastoquinone transfers 2e- and picks up 2H+ from stroma, releasing them into lumen at cyt b6f.',
        'Cyclic flow involves PSI -> Ferredoxin -> cyt b6f -> Plastocyanin -> PSI, synthesizing ATP without NADPH.'
      ],
      practiceQuestionsCount: 3
    },
    {
      id: 'rev-3',
      topic: 'Photorespiration & C4 Adaptations',
      importance: 58,
      currentScore: 45,
      priority: 'Practice if time permits',
      actionTitle: 'RuBisCO Oxygenase Byproduct (2-Phosphoglycolate)',
      estimatedMinutes: 5,
      completed: false,
      notes: [
        'RuBisCO + O2 forms 1 3-PGA and 1 2-phosphoglycolate (toxic, recycled in peroxisomes/mitochondria).'
      ],
      practiceQuestionsCount: 2
    },
    {
      id: 'rev-4',
      topic: 'Calvin Cycle & Carbon Fixation',
      importance: 92,
      currentScore: 88,
      priority: 'Maintain',
      actionTitle: 'High-Yield Stoichiometry Retention Check',
      estimatedMinutes: 5,
      completed: true,
      notes: [
        '3 CO2 fixed = 6 G3P formed = 1 net G3P exported + 5 G3P recycled to 3 RuBP with 3 ATP.'
      ],
      practiceQuestionsCount: 2
    }
  ]
};

export const MOCK_HISTORY = [
  {
    id: 'exam-hist-1',
    examTitle: 'Chapter 8 Comprehensive Assessment',
    date: 'Today, 12:45 PM',
    scorePercent: 78,
    totalQuestions: 15,
    correctCount: 12,
    timeSpent: '11m 42s',
    weakTopics: ['Light Reactions & Photolysis', 'Electron Transport & ATP Synthase']
  },
  {
    id: 'exam-hist-2',
    examTitle: 'Photosystems & Light Reactions Mini-Quiz',
    date: 'Yesterday, 4:15 PM',
    scorePercent: 60,
    totalQuestions: 10,
    correctCount: 6,
    timeSpent: '8m 20s',
    weakTopics: ['Light Reactions & Photolysis']
  },
  {
    id: 'exam-hist-3',
    examTitle: 'Carbon Fixation & Stroma Enzymology',
    date: '2 days ago, 7:30 PM',
    scorePercent: 90,
    totalQuestions: 10,
    correctCount: 9,
    timeSpent: '7m 10s',
    weakTopics: []
  }
];
