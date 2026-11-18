"""
=============================================================================
StudyAI — Benchmark Evaluation Dataset (20 Real Academic Documents)
=============================================================================
Provides 20 real academic documents / document sections across diverse
disciplines with authoritative textbook material for evaluating AI quality.
Used to generate 100 questions (5 per document) and measure quality metrics.
=============================================================================
"""

BENCHMARK_DOCUMENTS = [
    {
        "id": "doc-01-os-scheduling",
        "title": "Operating Systems: CPU Scheduling & Context Switching",
        "subject": "Operating Systems",
        "category": "Computer Science",
        "content": """Chapter 3: Process Management, Thread Execution, and CPU Scheduling.
A process is an active program in execution requiring resources including CPU time, memory, and I/O devices. The Process Control Block (PCB) is the central data structure maintained by the operating system kernel to track process state, program counter, CPU registers, memory management information, and accounting details.

When the CPU switches between processes, a context switch occurs. During a context switch, the kernel saves the execution context of the currently running process into its PCB and loads the saved context of the newly scheduled process from its PCB. Context switching imposes pure computational overhead because the CPU performs no user application work while switching hardware state and flushing caches.

CPU scheduling algorithms determine which ready process is allocated CPU execution time. First-Come First-Served (FCFS) scheduling is non-preemptive and simple to implement using a FIFO queue, but it frequently suffers from the convoy effect, where short CPU-burst processes are delayed behind a long CPU-burst process, resulting in high average waiting times. Shortest Job First (SJF) scheduling selects the process with the shortest expected CPU burst; it is provably optimal in minimizing average waiting time, but requires burst time prediction. Round Robin (RR) scheduling is a preemptive algorithm designed for time-sharing systems where each process receives a cyclic CPU time quantum. If the time quantum is excessively large, RR degenerates into FCFS; if it is too small, context switching overhead dominates CPU execution.""",
        "key_entities": ["Process Control Block", "context switch", "First-Come First-Served", "convoy effect", "Shortest Job First", "Round Robin", "time quantum"],
        "copilot_grounded_query": "What causes the convoy effect in CPU scheduling?",
        "copilot_ungrounded_query": "How does photosynthesis produce glucose in plants?"
    },
    {
        "id": "doc-02-os-virtual-memory",
        "title": "Operating Systems: Virtual Memory & Page Replacement",
        "subject": "Operating Systems",
        "category": "Computer Science",
        "content": """Chapter 9: Virtual Memory Architecture and Paging Systems.
Virtual memory separates user logical memory from physical memory, allowing execution of processes whose address spaces exceed available physical RAM. Memory management units (MMUs) map logical virtual addresses into physical addresses through page tables. Demand paging loads pages into memory only when they are referenced during program execution.

When a process references a virtual page not currently resident in physical frames, the MMU hardware triggers a page fault trap to the operating system kernel. The kernel handles the page fault by suspending the process, locating the required page on backing storage (swap disk), allocating an empty physical frame, reading the page from disk, updating the page table entry with a valid bit, and restarting the faulted instruction.

When all physical memory frames are occupied, the page replacement algorithm selects a victim page to evict. The First-In First-Out (FIFO) algorithm evicts the oldest loaded page. FIFO is susceptible to Belady's Anomaly, wherein allocating more physical frames paradoxically results in an increased number of page faults for certain reference strings. The Least Recently Used (LRU) algorithm evicts the page that has not been referenced for the longest duration, approximating the theoretical optimal offline page replacement algorithm (Belady's MIN). LRU does not suffer from Belady's anomaly because it belongs to the class of stack algorithms.""",
        "key_entities": ["virtual memory", "demand paging", "page fault", "page replacement", "Belady's Anomaly", "Least Recently Used", "stack algorithms"],
        "copilot_grounded_query": "What is Belady's Anomaly and which page replacement algorithm experiences it?",
        "copilot_ungrounded_query": "What are the rules of soccer regarding offside?"
    },
    {
        "id": "doc-03-os-concurrency",
        "title": "Operating Systems: Process Synchronization & Deadlocks",
        "subject": "Operating Systems",
        "category": "Computer Science",
        "content": """Chapter 5: Process Synchronization, Critical Sections, and Deadlock Conditions.
In multitasking systems, concurrent threads sharing memory can experience race conditions, where final execution outcome depends on arbitrary instruction interleaving. A critical section is a code block accessing shared variables. A valid critical section solution must satisfy three criteria: Mutual Exclusion (only one process in critical section), Progress (unblocked processes select next entrant without delay), and Bounded Waiting (entry requests must be granted within finite steps).

Edsger Dijkstra introduced the Semaphore, an integer synchronization variable accessed via two atomic operations: wait() or P(), which decrements the value and blocks if non-positive; and signal() or V(), which increments the value and unblocks waiting processes. Binary semaphores act as mutex locks with values 0 or 1, while counting semaphores coordinate access to finite resource pools.

A deadlock occurs when a set of processes are permanently blocked waiting for resources held by each other. According to E.G. Coffman (1971), a deadlock requires four simultaneous conditions: Mutual Exclusion (non-shareable resources), Hold and Wait (holding resources while requesting others), No Preemption (resources cannot be forcibly reclaimed), and Circular Wait (a circular chain of processes where each waits for a resource held by the next). Dijkstra's Banker's Algorithm prevents deadlock through dynamic avoidance by evaluating resource allocation state transitions to maintain a guaranteed safe sequence.""",
        "key_entities": ["critical section", "Mutual Exclusion", "Bounded Waiting", "Semaphore", "wait()", "signal()", "Coffman conditions", "Circular Wait", "Banker's Algorithm"],
        "copilot_grounded_query": "What are the four Coffman conditions required for a deadlock?",
        "copilot_ungrounded_query": "Who won the 1994 FIFA World Cup?"
    },
    {
        "id": "doc-04-net-transport",
        "title": "Computer Networks: Transmission Control Protocol (TCP)",
        "subject": "Computer Networks",
        "category": "Computer Science",
        "content": """Transport Layer Architecture: Transmission Control Protocol (TCP).
The Transmission Control Protocol (RFC 793) is a connection-oriented, full-duplex transport protocol providing reliable, sequenced byte streams over unreliable IP networks. TCP establishes connections using a three-way handshake: the client transmits a SYN packet with initial sequence number x; the server responds with a SYN-ACK packet containing sequence number y and acknowledgment x+1; and the client confirms with an ACK packet containing acknowledgment y+1.

TCP achieves reliability through cumulative acknowledgments, sequence numbering of byte payloads, checksums, and adaptive retransmission timers based on Round-Trip Time (RTT) estimations. Flow control protects the receiver from buffer overflow by using a sliding window: the receiver advertises a receive window (rwnd) indicating available buffer space, and the sender throttles transmission to not exceed rwnd unacknowledged bytes.

Congestion control protects network routers from queue collapse by dynamically calculating a congestion window (cwnd). TCP Tahoe and Reno implement four congestion algorithms: Slow Start doubles cwnd exponentially each RTT until reaching the slow start threshold (ssthresh); Congestion Avoidance increments cwnd linearly by 1 MSS per RTT; Fast Retransmit retransmits missing segments upon receiving three duplicate ACKs without waiting for retransmission timeout; and Fast Recovery halves ssthresh while maintaining cwnd at ssthresh plus duplicate ACK inflight packets.""",
        "key_entities": ["Transmission Control Protocol", "three-way handshake", "SYN", "SYN-ACK", "flow control", "sliding window", "congestion window", "Slow Start", "Fast Retransmit"],
        "copilot_grounded_query": "How does TCP establish a connection using the three-way handshake?",
        "copilot_ungrounded_query": "What ingredients are in an authentic Italian tiramisu?"
    },
    {
        "id": "doc-05-net-routing",
        "title": "Computer Networks: Routing Algorithms & Protocols",
        "subject": "Computer Networks",
        "category": "Computer Science",
        "content": """Network Layer Architecture: Routing Algorithms and Path Determination.
The primary duty of the network layer is routing: determining the optimal path packets travel from source to destination across an internetwork graph of routers and links. Routing algorithms are classified as Distance Vector or Link State.

Distance Vector routing algorithms, based on the Bellman-Ford algorithm, operate iteratively, asynchronously, and distributedly. Each router periodically transmits its distance vector (estimated cost to all known destinations) to directly connected neighbors. Distance Vector protocols, such as the Routing Information Protocol (RIP), are prone to the count-to-infinity problem during link failures, where routing loops cause cost estimates to increment endlessly. Remedies include split horizon and poison reverse.

Link State routing algorithms, exemplified by Open Shortest Path First (OSPF), are centralized global algorithms. Each router floods Link State Advertisements (LSAs) containing the identities and costs of its local links to all routers across the autonomous system. Once every router constructs an identical global network topology graph, it executes Dijkstra's Shortest Path Algorithm locally to compute the shortest-path tree from itself to all network nodes, avoiding routing loops and converging rapidly.""",
        "key_entities": ["Distance Vector", "Bellman-Ford", "count-to-infinity", "Link State", "Open Shortest Path First", "Link State Advertisements", "Dijkstra's Shortest Path"],
        "copilot_grounded_query": "How do Link State algorithms like OSPF calculate optimal paths?",
        "copilot_ungrounded_query": "What is the capital of Australia?"
    },
    {
        "id": "doc-06-net-dns-http",
        "title": "Computer Networks: DNS Resolution & Application Protocols",
        "subject": "Computer Networks",
        "category": "Computer Science",
        "content": """Application Layer: Domain Name System (DNS) and Hypertext Transfer Protocol.
The Domain Name System (DNS) is a hierarchical, distributed database converting human-readable hostnames into 32-bit IPv4 or 128-bit IPv6 network addresses. The DNS namespace is partitioned hierarchically: Root DNS servers direct queries to Top-Level Domain (TLD) servers (.com, .org, .edu), which delegate authority to Authoritative DNS servers for specific domains.

DNS queries execute recursively or iteratively. In recursive resolution, the client's local DNS resolver acts on the client's behalf, querying root, TLD, and authoritative servers sequentially until obtaining the resource record. Resource records include A records (IPv4 address), AAAA records (IPv6 address), CNAME records (canonical domain aliases), and MX records (mail exchange servers). DNS responses include a Time-To-Live (TTL) field specifying how long resolvers may cache records locally before issuing fresh queries.

The Hypertext Transfer Protocol (HTTP) is the foundational stateless client-server protocol of the World Wide Web. HTTP/1.0 required a new TCP connection per object request. HTTP/1.1 introduced persistent TCP connections using Keep-Alive headers and pipelining. HTTP/2 revolutionized transport through binary framing and multiplexing multiple concurrent request-response streams over a single TCP connection, eliminating head-of-line blocking at the application layer. HTTPS wraps HTTP traffic inside Transport Layer Security (TLS) cryptographic sessions.""",
        "key_entities": ["Domain Name System", "Top-Level Domain", "Authoritative DNS", "A records", "CNAME records", "Time-To-Live", "HTTP/1.1", "HTTP/2", "multiplexing"],
        "copilot_grounded_query": "What is the role of Time-To-Live (TTL) in DNS caching?",
        "copilot_ungrounded_query": "What is the recipe for chicken tikka masala?"
    },
    {
        "id": "doc-07-dsa-trees",
        "title": "Data Structures: Balanced Binary Search Trees",
        "subject": "Data Structures & Algorithms",
        "category": "Computer Science",
        "content": """Advanced Data Structures: Balanced Binary Search Trees (AVL and Red-Black Trees).
A Binary Search Tree (BST) maintains the ordering invariant that for every node with key k, all keys in its left subtree are strictly less than k, and all keys in its right subtree are strictly greater than k. An unaugmented BST can degenerate into a linear linked list with worst-case search time complexity of O(n) when keys are inserted in sorted order.

An AVL tree, introduced by Georgy Adelson-Velsky and Evgenii Landis (1962), is a strictly height-balanced BST. For every node, the balance factor—defined as the height of its left subtree minus the height of its right subtree—must belong to the set {-1, 0, +1}. When an insertion or deletion violates this property, balance is restored using tree rotations: Single Left (LL) or Right (RR) rotations for monotonic imbalances, and Double Left-Right (LR) or Right-Left (RL) rotations for zigzag imbalances. AVL trees guarantee strict O(log n) worst-case lookup time.

A Red-Black Tree is a self-balancing BST with relaxed balance criteria requiring at most 2 rotations per insertion. Each node is colored red or black, adhering to five invariant rules: every node is red or black; the root is black; all leaf null nodes are black; red nodes cannot have red children (no two consecutive red nodes); and every simple path from any node to its descendant leaves must contain the exact same number of black nodes (uniform black-height). Red-Black trees guarantee maximum tree height <= 2 * log2(n + 1).""",
        "key_entities": ["Binary Search Tree", "AVL tree", "balance factor", "tree rotations", "Red-Black Tree", "black-height", "O(log n)"],
        "copilot_grounded_query": "What are the five invariant rules that define a Red-Black Tree?",
        "copilot_ungrounded_query": "How many teeth does an adult human have?"
    },
    {
        "id": "doc-08-dsa-graphs",
        "title": "Algorithms: Graph Traversals & Shortest Path",
        "subject": "Data Structures & Algorithms",
        "category": "Computer Science",
        "content": """Graph Algorithms: Systematic Traversals and Shortest Path Optimization.
A graph G = (V, E) consists of a set of vertices V and edges E. Graph traversal algorithms visit every vertex reachable from a starting source node.

Breadth-First Search (BFS) explores vertices in layers of increasing distance from the source using a First-In First-Out (FIFO) queue. BFS marks visited nodes to avoid cyclic loops and runs in O(|V| + |E|) time complexity when represented with adjacency lists. BFS computes unweighted shortest paths: the first time BFS visits a vertex, the path discovered contains the minimum number of edge hops.

Depth-First Search (DFS) explores as deep as possible along each branch before backtracking, utilizing a Last-In First-Out (LIFO) stack or recursion. DFS produces discovery and finish timestamps for vertices, categorizing edges into tree, back, forward, and cross edges. DFS is fundamental for detecting cycles in directed graphs, computing strongly connected components (Kosaraju's and Tarjan's algorithms), and determining topological orderings for Directed Acyclic Graphs (DAGs).

Dijkstra's Algorithm solves the Single-Source Shortest Path (SSSP) problem on weighted graphs with non-negative edge weights. Using a min-priority queue (min-heap), Dijkstra's algorithm iteratively extracts the vertex u with minimum provisional distance, relaxes all outgoing incident edges (u, v), and updates distance labels. With a binary heap, Dijkstra's algorithm operates in O((|V| + |E|) log |V|) time.""",
        "key_entities": ["Breadth-First Search", "FIFO queue", "Depth-First Search", "topological orderings", "Directed Acyclic Graphs", "Dijkstra's Algorithm", "Single-Source Shortest Path"],
        "copilot_grounded_query": "Why does Breadth-First Search find shortest paths in unweighted graphs?",
        "copilot_ungrounded_query": "What is the speed limit on the German autobahn?"
    },
    {
        "id": "doc-09-db-acid",
        "title": "Database Systems: ACID Properties & Concurrency Control",
        "subject": "Database Systems",
        "category": "Computer Science",
        "content": """Database Management Systems: Transaction Processing and Concurrency Control.
A transaction is a logical unit of database work consisting of read and write operations. Relational database engines guarantee data integrity by enforcing the ACID properties:
1. Atomicity: All operations in a transaction succeed completely, or the transaction is aborted with all changes rolled back. Atomicity is achieved through Write-Ahead Logging (WAL) and undo logs.
2. Consistency: A transaction transitions the database from one valid state satisfying all schema integrity constraints to another valid state.
3. Isolation: Concurrently executing transactions cannot observe each other's intermediate uncommitted states. The ANSI SQL standard defines four isolation levels: Read Uncommitted, Read Committed, Repeatable Read, and Serializable.
4. Durability: Once a transaction commits, its modifications are permanently recorded in non-volatile storage, surviving subsequent system crashes.

Concurrency control mechanisms prevent anomalies including dirty reads (reading uncommitted data), non-repeatable reads (different values read in same transaction), and phantom reads (new rows appearing in range queries). Strict Two-Phase Locking (Strict 2PL) guarantees conflict serializability. In Strict 2PL, a transaction acquires shared locks for reads and exclusive locks for writes during its growing phase, and releases all locks simultaneously only at commit or abort time during its shrinking phase, preventing cascading aborts.""",
        "key_entities": ["transaction", "Atomicity", "Consistency", "Isolation", "Durability", "Write-Ahead Logging", "isolation levels", "dirty reads", "Strict Two-Phase Locking"],
        "copilot_grounded_query": "What are the four ANSI SQL transaction isolation levels and what anomalies do they prevent?",
        "copilot_ungrounded_query": "How do you change a flat tire on a bicycle?"
    },
    {
        "id": "doc-10-db-normalization",
        "title": "Database Systems: Relational Normalization & Normal Forms",
        "subject": "Database Systems",
        "category": "Computer Science",
        "content": """Relational Database Design: Functional Dependencies and Normalization Theory.
Relational normalization is the formal mathematical process of decomposing tables with redundancy to minimize data anomalies: insertion anomalies (inability to add data without unrelated fields), deletion anomalies (unintended loss of facts when deleting tuples), and update anomalies (inconsistent partial updates).

Normalization relies on Functional Dependencies (FDs). An FD X -> Y specifies that attribute set X uniquely determines attribute set Y in relation R. Armstrong's Axioms—Reflexivity, Augmentation, and Transitivity—form a sound and complete inference system for computing functional dependency closures.

Normal forms establish progressive constraints:
- First Normal Form (1NF): Every attribute contains only atomic, indivisible values, with no repeating groups or composite columns.
- Second Normal Form (2NF): Relation is in 1NF and contains no partial functional dependencies; every non-prime attribute is fully functionally dependent on the entire primary key, not a proper subset of a composite primary key.
- Third Normal Form (3NF): Relation is in 2NF and contains no transitive functional dependencies; for every non-trivial FD X -> A, either X is a superkey, or A is a prime attribute.
- Boyce-Codd Normal Form (BCNF): A stricter variant of 3NF where for every non-trivial functional dependency X -> A, X must be a superkey without exception.""",
        "key_entities": ["normalization", "Functional Dependencies", "Armstrong's Axioms", "First Normal Form", "Second Normal Form", "Third Normal Form", "Boyce-Codd Normal Form", "superkey"],
        "copilot_grounded_query": "What is the difference between Third Normal Form (3NF) and Boyce-Codd Normal Form (BCNF)?",
        "copilot_ungrounded_query": "What is the meaning of life according to Douglas Adams?"
    },
    {
        "id": "doc-11-ai-transformers",
        "title": "Artificial Intelligence: Transformer Models & Self-Attention",
        "subject": "Artificial Intelligence & Deep Learning",
        "category": "Artificial Intelligence",
        "content": """Deep Learning Architectures: The Transformer and Self-Attention Mechanism.
Introduced by Vaswani et al. (2017) in 'Attention Is All You Need', the Transformer replaced recurrent architectures with attention mechanisms, enabling full parallelization across sequence tokens. The canonical architecture consists of an Encoder stack and Decoder stack.

The fundamental core of the Transformer is Scaled Dot-Product Attention. Input representations are linearly projected into three matrices: Queries Q of dimension dk, Keys K of dimension dk, and Values V of dimension dv. Attention weights are computed by taking the matrix product of queries and transposed keys, dividing by sqrt(dk), and applying a softmax activation:
Attention(Q, K, V) = softmax((Q * K^T) / sqrt(dk)) * V

The scaling factor 1 / sqrt(dk) is crucial: for large projection dimensions dk, dot products grow large in magnitude, pushing softmax functions into saturation regions with vanishingly small backpropagation gradients.

Multi-Head Attention projects Q, K, and V into h parallel subspace representations, executing scaled dot-product attention in parallel:
MultiHead(Q, K, V) = Concat(head_1, ..., head_h) * W^O
This enables the network to attend simultaneously to syntactic dependencies, semantic coreference, and positional context. Because Transformers lack recurrence and convolution, they are permutation invariant; Positional Encodings using sinusoidal functions are added directly to token embeddings to inject sequence order.""",
        "key_entities": ["Transformer", "Scaled Dot-Product Attention", "Queries", "Keys", "Values", "softmax", "Multi-Head Attention", "Positional Encodings"],
        "copilot_grounded_query": "Why does Scaled Dot-Product Attention divide the dot product by the square root of dk?",
        "copilot_ungrounded_query": "What is the plot of Hamlet?"
    },
    {
        "id": "doc-12-ai-backprop",
        "title": "Machine Learning: Gradient Descent & Backpropagation",
        "subject": "Machine Learning",
        "category": "Artificial Intelligence",
        "content": """Neural Network Optimization: Gradient Descent and Error Backpropagation.
Artificial Neural Networks learn continuous representations by optimizing parameter weights W and biases b to minimize an empirical loss function L (such as Mean Squared Error for regression or Categorical Cross-Entropy for classification).

Gradient Descent updates parameter vectors in the opposite direction of the loss function gradient:
theta_{t+1} = theta_t - alpha * nabla_theta L(theta_t)
where alpha is the learning rate hyperparameter. Batch Gradient Descent computes gradients across the entire training dataset; Stochastic Gradient Descent (SGD) updates parameters per individual example, introducing stochastic noise that assists in escaping shallow local minima; and Mini-batch SGD computes updates across batches (typically 32 to 512 samples), balancing computational efficiency on GPU tensor cores with gradient stability.

Backpropagation applies the multivariable chain rule of calculus to compute partial derivatives of loss L with respect to every weight in a multi-layer network. During the forward pass, layer activations are cached. During the backward pass, error terms delta are propagated backwards from the output layer to the input layer. Deep architectures frequently encounter the vanishing gradient problem when using saturating activation functions like Sigmoid or Tanh, where repeated chain multiplication of small derivatives approaches zero. Non-saturating activations like ReLU and adaptive optimizers like Adam mitigate this challenge.""",
        "key_entities": ["loss function", "Gradient Descent", "learning rate", "Stochastic Gradient Descent", "Backpropagation", "chain rule", "vanishing gradient", "ReLU"],
        "copilot_grounded_query": "What mathematical principle does backpropagation rely on to calculate gradients?",
        "copilot_ungrounded_query": "What is the recipe for chocolate chip cookies?"
    },
    {
        "id": "doc-13-bio-dna",
        "title": "Molecular Biology: DNA Replication & Polymerase Fidelity",
        "subject": "Molecular Biology",
        "category": "Life Sciences",
        "content": """Molecular Genetics: Mechanisms of Semiconservative DNA Replication.
DNA replication is the biological process by which a cell duplicates its genome prior to mitotic division. In 1958, the Meselson-Stahl experiment proved that DNA replicates semiconservatively: each daughter double helix consists of one original parental template strand and one newly synthesized nascent strand.

Replication initiates at specific genomic loci termed origins of replication. The enzyme DNA Helicase unzips the double-stranded DNA by breaking hydrogen bonds between complementary base pairs, creating a Y-shaped replication fork. Single-Stranded Binding Proteins (SSBs) stabilize unwound template strands, while DNA Topoisomerase (Gyrase) relieves supercoiling tension ahead of the fork.

Because DNA polymerases can only append nucleotides to an existing 3'-hydroxyl group, RNA Primase synthesizes short RNA primers. DNA Polymerase III synthesizes the leading strand continuously in the 5' to 3' direction toward the replication fork. The lagging strand is synthesized discontinuously away from the fork as a series of Okazaki fragments. DNA Polymerase I removes RNA primers with its 5' to 3' exonuclease activity and fills gaps with DNA nucleotides, after which DNA Ligase catalyzes phosphodiester bonds to seal nicks. High replication fidelity is maintained by DNA Polymerase III's 3' to 5' proofreading exonuclease activity, which detects and excises mismatched bases.""",
        "key_entities": ["semiconservative", "Meselson-Stahl", "DNA Helicase", "replication fork", "DNA Topoisomerase", "RNA Primase", "leading strand", "lagging strand", "Okazaki fragments", "DNA Ligase", "proofreading"],
        "copilot_grounded_query": "How is the lagging strand synthesized during DNA replication?",
        "copilot_ungrounded_query": "What is the square root of 256?"
    },
    {
        "id": "doc-14-bio-respiration",
        "title": "Cellular Biology: Cellular Respiration & ATP Synthase",
        "subject": "Cellular Biology",
        "category": "Life Sciences",
        "content": """Cellular Bioenergetics: Aerobic Respiration and Oxidative Phosphorylation.
Cellular respiration is the catabolic pathway by which heterotrophic organisms oxidize glucose to synthesize adenosine triphosphate (ATP), releasing carbon dioxide and water:
C6H12O6 + 6O2 -> 6CO2 + 6H2O + ~30-32 ATP.

Respiration proceeds through four stages:
1. Glycolysis: Occurs in the cell cytosol. One 6-carbon glucose molecule is broken down into two 3-carbon pyruvate molecules, yielding a net 2 ATP and 2 NADH without requiring oxygen.
2. Pyruvate Oxidation: Pyruvate enters the mitochondrial matrix via active transport, where the pyruvate dehydrogenase complex oxidizes it into Acetyl-CoA, releasing CO2 and producing NADH.
3. The Citric Acid Cycle (Krebs Cycle): In the mitochondrial matrix, Acetyl-CoA combines with 4-carbon oxaloacetate to form 6-carbon citrate. Two turns of the cycle oxidize two acetyl groups, generating 2 ATP, 6 NADH, 2 FADH2, and 4 CO2.
4. Oxidative Phosphorylation: High-energy electrons from NADH and FADH2 traverse four protein complexes (I, II, III, IV) embedded in the inner mitochondrial membrane. Electron transfer drives active pumping of protons (H+) from the matrix into the intermembrane space, generating a proton-motive force (pmf). As protons flow down their electrochemical gradient back into the matrix through ATP Synthase, rotary catalysis drives phosphorylation of ADP into ATP. Oxygen acts as the terminal electron acceptor, forming water.""",
        "key_entities": ["Cellular respiration", "Glycolysis", "mitochondrial matrix", "Krebs Cycle", "Oxidative Phosphorylation", "proton-motive force", "ATP Synthase", "terminal electron acceptor"],
        "copilot_grounded_query": "What role does oxygen play in the electron transport chain during cellular respiration?",
        "copilot_ungrounded_query": "Who was the sixteenth president of the United States?"
    },
    {
        "id": "doc-15-bio-photosynthesis",
        "title": "Plant Biology: Oxygenic Photosynthesis & Light Reactions",
        "subject": "Plant Biology",
        "category": "Life Sciences",
        "content": """Photosynthetic Metabolism: Light-Dependent and Light-Independent Reactions.
Photosynthesis is the autotrophic process by which green plants and algae convert light energy into chemical energy stored in carbohydrates:
6CO2 + 6H2O + Photons -> C6H12O6 + 6O2.
The process occurs within chloroplasts, partitioned into thylakoid membranes and the stroma.

1. Light-Dependent Reactions:
Embedded in thylakoid membranes, Photosystem II (P680) and Photosystem I (P700) contain chlorophyll pigments absorbing blue and red light while reflecting green light. In Photosystem II, photon excitation ejects high-energy electrons. Water molecules are split by the oxygen-evolving complex in photolysis:
2H2O -> 4H+ + 4e- + O2,
releasing oxygen gas. Electrons move through plastoquinone, the cytochrome b6f complex, and plastocyanin to Photosystem I, pumping protons into the thylakoid lumen. ATP Synthase utilizes this proton gradient to synthesize ATP. Photosystem I re-excites electrons, transferring them to ferredoxin-NADP+ reductase to reduce NADP+ into NADPH.

2. The Calvin Cycle (Light-Independent Reactions):
In the chloroplast stroma, the enzyme RuBisCO (Ribulose-1,5-bisphosphate carboxylase-oxygenase) catalyzes carbon fixation by binding CO2 to 5-carbon ribulose 1,5-bisphosphate (RuBP), forming 3-phosphoglycerate (3-PGA). ATP and NADPH reduce 3-PGA into glyceraldehyde-3-phosphate (G3P), from which glucose is synthesized, and RuBP is regenerated.""",
        "key_entities": ["Photosystem II", "Photosystem I", "photolysis", "cytochrome b6f", "Calvin Cycle", "RuBisCO", "carbon fixation", "RuBP", "glyceraldehyde-3-phosphate"],
        "copilot_grounded_query": "What enzyme catalyzes the carbon fixation stage of the Calvin cycle?",
        "copilot_ungrounded_query": "What is the average lifespan of a golden retriever?"
    },
    {
        "id": "doc-16-chem-substitution",
        "title": "Organic Chemistry: Nucleophilic Substitution Mechanisms",
        "subject": "Organic Chemistry",
        "category": "Physical Sciences",
        "content": """Mechanisms in Organic Chemistry: SN1 vs SN2 Nucleophilic Substitution.
Nucleophilic substitution reactions involve an electron-rich nucleophile attacking an electrophilic sp3-hybridized carbon atom bearing a leaving group. These reactions proceed through two distinct kinetic mechanisms:

The SN2 Mechanism (Substitution Nucleophilic Bimolecular) is a concerted, single-step reaction. The nucleophile attacks the electrophilic carbon from the backside—exactly 180 degrees opposite the leaving group—simultaneously as the carbon-leaving group bond breaks through a pentacoordinated transition state. Because of this backside attack, SN2 reactions proceed with complete inversion of stereochemical configuration (Walden Inversion). The reaction rate exhibits second-order kinetics: Rate = k[Substrate][Nucleophile]. Steric hindrance governs reactivity: methyl > primary (1 deg) > secondary (2 deg) >> tertiary (3 deg, unreactive). Polar aprotic solvents (such as DMSO, DMF, and acetone) favor SN2 by solvating cations without hydrogen-bonding to the nucleophile.

The SN1 Mechanism (Substitution Nucleophilic Unimolecular) is a stepwise, two-step reaction. In the rate-determining step, the leaving group departs spontaneously, forming a planar, sp2-hybridized carbocation intermediate. In the second step, the nucleophile attacks either face of the carbocation, yielding racemization. The reaction rate exhibits first-order kinetics: Rate = k[Substrate]. Substrate reactivity follows carbocation stability: tertiary (3 deg) > secondary (2 deg) >> primary (1 deg). Polar protic solvents (such as water and alcohols) stabilize ionic intermediates and accelerate SN1.""",
        "key_entities": ["SN2 Mechanism", "backside attack", "Walden Inversion", "second-order kinetics", "SN1 Mechanism", "carbocation intermediate", "racemization", "polar aprotic solvents", "polar protic solvents"],
        "copilot_grounded_query": "Why does the SN2 mechanism produce inversion of stereochemical configuration?",
        "copilot_ungrounded_query": "What is the highest mountain peak in Africa?"
    },
    {
        "id": "doc-17-phys-newton",
        "title": "Classical Mechanics: Newton's Laws & Momentum Conservation",
        "subject": "Physics",
        "category": "Physical Sciences",
        "content": """Classical Mechanics: Newton's Laws of Motion and Linear Momentum.
Isaac Newton formulated the foundations of classical mechanics in the 'Philosophiae Naturalis Principia Mathematica' (1687):
1. First Law (Law of Inertia): An object continues in a state of rest or uniform motion in a straight line unless acted upon by a non-zero net external force. Inertia is measured by inertial mass.
2. Second Law: The net external force acting on a body equals the time rate of change of its linear momentum:
F_net = dp/dt = d(mv)/dt.
When mass is constant, this reduces to the familiar equation F_net = ma.
3. Third Law (Action-Reaction): Whenever body A exerts a force on body B, body B simultaneously exerts an equal and opposite force on body A: F_{AB} = -F_{BA}. Action-reaction pairs act on different objects and therefore never cancel each other out.

Linear momentum is defined as p = mv. The Impulse-Momentum Theorem states that the impulse J of a force equals the change in momentum: J = integral F dt = delta p. In an isolated system experiencing zero net external force (F_ext = 0), total linear momentum is strictly conserved: p_initial = p_final. In elastic collisions, both total momentum and total kinetic energy are conserved; in inelastic collisions, total momentum is conserved, but kinetic energy is partially converted into internal thermal energy or deformation.""",
        "key_entities": ["Newton's Laws", "Law of Inertia", "linear momentum", "Action-Reaction", "Impulse-Momentum Theorem", "isolated system", "elastic collisions", "inelastic collisions"],
        "copilot_grounded_query": "What is the physical distinction between elastic and inelastic collisions regarding energy conservation?",
        "copilot_ungrounded_query": "Who painted the Mona Lisa?"
    },
    {
        "id": "doc-18-phys-thermo",
        "title": "Thermodynamics: Laws of Thermodynamics & Carnot Engine",
        "subject": "Thermodynamics",
        "category": "Physical Sciences",
        "content": """Macroscopic Physics: The Four Laws of Thermodynamics and Heat Engines.
Thermodynamics describes macroscopic transformations of thermal energy, mechanical work, and state variables.
The Zeroth Law establishes that if systems A and B are in thermal equilibrium with system C, they are in thermal equilibrium with each other.
The First Law enforces conservation of energy, where internal energy change equals heat absorbed minus work performed.
The Second Law states that the total entropy of an isolated thermodynamic system never decreases over irreversible processes.
The Kelvin-Planck statement asserts that no cyclic heat engine can convert absorbed thermal energy entirely into mechanical work.
The Third Law dictates that the entropy of a pure crystalline substance approaches a universal constant minimum at absolute zero.
Nicolas Sadi Carnot proved that the maximum theoretical efficiency of a reversible heat engine operating between hot reservoir T_H and cold reservoir T_C is given by eta = 1 - (T_C / T_H).
No physical heat engine can exceed the theoretical upper bound established by the Carnot cycle efficiency theorem.""",
        "key_entities": ["Zeroth Law", "First Law", "state function", "Second Law", "entropy", "Kelvin-Planck", "Third Law", "Carnot cycle", "thermal efficiency"],
        "copilot_grounded_query": "What is the formula for the maximum theoretical efficiency of a Carnot heat engine?",
        "copilot_ungrounded_query": "What is the capital of Canada?"
    },
    {
        "id": "doc-19-math-linear",
        "title": "Linear Algebra: Matrix Eigenvalues & Diagonalization",
        "subject": "Mathematics",
        "category": "Formal Sciences",
        "content": """Advanced Linear Algebra: Spectral Theory, Eigenvalues, and Diagonalization.
Let A be an n x n square matrix over field R or C. A non-zero vector v is an eigenvector of A with corresponding eigenvalue lambda if the linear transformation scales v without changing its direction:
A * v = lambda * v, or equivalently (A - lambda * I) * v = 0.

For non-trivial eigenvector solutions to exist, the matrix (A - lambda * I) must be singular, meaning its determinant must equal zero. This yields the Characteristic Polynomial:
p(lambda) = det(A - lambda * I) = 0.
The roots of the characteristic polynomial are the eigenvalues of A. The algebraic multiplicity of an eigenvalue is its multiplicity as a root of p(lambda); the geometric multiplicity is the dimension of its eigenspace, nullity(A - lambda * I). The geometric multiplicity never exceeds algebraic multiplicity.

A matrix A is diagonalizable if there exists an invertible matrix P and diagonal matrix D such that A = P * D * P^(-1). A square matrix of size n is diagonalizable if and only if it possesses n linearly independent eigenvectors, which occurs when the geometric multiplicity of each eigenvalue equals its algebraic multiplicity. The Spectral Theorem for real symmetric matrices states that every real symmetric matrix has real eigenvalues and is orthogonally diagonalizable: A = Q * D * Q^T, where Q is an orthogonal matrix whose columns form an orthonormal basis of eigenvectors.""",
        "key_entities": ["eigenvector", "eigenvalue", "Characteristic Polynomial", "algebraic multiplicity", "geometric multiplicity", "diagonalizable", "Spectral Theorem", "symmetric matrix"],
        "copilot_grounded_query": "Under what condition is an n x n matrix guaranteed to be diagonalizable?",
        "copilot_ungrounded_query": "How many millimeters are in one kilometer?"
    },
    {
        "id": "doc-20-law-constitutional",
        "title": "Constitutional Law: Separation of Powers & Judicial Review",
        "subject": "Constitutional Law",
        "category": "Legal Studies",
        "content": """Constitutional Jurisprudence: Institutional Separation of Powers and Judicial Review.
The doctrine of the separation of powers, developed theoretically by Baron de Montesquieu in 'The Spirit of the Laws' (1748), posits that tyrannical governance is avoided by dividing sovereign state power into three distinct branches: the Legislative (law-making), the Executive (law-enforcing), and the Judicial (law-interpreting).

Under the United States Constitution, this functional separation is secured through an interdependent system of checks and balances. Article I vests legislative powers in Congress, subject to Presidential veto, which Congress may override by a two-thirds majority in both chambers. Article II vests executive authority in the President, subject to the Senate's power of Advice and Consent on judicial nominations and treaties, as well as congressional impeachment. Article III vests judicial power in the Supreme Court and inferior federal courts, with judges holding tenure during good behavior.

The cornerstone doctrine of American constitutional jurisprudence is Judicial Review: the authority of courts to invalidate statutes and executive actions that violate constitutional provisions. In the landmark decision Marbury v. Madison (1803), Chief Justice John Marshall established judicial review, writing: 'It is emphatically the province and duty of the judicial department to say what the law is.' Marshall reasoned that because the Constitution is the supreme law of the land, an act of the legislature repugnant to the Constitution is void.""",
        "key_entities": ["separation of powers", "Montesquieu", "Legislative", "Executive", "Judicial", "checks and balances", "veto", "Article III", "Judicial Review", "Marbury v. Madison", "John Marshall"],
        "copilot_grounded_query": "Which landmark supreme court case established the doctrine of judicial review in the United States?",
        "copilot_ungrounded_query": "What is the boiling temperature of olive oil?"
    }
]
