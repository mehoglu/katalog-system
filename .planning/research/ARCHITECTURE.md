# Architecture Patterns for Agent-Based Data Processing Systems

**Domain:** LLM-powered product catalog generation with web UI
**Researched:** 25. März 2026
**Confidence:** MEDIUM (based on established patterns in agent-based systems, no project-specific external research conducted)

## Recommended Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                       Web Frontend                           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │  Upload  │  │  Review  │  │  Edit    │  │ Preview  │   │
│  │  Page    │  │  Table   │  │  Mapping │  │  Catalog │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└────────────┬─────────────────────────────────────┬──────────┘
             │ HTTP/API                       │ WebSocket
             ↓                                     ↓
┌─────────────────────────────────────────────────────────────┐
│                     Backend API Layer                        │
│  ┌──────────────┐  ┌───────────────┐  ┌──────────────┐    │
│  │ Upload       │  │ Processing    │  │ Generation   │    │
│  │ Controller   │  │ Controller    │  │ Controller   │    │
│  └──────────────┘  └───────────────┘  └──────────────┘    │
└────────────┬─────────────────────────────────────┬──────────┘
             │                                      │
             ↓                                      ↓
┌─────────────────────────────────────────────────────────────┐
│               Agent Orchestration Layer                      │
│  ┌────────────────────────────────────────────────────┐    │
│  │          Agent Coordinator/Orchestrator            │    │
│  └────────────────────────────────────────────────────┘    │
│  ┌──────────┐  ┌───────────┐  ┌──────────┐  ┌────────┐   │
│  │   CSV    │  │  Mapping  │  │  Text    │  │ Image  │   │
│  │ Analyzer │  │  Merger   │  │ Refiner  │  │ Linker │   │
│  │  Agent   │  │  Agent    │  │  Agent   │  │ Agent  │   │
│  └──────────┘  └───────────┘  └──────────┘  └────────┘   │
└────────────┬─────────────────────────────────────┬──────────┘
             │                                      │
             ↓                                      ↓
┌─────────────────────────────────────────────────────────────┐
│                  Service/Utility Layer                       │
│  ┌──────────┐  ┌───────────┐  ┌──────────┐  ┌────────┐   │
│  │   CSV    │  │  Template │  │  File    │  │  LLM   │   │
│  │  Parser  │  │  Engine   │  │  Manager │  │ Client │   │
│  └──────────┘  └───────────┘  └──────────┘  └────────┘   │
└────────────┬─────────────────────────────────────┬──────────┘
             │                                      │
             ↓                                      ↓
┌─────────────────────────────────────────────────────────────┐
│                    Storage Layer                             │
│  ┌──────────┐  ┌───────────┐  ┌──────────┐  ┌────────┐   │
│  │  Files   │  │  Mapping  │  │  Images  │  │ Output │   │
│  │  (CSV)   │  │  DB/JSON  │  │  (Disk)  │  │  HTML  │   │
│  └──────────┘  └───────────┘  └──────────┘  └────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### Component Boundaries

| Component | Responsibility | Communicates With | Data Flow |
|-----------|---------------|-------------------|-----------|
| **Web Frontend** | User interaction, file uploads, data visualization | Backend API via REST/GraphQL | Sends CSV/images → Receives processed data, HTML previews |
| **Backend API** | Request handling, validation, job coordination | Agent Orchestrator, Storage | Routes requests → Monitors jobs → Returns results |
| **Agent Orchestrator** | Workflow coordination, agent lifecycle, state management | Individual Agents, LLM Client | Distributes tasks → Collects results → Manages dependencies |
| **CSV Analyzer Agent** | Column detection, semantic analysis, structure mapping | LLM Client, Mapping DB | Raw CSV → Structured schema understanding |
| **Mapping Merger Agent** | Data joining across sources, conflict resolution | LLM Client, Mapping DB | Multiple CSVs → Unified product records |
| **Text Refiner Agent** | Product text improvement, German language optimization | LLM Client | Raw product names → Polished descriptions |
| **Image Linker Agent** | Article number-based image assignment | File Manager | Product IDs + Image directory → Image-product associations |
| **Template Engine** | HTML generation from structured data | Product data, Images | Product records → HTML files (per-product + catalog) |
| **Mapping Store** | Persistence of learned CSV patterns | Backend API, Agents | Stores/retrieves column mappings |
| **File Manager** | CSV storage, image handling, output management | Backend API, Agents | Manages upload/processing/output lifecycle |

### Data Flow

**Primary Processing Pipeline:**

```
User Upload (CSV + Images)
    ↓
Backend validates & stores
    ↓
Agent Orchestrator spawns CSV Analyzer Agent
    ↓
CSV Analyzer → LLM → Column semantics identified
    ↓
Mapping Merger Agent → Joins data from both CSVs by article number
    ↓
Text Refiner Agent → LLM → Improves product descriptions (German)
    ↓
Image Linker Agent → Matches images to article numbers
    ↓
Merged product records written to intermediate storage
    ↓
Template Engine → Renders HTML (per-product + full catalog)
    ↓
Output delivered to user (preview/download)
```

**Feedback/Correction Flow:**

```
User views mapped data in table UI
    ↓
User edits incorrect mappings
    ↓
Backend updates mapping store
    ↓
User triggers re-generation
    ↓
Template Engine re-runs with corrected data
    ↓
New HTML output generated
```

## Architectural Patterns

### Pattern 1: Multi-Agent System (MAS)

**What:** Multiple specialized AI agents coordinate to solve complex tasks. Each agent has a specific domain (CSV analysis, text refinement, etc.).

**When to use:** When tasks require different types of reasoning or domain expertise. Ideal for this project because CSV structure analysis, data merging, and text improvement are distinct concerns.

**Trade-offs:**
- **Pros:** Clear separation of concerns, agents can be improved independently, easier debugging per agent
- **Cons:** Coordination complexity, potential for inter-agent communication overhead, need for robust orchestration

**Example Architecture:**
```typescript
// Agent interface
interface Agent {
  name: string;
  execute(context: AgentContext): Promise<AgentResult>;
}

// CSV Analyzer Agent
class CSVAnalyzerAgent implements Agent {
  async execute(context: AgentContext): Promise<AgentResult> {
    const csvContent = context.input.csv;
    const prompt = `Analyze this CSV structure and identify column meanings...`;
    const analysis = await llm.complete(prompt);
    return {
      schema: analysis.schema,
      columnMappings: analysis.mappings
    };
  }
}

// Orchestrator
class AgentOrchestrator {
  async runPipeline(csvFiles: File[], images: File[]) {
    // Sequential agent execution with dependency management
    const analysis = await analyzerAgent.execute({ input: csvFiles });
    const merged = await mergerAgent.execute({ input: analysis });
    const refined = await refinerAgent.execute({ input: merged });
    const linked = await imageAgent.execute({ input: { products: refined, images } });
    return linked;
  }
}
```

### Pattern 2: Event-Driven Pipeline

**What:** Processing steps communicate through events/messages. Each stage processes data and emits events for the next stage.

**When to use:** When you want loose coupling, async processing, and ability to scale individual stages independently.

**Trade-offs:**
- **Pros:** Scalable, components decoupled, easy to add new processing steps, good for long-running tasks
- **Cons:** Harder to debug, eventual consistency, requires message queue infrastructure

**Example:**
```typescript
// Event bus pattern
class ProcessingPipeline {
  on(event: 'csv-analyzed', handler: (data) => void);
  on(event: 'data-merged', handler: (data) => void);
  on(event: 'text-refined', handler: (data) => void);
  
  async start(uploadId: string) {
    this.emit('upload-received', { uploadId });
    // Pipeline stages listen and emit events
  }
}
```

**For this project:** MEDIUM fit. Good for handling 500+ products asynchronously, but adds complexity. Consider for production scaling, but start with simpler orchestration.

### Pattern 3: Repository Pattern with Agent Services

**What:** Traditional layered architecture with agents as specialized services. Controllers call agent services, which interact with repositories for data persistence.

**When to use:** When you want familiar web architecture patterns but need AI capabilities. Good for teams experienced with MVC/layered architectures.

**Trade-offs:**
- **Pros:** Familiar to web developers, easy to understand, straightforward testing, clear data flow
- **Cons:** Less flexibility for complex agent interactions, agents feel more like "smart services" than autonomous entities

**Example:**
```typescript
class ProductController {
  constructor(
    private csvAnalyzer: CSVAnalyzerService,
    private dataMerger: DataMergerService,
    private textRefiner: TextRefinerService,
    private catalogGenerator: CatalogGeneratorService
  ) {}
  
  async processCatalog(req, res) {
    const csvFiles = req.files.csvFiles;
    const images = req.files.images;
    
    // Sequential service calls
    const schema = await this.csvAnalyzer.analyzeStructure(csvFiles);
    const products = await this.dataMerger.merge(csvFiles, schema);
    const refined = await this.textRefiner.improveGerman(products);
    const catalog = await this.catalogGenerator.generate(refined, images);
    
    res.json({ catalogId: catalog.id });
  }
}
```

**For this project:** HIGH fit. Simpler to implement initially, fits web development conventions, easier to add mapping correction UI.

### Pattern 4: Function/Tool Calling Architecture

**What:** Agents use LLM function calling to dynamically select and execute tools (parsers, databases, APIs) based on context.

**When to use:** When agents need to autonomously decide which tools to use. Best for exploratory or conversational workflows.

**Trade-offs:**
- **Pros:** Very flexible, agents can adapt to unexpected scenarios, minimal hard-coded logic
- **Cons:** Less predictable, harder to guarantee consistent behavior, potential for infinite loops or expensive LLM calls

**Example:**
```typescript
const tools = [
  {
    name: "parse_csv",
    description: "Parse and analyze CSV structure",
    parameters: { csvPath: "string" }
  },
  {
    name: "merge_data",
    description: "Merge data from two CSVs by key",
    parameters: { csv1: "object", csv2: "object", key: "string" }
  }
];

// Agent decides which tool to use
const response = await llm.complete({
  messages: [{ role: "user", content: "Process these two CSVs..." }],
  tools,
  tool_choice: "auto"
});
```

**For this project:** LOW-MEDIUM fit. Useful for CSV structure analysis where column names vary, but adds unpredictability. Use selectively for analysis phase only.

## Data Flow Patterns

### Sequential Pipeline (Recommended for MVP)

```
Upload → Store Files → CSV Analysis → Data Merge → Text Refinement → Image Linking → HTML Generation → Serve Output
```

**Characteristics:**
- Each step completes before next begins
- Clear error handling at each stage
- Easy to show progress (6 distinct steps)
- State stored after each stage (allows correction/retry)

**Implementation:**
```typescript
async function processCatalog(uploadId: string) {
  const job = await jobTracker.create(uploadId);
  
  try {
    // Step 1: Analyze CSV structures
    await job.updateProgress(0, "Analyzing CSV structures...");
    const schema = await analyzeCSVs(uploadId);
    await job.save({ schema });
    
    // Step 2: Merge data
    await job.updateProgress(20, "Merging product data...");
    const products = await mergeData(uploadId, schema);
    await job.save({ products });
    
    // Step 3: Refine text
    await job.updateProgress(40, "Improving product descriptions...");
    const refined = await refineText(products);
    await job.save({ refined });
    
    // Step 4: Link images
    await job.updateProgress(60, "Linking product images...");
    const withImages = await linkImages(refined, uploadId);
    await job.save({ withImages });
    
    // Step 5: Generate HTML
    await job.updateProgress(80, "Generating catalog HTML...");
    const htmlFiles = await generateHTML(withImages);
    
    await job.complete(htmlFiles);
  } catch (error) {
    await job.fail(error);
  }
}
```

### Parallel Processing (For Production Scale)

For 500+ products, parallelize within stages where possible:

```
CSV Analysis (once per file)
    ↓
Data Merge (once)
    ↓
Text Refinement (parallel batches of 10 products)
    ↓
Image Linking (parallel per product)
    ↓
HTML Generation (parallel per product + 1 catalog index)
```

**Implementation consideration:**
```typescript
// Batch processing for LLM calls
async function refineTextBatch(products: Product[]): Promise<Product[]> {
  const batchSize = 10;
  const batches = chunk(products, batchSize);
  
  const results = await Promise.all(
    batches.map(batch => llm.refineProductTexts(batch))
  );
  
  return results.flat();
}
```

### State Persistence Pattern

Store intermediate results for correction workflow:

```
.data/
  jobs/
    {uploadId}/
      raw/              # Original CSV and images
        preisliste.csv
        edi-export.csv
        bilder/
      intermediate/     # Processing results
        schema.json     # CSV analysis results
        products.json   # Merged product data
        mappings.json   # User-correctable mappings
      output/           # Generated files
        produkt-001.html
        produkt-002.html
        katalog.html
```

## Scaling Considerations

| Concern | At 10 Products (Dev) | At 500 Products (Target) | At 5000 Products (Future) |
|---------|---------------------|-------------------------|--------------------------|
| **Processing Time** | Sequential (< 1 min) | Sequential acceptable (5-10 min) | Parallel batches required (10-15 min) |
| **LLM Costs** | ~$0.10 per run | ~$5 per run | ~$50 per run; consider caching, cheaper models for some tasks |
| **Storage** | Local filesystem | Local filesystem | Consider S3/cloud storage |
| **Concurrency** | Single job at a time | Queue multiple uploads | Worker pool pattern |
| **Memory** | Load all in memory | Load all in memory | Stream processing for CSVs |
| **Error Recovery** | Retry from start | Resume from last checkpoint | Partial retry per stage |

## Anti-Patterns to Avoid

### Anti-Pattern 1: Fully Autonomous Agent Without Guardrails

**What:** Letting agents make all decisions without constraints or validation.

**Why bad:** 
- Unpredictable costs (agents might call LLM in loops)
- Inconsistent output quality
- Hard to debug when things go wrong
- May "hallucinate" CSV column meanings

**Instead:** 
- Use guided prompts with clear expected outputs
- Validate agent outputs with schemas (Zod, JSON Schema)
- Set maximum retry limits
- Implement confidence scoring for agent decisions

```typescript
// BAD: Open-ended agent
const result = await agent.run("Figure out what these CSVs mean and merge them");

// GOOD: Constrained agent with validation
const schema = z.object({
  columns: z.array(z.object({
    name: z.string(),
    type: z.enum(['product_id', 'price', 'description', 'dimension']),
    confidence: z.number().min(0).max(1)
  }))
});

const result = await agent.analyzeCSV(csv, { expectedSchema: schema, maxRetries: 2 });
if (result.confidence < 0.8) {
  // Flag for human review
}
```

### Anti-Pattern 2: Synchronous Processing Without Progress Feedback

**What:** Blocking the web request while processing 500 products.

**Why bad:**
- HTTP timeouts (most servers have 30-60s limits)
- Poor UX (user sees loading spinner for minutes)
- If anything fails, user loses all progress

**Instead:**
- Use background jobs with progress tracking
- Return job ID immediately, poll for status
- Or use WebSocket for real-time updates

```typescript
// BAD: Synchronous
app.post('/process-catalog', async (req, res) => {
  const result = await processCatalog(req.files); // Takes 10 minutes
  res.json(result);
});

// GOOD: Async with job tracking
app.post('/process-catalog', async (req, res) => {
  const jobId = await jobs.create(req.files);
  res.json({ jobId, status: 'processing' });
});

app.get('/job-status/:jobId', async (req, res) => {
  const status = await jobs.getStatus(req.params.jobId);
  res.json(status); // { progress: 60, step: 'refining text' }
});
```

### Anti-Pattern 3: No Intermediate State Persistence

**What:** Processing all 500 products in memory without saving progress.

**Why bad:**
- If process crashes at 95%, start from scratch
- Can't implement correction workflow (no saved mappings to edit)
- Hard to debug (can't inspect intermediate results)

**Instead:**
- Save results after each major stage
- Store mappings separately so users can edit them
- Enable "re-run from stage X" functionality

### Anti-Pattern 4: Storing Everything in Relational DB

**What:** Using PostgreSQL/MySQL to store CSV contents, intermediate JSON blobs, generated HTML.

**Why bad:**
- Relational DBs not optimized for large blobs
- Harder to version/snapshot processing results
- Unnecessary complexity for single-user system

**Instead:**
- Use filesystem for file-based artifacts (CSVs, images, HTML)
- Use lightweight JSON/SQLite for structured data (mappings, metadata)
- Only use DB if multi-user features added later

## Integration Points

### LLM Provider Integration

**Recommended Approach:**
- Abstract LLM calls behind interface
- Support multiple providers (OpenAI, Anthropic, local models)
- Implement retry logic and rate limiting
- Cache common analyses (standard column names)

```typescript
interface LLMProvider {
  complete(prompt: string, options?: CompletionOptions): Promise<string>;
  embeddings(text: string): Promise<number[]>;
}

class OpenAIProvider implements LLMProvider { /**/ }
class AnthropicProvider implements LLMProvider { /**/ }
class LocalModelProvider implements LLMProvider { /**/ }

// Usage
const llm: LLMProvider = createProvider(process.env.LLM_PROVIDER);
```

### Template Engine Integration

**Options:**
1. **Handlebars/Mustache** - Simple variable substitution
2. **Pug/EJS** - More logic in templates
3. **React/Vue SSR** - Component-based, overkill for this use case
4. **Template literals** - Simplest for MVP

**Recommendation:** Start with template literals for MVP, migrate to Handlebars if complexity increases.

```typescript
// Simple template literal approach
function generateProductHTML(product: Product): string {
  return `
<!DOCTYPE html>
<html>
  <head>
    <title>${product.name}</title>
    <style>${catalogStyles}</style>
  </head>
  <body>
    <div class="product">
      <h1>${product.name}</h1>
      <p>${product.description}</p>
      <div class="images">
        ${product.images.map(img => `<img src="${img}" />`).join('')}
      </div>
      <div class="specs">
        <dl>
          <dt>Artikelnummer</dt><dd>${product.articleNumber}</dd>
          <dt>Preis</dt><dd>${product.price}</dd>
        </dl>
      </div>
    </div>
  </body>
</html>
  `.trim();
}
```

### File System Organization

```
project-root/
├── uploads/              # Temporary upload storage
│   └── {sessionId}/
│       ├── preisliste.csv
│       ├── edi-export.csv
│       └── bilder/
├── data/                 # Persistent processing data
│   └── jobs/
│       └── {jobId}/
│           ├── schema.json
│           ├── products.json
│           ├── mappings.json  # User-editable
│           └── metadata.json
├── output/               # Generated HTML files
│   └── {jobId}/
│       ├── index.html          # Full catalog
│       └── produkte/
│           ├── produkt-001.html
│           └── produkt-002.html
└── cache/                # Optional: mapping templates cache
    └── learned-mappings.json
```

## Technology Stack Implications

### Backend Framework

**Options:**
1. **Node.js + Express** - Simple, good for MVP, large ecosystem
2. **Python + FastAPI** - Native ML/AI library support, type hints
3. **Next.js API Routes** - Unified frontend/backend, good DX

**Recommendation:** **Next.js** or **FastAPI**
- Next.js if team is TypeScript/React-focused (unified codebase)
- FastAPI if Python ecosystem preferred (more AI libraries)

### Agent Framework

**Options:**
1. **LangChain** - Comprehensive, many integrations, JavaScript + Python
2. **LangGraph** - State machine approach, good for complex flows
3. **Custom** - Full control, minimal dependencies

**Recommendation:** **Custom orchestration for MVP, LangChain if complexity grows**
- For this project's linear pipeline, custom orchestration is simpler
- LangChain adds value when agents need complex tool use or loops

### State Management

**Options:**
1. **Filesystem JSON** - Simple, version-friendly, sufficient for single-user
2. **SQLite** - Structured queries, ACID guarantees, still file-based
3. **PostgreSQL** - Overkill unless planning multi-user features

**Recommendation:** **Filesystem JSON for MVP**
- Maps to job-based structure naturally
- Easy to inspect/debug
- Version control friendly
- Migrate to SQLite if query complexity increases

## Build Order Recommendations

### Phase 1: Foundation (Backend Core)
**Goal:** Basic file handling and storage structure

**Components:**
1. File upload endpoint (Express/FastAPI)
2. Filesystem job structure
3. Basic CSV parser (Papa Parse / pandas)
4. Job status tracking

**Why first:** Establishes data flow foundation, no AI dependencies yet.

### Phase 2: CSV Analysis Agent
**Goal:** Understand CSV structures automatically

**Components:**
1. LLM client abstraction
2. CSV Analyzer agent (structure detection)
3. Schema storage
4. Confidence scoring

**Why second:** Core differentiator, needed before processing can continue.

### Phase 3: Data Merging
**Goal:** Join data from multiple sources

**Components:**
1. Mapping Merger agent
2. Conflict resolution logic
3. Article number-based joining
4. Merged product storage

**Why third:** Depends on schema from Phase 2, foundational for output.

### Phase 4: Web UI (Upload + Review)
**Goal:** User can upload files and see results

**Components:**
1. Upload page (drag-drop or file selection)
2. Job status page (progress bar)
3. Data review table (mapped products)
4. Basic routing

**Why fourth:** Makes system usable, reveals UX needs early.

### Phase 5: Text Refinement
**Goal:** Improve product descriptions

**Components:**
1. Text Refiner agent
2. German language optimization prompts
3. Batch processing for efficiency

**Why fifth:** Adds value but system works without it, can be refined iteratively.

### Phase 6: Image Linking
**Goal:** Associate images with products

**Components:**
1. Image Linker agent
2. Filename parsing (article number extraction)
3. Multiple images per product support

**Why sixth:** Independent from text processing, straightforward logic.

### Phase 7: HTML Generation
**Goal:** Create catalog output

**Components:**
1. Template engine setup
2. Per-product HTML generator
3. Full catalog index generator
4. CSS styling (modern, A4-ready)

**Why seventh:** All data is ready, just needs rendering. Can iterate on design.

### Phase 8: Mapping Correction UI
**Goal:** User can fix wrong mappings

**Components:**
1. Editable table component
2. Mapping update endpoint
3. Re-generation trigger
4. Diff view (before/after)

**Why eighth:** Depends on users seeing actual results to know what to correct.

### Phase 9: Mapping Persistence
**Goal:** Learn from corrections

**Components:**
1. Mapping template storage
2. Pattern matching for known CSVs
3. Confidence scoring on re-use

**Why ninth:** Optimization, system works without it, but improves over time.

## Sources

**Primary Sources:**
- Training data knowledge of LangChain/LangGraph architecture patterns (HIGH confidence)
- Common web application architecture patterns (HIGH confidence)
- Multi-agent system (MAS) design principles from AI literature (HIGH confidence)

**Limitations:**
- No external web research conducted (Brave API unavailable)
- No Context7 or official documentation queried for specific libraries
- Patterns derived from general knowledge of agent-based systems, not project-specific research

**Confidence Assessment:**
- **Architecture patterns:** HIGH - Standard patterns well-established in industry
- **Agent orchestration:** MEDIUM-HIGH - Based on common LangChain/ReAct patterns but not verified against latest (2026) best practices  
- **Technology recommendations:** MEDIUM - Based on 2024-2025 ecosystem knowledge, may not reflect 2026 updates
- **Build order:** HIGH - Logical dependency analysis based on component interactions

**Recommendation:** Validate specific library choices (LangChain version, Next.js vs FastAPI) with current documentation before implementation.
