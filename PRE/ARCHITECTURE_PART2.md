# COMPREHENSIVE SYSTEM ARCHITECTURE - PART 2
# Continuation: Visualization, Database, API Reference, Examples

**This is a continuation of ARCHITECTURE.md. Read that file first.**

---

## CONVERSATION MANAGEMENT SYSTEM (Continued)

### Memory Management Strategy

**Problem**: Long conversations can consume excessive memory with large DataFrames.

**Solution**: Multi-level cleanup

```python
# Level 1: Automatic Data Context Cleanup
def add_data_context(self, context: DataContext):
    self.data_contexts.append(context)
    if len(self.data_contexts) > 10:  # Keep only last 10
        self.data_contexts = self.data_contexts[-10:]

# Level 2: DataFrame Snapshot (Not Full DF)
dataframe_snapshot = {
    "columns": list(df.columns),
    "row_count": len(df),
    "sample": df.head(50).to_dict()  # Only first 50 rows
}

# Level 3: Manual Cleanup (if needed)
conversation_state.clear_old_contexts(max_keep=3)
```

**Memory Footprint**:
- Full DataFrame (10,000 rows): ~2-5 MB
- Snapshot (50 rows): ~100-200 KB
- **Savings**: 95%+ reduction

---

## VISUALIZATION PIPELINE

### Decision Tree for Visualization

```
User Question
    ↓
┌─────────────────────────────────────┐
│ Contains viz keywords?              │
│ (chart, plot, graph, visualize...)  │
└─────────────────────────────────────┘
    │
    ├─ NO → should_visualize = False
    │        (No visualization created)
    │
    └─ YES
        ↓
┌─────────────────────────────────────┐
│ Check Data Suitability              │
│ • df.empty? → NO viz                │
│ • len(df) < 2? → NO viz             │
│ • No numeric columns? → NO viz       │
└─────────────────────────────────────┘
        ↓
┌─────────────────────────────────────┐
│ LLM Analyzes Data Structure         │
│ Input:                              │
│ • Question                          │
│ • Column names & types              │
│ • Sample data (5 rows)              │
│                                     │
│ Output: VisualizationResponse       │
│ • Chart type recommendation         │
│ • Axis assignments                  │
│ • Color/grouping column             │
│ • Title suggestion                  │
│ • Rationale                         │
└─────────────────────────────────────┘
        ↓
┌─────────────────────────────────────┐
│ Column Resolution                   │
│ • Resolve column names              │
│ • Handle case insensitivity         │
│ • Apply fallbacks if needed         │
└─────────────────────────────────────┘
        ↓
┌─────────────────────────────────────┐
│ Chart Creation (Plotly)             │
│ • Build figure based on type        │
│ • Configure styling                 │
│ • Add interactivity                 │
│ • Return go.Figure object           │
└─────────────────────────────────────┘
        ↓
┌─────────────────────────────────────┐
│ Serialize & Store                   │
│ • Convert to JSON: fig.to_json()    │
│ • Store in Message.figure_json      │
│ • Save to conversation file         │
└─────────────────────────────────────┘
```

### Chart Type Selection Logic

#### Bar Chart
**When**: Comparing values across categories
```python
Indicators:
• Question contains: "compare", "each", "by category"
• Data has: 1 categorical + 1 numeric column
• Row count: 2-100 optimal

Example Question: "Show sales by region"
```

#### Line Chart
**When**: Showing trends over time
```python
Indicators:
• Question contains: "trend", "over time", "change"
• Data has: date/time column + numeric column
• Rows ordered by date

Example Question: "How have sales changed over months?"
```

#### Pie Chart
**When**: Showing part-to-whole relationships
```python
Indicators:
• Question contains: "percentage", "proportion", "share"
• Data has: categorical + 1 numeric (usually sum/count)
• Limited categories (<10 for readability)

Example Question: "What's the percentage of sales by category?"

Special Handling:
• Auto-limit to top 10 if more categories exist
• Explode largest slice (optional)
```

#### Box Plot
**When**: Analyzing distributions and outliers
```python
Indicators:
• Question contains: "distribution", "range", "outliers"
• Data has: categorical grouping + numeric values
• Multiple values per category (≥4 for box)

Example Question: "Show profit margin distribution by category"

Requirements:
• Each category must have ≥4 data points
• Falls back to bar chart if insufficient data
```

#### Scatter Plot
**When**: Exploring relationships between two numeric variables
```python
Indicators:
• Question contains: "relationship", "correlation"
• Data has: 2+ numeric columns

Example Question: "Is there a relationship between price and quantity?"
```

#### Histogram
**When**: Showing frequency distribution of a single variable
```python
Indicators:
• Question contains: "frequency", "distribution"
• Data has: 1 numeric column

Example Question: "Show the distribution of order amounts"
```

### Plotly Styling Standards

All charts use consistent styling for professional appearance:

```python
fig.update_layout(
    # Theme
    template="plotly",
    
    # Title
    title={
        "text": title,
        "font": {"size": 16, "family": "Arial, sans-serif"}
    },
    
    # Dimensions
    height=500,
    width=None,  # Auto-responsive
    
    # Grid
    xaxis=dict(
        showgrid=True,
        gridwidth=1,
        gridcolor='LightGray'
    ),
    yaxis=dict(
        showgrid=True,
        gridwidth=1,
        gridcolor='LightGray'
    ),
    
    # Legend
    showlegend=True,
    legend=dict(
        orientation="v",
        yanchor="top",
        y=0.99,
        xanchor="left",
        x=1.01,
        bgcolor="rgba(255, 255, 255, 0.8)",
        bordercolor="rgba(0, 0, 0, 0.2)",
        borderwidth=1
    ),
    
    # Interaction
    hovermode='closest'
)
```

### Visualization Preservation

**Challenge**: Plotly figures are complex objects that can't be directly serialized to JSON.

**Solution**: Use `fig.to_json()` and `go.Figure(json.loads(...))`

```python
# Save
figure_json = fig.to_json()
message.figure_json = figure_json

# Load
fig = go.Figure(json.loads(message.figure_json))
history.append((None, gr.Plot(value=fig)))
```

**JSON Structure** (abbreviated):
```json
{
  "data": [
    {
      "type": "bar",
      "x": ["Cat1", "Cat2", "Cat3"],
      "y": [10, 20, 15],
      "marker": {"color": "#636efa"}
    }
  ],
  "layout": {
    "title": {"text": "My Chart"},
    "xaxis": {"title": {"text": "Category"}},
    "yaxis": {"title": {"text": "Value"}},
    "template": "plotly"
  }
}
```

---

## DATABASE & VECTOR STORAGE

### SQLite Database Structure

**Source Database** (`analysis.db`):
- User's business data tables
- No modifications made during queries (read-only)
- Standard SQLite features: PRAGMA, indexes, transactions

**Schema Discovery**:
```python
# Get all user tables
SELECT name FROM sqlite_master 
WHERE type='table' AND name NOT LIKE 'sqlite_%'

# Get table schema
PRAGMA table_info('table_name')
# Returns: (cid, name, type, notnull, dflt_value, pk)
```

### ChromaDB Vector Database

**Location**: `./chroma_db_768dim/` directory

**Collections**:

1. **table_metadata**
   - Stores: Table-level semantic information
   - ID format: `table_{table_name}`
   - Embedding: 768-dimensional vector from nomic-embed-text
   
   **Metadata Schema**:
   ```python
   {
       "table_name": str,
       "description": str,
       "category": str,  # sales, financial, educational, etc.
       "business_context": str,
       "suggested_primary_key": str,
       "data_quality_notes": str (JSON array),
       "row_count": int,
       "column_count": int
   }
   ```

2. **column_metadata**
   - Stores: Column-level semantic information
   - ID format: `column_{table_name}_{column_name}`
   - Embedding: 768-dimensional vector
   
   **Metadata Schema**:
   ```python
   {
       "table_name": str,
       "column_name": str,
       "sql_type": str,  # TEXT, INTEGER, REAL, DATE, BOOLEAN
       "python_type": str,  # str, int, float, datetime, bool
       "description": str,
       "business_meaning": str,
       "constraints": str (JSON array),
       "is_nullable": str (bool as string),
       "suggested_index": str (bool as string),
       "unique_count": int,
       "null_count": int
   }
   ```

### Vector Search Mechanism

**Query Processing**:

```python
# 1. User asks: "Show me sales data"

# 2. Generate embedding for question
query_embedding = _get_embedding("Show me sales data")
# Result: [0.234, -0.567, ...] (768 numbers)

# 3. Query ChromaDB
results = table_collection.query(
    query_embeddings=[query_embedding],
    n_results=5  # Top 5 most relevant tables
)

# 4. ChromaDB returns ranked results
{
    "ids": [["table_sales", "table_transactions", ...]],
    "distances": [[0.12, 0.34, ...]],  # Lower = more similar
    "metadatas": [[
        {"table_name": "sales", "description": "..."},
        {"table_name": "transactions", "description": "..."}
    ]],
    "documents": [[
        "Table: sales\nDescription: ...",
        "Table: transactions\nDescription: ..."
    ]]
}

# 5. Format metadata for LLM context
metadata_str = "\n\n".join(results["documents"][0])
```

**Similarity Calculation**: Cosine similarity between embeddings
- Score 0.0-1.0 (ChromaDB shows as distance, lower is better)
- Semantic matching: "revenue" finds "sales", "income", "earnings"

### Embedding Model: nomic-embed-text

**Specifications**:
- Dimensions: 768
- Context length: 8192 tokens
- Hosted: Ollama local server
- Endpoint: `POST http://localhost:11434/api/embeddings`

**Request/Response**:
```python
# Request
{
    "model": "nomic-embed-text",
    "prompt": "Show me sales data"
}

# Response
{
    "embedding": [0.234, -0.567, 0.123, ..., 0.891]  # 768 floats
}
```

**Why 768 dimensions**:
- Balance between accuracy and performance
- Standard BERT-base size
- Sufficient for capturing semantic meaning
- Efficient storage (~3KB per embedding)

---

## CLASS & FUNCTION REFERENCE

### Pydantic Models

#### QuestionIntent (Enum)
```python
class QuestionIntent(str, Enum):
    NEW_QUERY = "new_query"        # Fresh database query
    RE_VISUALIZE = "re_visualize"  # New chart for same data
    TRANSFORM = "transform"         # Modify existing data
    COMBINE = "combine"             # Merge multiple datasets
    COMPARE = "compare"             # Side-by-side comparison
    CLARIFY = "clarify"             # Explain previous result
```

#### IntentAnalysis
```python
class IntentAnalysis(BaseModel):
    intent: str                     # One of QuestionIntent values
    references_previous: bool       # True if mentions "that", "those", etc.
    referenced_concepts: List[str]  # ["sales", "categories", "profit"]
    needs_context: bool             # True if requires conversation history
    confidence: float               # 0.0-1.0 confidence score
```

#### VisualizationResponse
```python
class VisualizationResponse(BaseModel):
    should_visualize: bool
    chart_types: List[str]  # ["bar", "line"] - alternatives
    primary_chart: str      # "bar" - recommended type
    x_axis: Optional[str]   # "category"
    y_axis: Optional[str]   # "sales_amount"
    color_by: Optional[str] # "region"
    title: str              # "Sales by Category"
    visualization_rationale: str  # Why this viz is appropriate
```

#### MetadataResponse
```python
class MetadataResponse(BaseModel):
    table_name: str
    description: str
    suggested_primary_key: Optional[str]
    category: str           # sales, financial, educational, etc.
    business_context: str
    data_quality_notes: List[str]
```

#### DataTypeResponse
```python
class DataTypeResponse(BaseModel):
    sql_type: str           # TEXT, INTEGER, REAL, DATE, BOOLEAN
    python_type: str        # str, int, float, datetime, bool
    description: str
    business_meaning: str
    constraints: List[str]  # ["NOT NULL", "UNIQUE"]
    is_nullable: bool
    suggested_index: bool
```

### SQL Cleaning Functions

#### `_clean_sql(query: str) -> str`

**Input**: Raw LLM SQL output (may contain markdown, explanations)
**Output**: Clean, executable SQL

**Transformations**:
1. Remove markdown fences: ` ```sql ... ``` `
2. Strip "SQLQuery:" prefixes
3. Extract last SQL statement marker
4. Remove numbered steps before SELECT
5. Remove explanatory prose
6. Extract SELECT/WITH keywords
7. Balance quotes
8. Collapse whitespace

**Example**:
```python
# Input
raw_sql = """
Here's the SQL query:
```sql
SELECT * FROM sales
WHERE amount > 100
ORDER BY date DESC
```
This query returns sales over $100.
"""

# Output
clean_sql = "SELECT * FROM sales WHERE amount > 100 ORDER BY date DESC"
```

#### `_validate_and_fix_tables(sql_query: str) -> str`

**Purpose**: Fix invalid table/column references

**Validation Steps**:
1. Load valid tables from SQLite
2. Extract CTE (Common Table Expression) names
3. Build column-to-table mapping
4. Analyze query aliases
5. Detect invalid table references
6. Fix or remove invalid JOINs
7. Replace invalid column references
8. Clean up broken clauses

**Example Fix**:
```sql
-- BEFORE (Invalid table "invalid_table")
SELECT s.region, SUM(invalid_table.amount) as total
FROM sales s
LEFT JOIN invalid_table ON s.id = invalid_table.sale_id
GROUP BY s.region

-- AFTER (Fixed)
SELECT s.region, SUM(s.amount) as total
FROM sales s
GROUP BY s.region
```

### Error Handling Functions

#### `_parse_with_fallback(response_text: str, parser, fallback_data: dict)`

**Purpose**: Gracefully handle LLM parsing failures

**Algorithm**:
```python
1. TRY: parser.parse(response_text)
2. IF fails:
   a. TRY: Extract JSON from markdown (```json ... ```)
   b. TRY: Extract any {...} pattern
   c. TRY: Fix common JSON issues (trailing commas, single quotes)
   d. IF all fail: RETURN fallback_data
```

**Usage**:
```python
# With fallback
result = self._parse_with_fallback(
    llm_response,
    self.viz_parser,
    fallback_data={
        "should_visualize": False,
        "primary_chart": "none",
        "visualization_rationale": "Could not parse LLM response"
    }
)
```

---

## CONFIGURATION & PARAMETERS

### QueryAgentEnhanced Configuration

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `source_db_path` | str | Required | Path to SQLite database |
| `vector_db_path` | str | `"./chroma_db_768dim"` | Path to ChromaDB directory |
| `llm_model` | str | `"qwen2.5:7b"` | Ollama model name |
| `conversation_state` | ConversationState | `None` | Existing state or creates new |
| `max_context_messages` | int | `10` | Max messages in LLM context |
| `max_data_contexts` | int | `20` | Max data contexts to retain |
| `temperature` | float | `0.1` | LLM temperature (0.0-1.0) |
| `ollama_base_url` | str | `"http://localhost:11434"` | Ollama server URL |
| `embedding_model` | str | `"nomic-embed-text"` | Embedding model (768-dim) |

**Temperature Impact**:
- `0.0`: Deterministic, same output for same input
- `0.1`: Slightly varied, good for SQL generation (current)
- `0.5`: Moderately creative
- `1.0`: Maximum creativity/randomness

### Ollama LLM Configuration

```python
self.llm = ChatOllama(
    model=llm_model,
    base_url=ollama_base_url,
    temperature=temperature,
    num_ctx=4096,          # Context window size (tokens)
    num_predict=1024,      # Max tokens to generate
    repeat_penalty=1.1,    # Penalize repetition (>1.0 reduces repetition)
    timeout=120            # Request timeout in seconds
)
```

**num_ctx (Context Window)**:
- 4096 tokens = ~16,000 characters
- Includes: system prompt + conversation history + question
- If exceeded, oldest messages dropped
- qwen2.5:7b supports up to 128K, but 4096 is optimal for speed

**num_predict**:
- Maximum tokens in response
- SQL queries typically <200 tokens
- Answers typically 100-500 tokens
- 1024 provides buffer for complex responses

### Gradio Configuration

```python
demo.launch(
    server_name="0.0.0.0",  # Listen on all interfaces
    server_port=6969,       # Port number
    share=False,            # Don't create public URL
    debug=False,            # Production mode
    show_error=True         # Display errors in UI
)
```

**Network Access**:
- `server_name="0.0.0.0"`: Accessible from any network interface
- `server_name="127.0.0.1"`: Localhost only
- Use firewall rules to control access in production

---

## DATA STRUCTURES & EXAMPLES

### Conversation JSON File Structure

**File**: `conversations/2e6a2e96-1a3f-43f8-95cb-2a1debc1135a.json`

```json
{
  "conversation_id": "2e6a2e96-1a3f-43f8-95cb-2a1debc1135a",
  "start_time": "2025-11-20T22:35:32.992155",
  "message_count": 4,
  "messages": [
    {
      "role": "user",
      "content": "What are the top 5 sales?",
      "timestamp": "2025-11-20T22:35:40.123456",
      "sql_query": null,
      "dataframe_snapshot": null,
      "visualization": null,
      "figure_json": null,
      "metadata": {
        "intent": "new_query"
      }
    },
    {
      "role": "assistant",
      "content": "The top 5 sales by amount are:\n1. $1,536.17 from Electronics (TXN-1234)\n2. $1,112.25 from Home (TXN-5678)\n...",
      "timestamp": "2025-11-20T22:35:45.789012",
      "sql_query": "SELECT * FROM sales ORDER BY amount DESC LIMIT 5",
      "dataframe_snapshot": {
        "columns": ["transaction_id", "amount", "date", "category"],
        "row_count": 5,
        "sample": {
          "transaction_id": {
            "0": "TXN-1234",
            "1": "TXN-5678",
            "2": "TXN-9012",
            "3": "TXN-3456",
            "4": "TXN-7890"
          },
          "amount": {
            "0": 1536.17,
            "1": 1112.25,
            "2": 765.28,
            "3": 508.85,
            "4": 246.47
          },
          "date": {
            "0": "2024-03-15",
            "1": "2024-02-28",
            "2": "2024-01-12",
            "3": "2024-04-03",
            "4": "2024-03-22"
          },
          "category": {
            "0": "Electronics",
            "1": "Home",
            "2": "Sports",
            "3": "Fashion",
            "4": "Beauty"
          }
        }
      },
      "visualization": null,
      "figure_json": null,
      "metadata": {
        "intent": "new_query",
        "success": true
      }
    },
    {
      "role": "user",
      "content": "Show as bar chart",
      "timestamp": "2025-11-20T22:36:00.111222",
      "sql_query": null,
      "dataframe_snapshot": null,
      "visualization": null,
      "figure_json": null,
      "metadata": {
        "intent": "re_visualize"
      }
    },
    {
      "role": "assistant",
      "content": "I've created a bar chart showing the top 5 sales by amount...",
      "timestamp": "2025-11-20T22:36:05.333444",
      "sql_query": "SELECT * FROM sales ORDER BY amount DESC LIMIT 5",
      "dataframe_snapshot": {
        "columns": ["transaction_id", "amount", "date", "category"],
        "row_count": 5,
        "sample": {...}
      },
      "visualization": "bar",
      "figure_json": "{\"data\":[{\"type\":\"bar\",\"x\":[\"Electronics\",\"Home\",\"Sports\",\"Fashion\",\"Beauty\"],\"y\":[1536.17,1112.25,765.28,508.85,246.47],\"marker\":{\"color\":\"#636efa\"}}],\"layout\":{\"title\":{\"text\":\"Top 5 Sales by Amount\"},\"xaxis\":{\"title\":{\"text\":\"Category\"}},\"yaxis\":{\"title\":{\"text\":\"Amount\"}}}}",
      "metadata": {
        "intent": "re_visualize",
        "success": true
      }
    }
  ],
  "data_contexts": [
    {
      "query": "SELECT * FROM sales ORDER BY amount DESC LIMIT 5",
      "columns": ["transaction_id", "amount", "date", "category"],
      "row_count": 5,
      "sample_data": {
        "transaction_id": {"0": "TXN-1234", "1": "TXN-5678", ...},
        "amount": {"0": 1536.17, "1": 1112.25, ...},
        "date": {"0": "2024-03-15", "1": "2024-02-28", ...},
        "category": {"0": "Electronics", "1": "Home", ...}
      },
      "timestamp": "2025-11-20T22:35:45.789012"
    }
  ],
  "visualizations": [
    {
      "question": "Show as bar chart",
      "chart_type": "bar",
      "data_summary": "5 rows",
      "timestamp": "2025-11-20T22:36:05.333444"
    }
  ]
}
```

### Answer Examples

#### Example 1: Simple Query Answer
```
Question: "What are the total sales by region?"

Answer: "The total sales by region are as follows:
- North: $245,678.90 (32% of total)
- South: $198,432.15 (26% of total)
- East: $176,543.22 (23% of total)
- West: $142,109.73 (19% of total)

The North region leads with the highest sales, accounting for nearly one-third of all revenue. Total across all regions: $762,764.00."

SQL: SELECT region, SUM(amount) as total_sales 
     FROM sales 
     GROUP BY region 
     ORDER BY total_sales DESC
```

#### Example 2: Comparative Analysis Answer
```
Question: "Compare Q1 vs Q2 sales"

Answer: "Comparing Q1 and Q2 sales performance:

Q1 (Jan-Mar): $1,234,567.89
Q2 (Apr-Jun): $1,456,234.12

Key findings:
• Q2 sales increased by $221,666.23 (+18% growth)
• Average daily sales: Q1 = $13,720, Q2 = $16,003
• Peak month: June with $523,145.67
• Growth driven primarily by Electronics (+45%) and Home categories (+32%)

The upward trend suggests strong market momentum heading into the second half of the year."

SQL: SELECT 
    CASE 
        WHEN CAST(SUBSTR(date, 6, 2) AS INTEGER) <= 3 THEN 'Q1'
        WHEN CAST(SUBSTR(date, 6, 2) AS INTEGER) <= 6 THEN 'Q2'
    END as quarter,
    SUM(amount) as total_sales,
    COUNT(*) as transaction_count
FROM sales
WHERE quarter IN ('Q1', 'Q2')
GROUP BY quarter
```

#### Example 3: Distribution Analysis Answer
```
Question: "Show profit margin distribution by category using box plot"

Answer: "The profit margin distribution reveals interesting patterns across categories:

• Electronics: Widest range (-2.95 to 1536.17), median 55.72
  - High variability indicates diverse product mix
  - Outliers on high end (premium items)
  
• Home: Second-highest median (47.86), range -3.55 to 1112.25
  - Consistent profitability with occasional high-value items
  
• Grocery: Notable concern - negative median (-2.26)
  - Range: -6.20 to 26.47
  - May require pricing strategy review
  
• Fashion, Beauty, Sports: Moderate ranges with positive medians
  - Relatively stable profitability
  
• Toys: Lowest median (7.93), narrow range
  - Consistent but low margins

The box plot visualization shows quartiles, outliers, and overall spread for each category, making it easy to identify which segments have the most variable or stable profit margins."

Visualization: Box plot with category on X-axis, profit_margin on Y-axis
```

---

## ERROR HANDLING & RECOVERY

### Error Categories & Responses

#### 1. Ollama Connection Errors

**Scenario**: Ollama server not running

```python
Error: Cannot connect to Ollama: Connection refused

Recovery:
1. Check Ollama status: `ollama serve`
2. Verify port: Default 11434
3. Check firewall rules
4. Restart Ollama service

User Message: "❌ Ollama is not running. Please ensure Ollama is installed and running with: ollama serve"
```

**Detection**:
```python
def test_ollama_connection(self) -> bool:
    try:
        response = requests.get(f"{self.ollama_base_url}/api/tags", timeout=5)
        return response.status_code == 200
    except Exception as e:
        logger.error(f"Cannot connect to Ollama: {e}")
        return False
```

#### 2. SQL Execution Errors

**Scenario**: Generated SQL is invalid

```python
Error: no such column: invalid_column

Recovery Strategy:
1. Log error with full SQL query
2. Extract error details (column name, table reference)
3. Build error feedback prompt for LLM
4. Regenerate SQL with error context
5. Retry execution (max 1 retry)

Prompt Example:
"Previous SQL attempt:
SELECT invalid_column FROM sales

SQLite error: no such column: invalid_column

Available columns: [transaction_id, amount, date, category]

Rewrite the SQL to use valid column names."
```

**Implementation**:
```python
for exec_attempt in range(2):
    try:
        df = pd.read_sql_query(final_sql, self.conn)
        break
    except Exception as e:
        execution_error = str(e)
        logger.error(f"SQL execution failed (attempt {exec_attempt + 1}): {execution_error}")
        
        if exec_attempt == 1:
            return {"success": False, "error": f"Query execution failed: {execution_error}"}
        
        # Regenerate SQL with error feedback
        alias_summary = self._describe_query_aliases(final_sql)
        repair_prompt = self._augment_prompt_with_error(
            context_prompt, final_sql, execution_error, alias_summary
        )
        
        regenerated_sql = self._generate_sql_with_retry(question, repair_prompt, metadata_str)
        final_sql = self._clean_sql(regenerated_sql)
```

#### 3. LLM Parsing Errors

**Scenario**: LLM returns malformed JSON

```python
Error: JSON parsing failed: Expecting ',' delimiter

Example Bad Response:
{
    "intent": "new_query",
    "confidence": 0.9,  # Missing closing brace
```

**Recovery**:
```python
def _parse_with_fallback(self, response_text, parser, fallback_data):
    try:
        return parser.parse(response_text)
    except Exception as e:
        # Try extract from markdown
        if "```json" in response_text:
            json_str = response_text.split("```json")[1].split("```")[0]
        else:
            json_str = response_text
        
        try:
            # Clean common issues
            json_str = json_str.replace("'", '"')  # Single to double quotes
            json_str = re.sub(r',\s*}', '}', json_str)  # Remove trailing commas
            parsed = json.loads(json_str)
            return parser.pydantic_object(**parsed)
        except:
            logger.warning("All parsing attempts failed, using fallback")
            return fallback_data
```

#### 4. Visualization Errors

**Scenario**: Cannot create chart

```python
Error: KeyError: 'invalid_column'

Recovery:
1. Log error with visualization config
2. Attempt column name resolution
3. If fails, skip visualization
4. Return results without chart
5. Inform user in answer text

User Message: "I couldn't create the visualization due to a column mismatch, but here are the query results..."
```

#### 5. Conversation Load Errors

**Scenario**: Corrupted conversation file

```python
Error: JSON decode error in conversation file

Recovery:
1. Log error with filename
2. Attempt partial recovery:
   - Load valid messages only
   - Skip corrupted visualizations
3. Display warning to user
4. Allow continued use with recovered data

User Message: "⚠️ Some data couldn't be loaded from this conversation, but I've recovered what I could."
```

### Logging Strategy

**Log Levels**:
- **DEBUG**: SQL queries, LLM prompts, detailed flow
- **INFO**: Major operations, user actions, success messages
- **WARNING**: Fallback usage, retries, non-critical issues
- **ERROR**: Failures, exceptions, invalid states

**Example Logs**:
```
2025-11-20 22:35:40 INFO: Detected intent: new_query (confidence: 0.95)
2025-11-20 22:35:42 DEBUG: Generated SQL: SELECT * FROM sales ORDER BY amount DESC LIMIT 5
2025-11-20 22:35:43 INFO: Query executed successfully, returned 5 rows
2025-11-20 22:35:45 WARNING: Pydantic parsing failed: JSONDecodeError, using fallback
2025-11-20 22:35:46 INFO: Created bar chart visualization
2025-11-20 22:35:47 INFO: Conversation saved: a1b2c3d4-uuid.json
```

---

## PERFORMANCE & OPTIMIZATION

### Bottleneck Analysis

**Typical Query Timeline**:
```
Operation                     Time      % of Total
─────────────────────────────────────────────────
User input received           0ms       -
Intent analysis (LLM)         800ms     20%
Metadata retrieval (Vector)   50ms      1%
SQL generation (LLM)          1200ms    30%
SQL validation               100ms     3%
Query execution              200ms     5%
Answer generation (LLM)       1000ms    25%
Viz decision (LLM)            500ms     12%
Viz creation (Plotly)         100ms     3%
State update & save           50ms      1%
─────────────────────────────────────────────────
TOTAL                         4000ms    100%
```

**LLM calls are the bottleneck** (75% of time)

### Optimization Strategies

#### 1. Caching

**SQL Query Cache**:
```python
# Cache identical questions
query_cache = {}

def get_cached_sql(question_hash):
    if question_hash in query_cache:
        logger.info("Using cached SQL query")
        return query_cache[question_hash]
    return None
```

**Metadata Cache**:
```python
# Load all metadata once at initialization
self.table_metadata = self._load_table_metadata()  # One-time
self.column_metadata = self._load_column_metadata()

# Reuse in memory instead of querying ChromaDB repeatedly
```

#### 2. Parallel Processing

**Potential Parallelization** (not currently implemented):
```python
import concurrent.futures

# Parallel LLM calls
with concurrent.futures.ThreadPoolExecutor() as executor:
    intent_future = executor.submit(self._analyze_question_intent, question)
    metadata_future = executor.submit(self._retrieve_metadata, question)
    
    intent = intent_future.result()
    metadata = metadata_future.result()

# Could reduce 850ms (intent + metadata) to ~800ms (max of both)
```

#### 3. Model Selection

**Speed vs Quality Tradeoff**:

| Model | Speed | Quality | Tokens/sec |
|-------|-------|---------|------------|
| qwen2.5:7b | Medium | High | ~40 |
| llama3:8b | Medium | High | ~35 |
| phi3:mini | Fast | Medium | ~60 |
| mixtral:8x7b | Slow | Highest | ~20 |

**Recommendation**: Use qwen2.5:7b (current default) for balanced performance

#### 4. Temperature Optimization

**Lower temperature = Faster generation**:
- Current: 0.1 (good for SQL accuracy)
- For pure speed: 0.0 (deterministic)
- Tradeoff: Less creative answers, but 10-15% faster

#### 5. Context Window Management

**Reduce context size**:
```python
# Instead of all recent messages:
recent_messages = self.conversation_state.get_recent_messages(10)

# Only include essential messages:
relevant_messages = [msg for msg in recent_messages if msg.sql_query is not None][:5]
```

**Impact**: Reduces token count, faster LLM processing

#### 6. DataFrame Snapshot Optimization

**Current**: Store first 50 rows
**Alternative**: Store only row count + columns for non-viz queries

```python
if viz_response.should_visualize:
    snapshot = df.head(50).to_dict()
else:
    snapshot = None  # Save memory & file size
```

### Memory Optimization

**Memory Profile** (typical 10-message conversation):

| Component | Size | Notes |
|-----------|------|-------|
| ConversationState | ~500 KB | With snapshots |
| DataFrame (active) | 2-5 MB | Depends on row count |
| Plotly Figure | ~200 KB | JSON serialized |
| ChromaDB metadata (loaded) | ~1-2 MB | All tables + columns |
| LLM context | ~500 KB | Temporary during calls |
| **TOTAL** | **4-8 MB** | Per conversation |

**For 100 concurrent users**: 400-800 MB (manageable)

**Optimization**:
- Auto-cleanup old data contexts (keep last 10)
- Don't store full DataFrames (only snapshots)
- Clear LLM context after each call
- Use generators for large result sets

---

## DEPLOYMENT GUIDE

### Prerequisites

**System Requirements**:
- **OS**: Windows 10/11, Linux (Ubuntu 20.04+), macOS 11+
- **RAM**: 8 GB minimum, 16 GB recommended
- **Storage**: 10 GB for models + data
- **CPU**: Modern multi-core processor
- **GPU**: Optional (speeds up Ollama if NVIDIA with CUDA)

**Software Dependencies**:
```bash
# Python 3.10 or higher
python --version  # Should be 3.10+

# Ollama
# Windows: Download installer from ollama.com
# Linux/Mac:
curl -fsSL https://ollama.com/install.sh | sh

# Verify Ollama
ollama --version
```

### Installation Steps

#### 1. Clone/Download Repository

```bash
git clone <repository-url>
cd "Ollama 2"
```

#### 2. Create Virtual Environment

```powershell
# Windows
python -m venv venv
.\venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

#### 3. Install Python Dependencies

```bash
pip install -r requirements.txt
```

**requirements.txt**:
```
pandas==2.1.3
plotly==5.18.0
gradio==4.8.0
langchain==0.1.0
langchain-community==0.0.10
langchain-ollama==0.0.3
chromadb==0.4.18
pydantic==2.5.2
python-dotenv==1.0.0
requests==2.31.0
```

#### 4. Download Ollama Models

```bash
# Main LLM model (7B parameters, ~4.7 GB)
ollama pull qwen2.5:7b

# Embedding model (~275 MB)
ollama pull nomic-embed-text

# Verify models
ollama list
```

Expected output:
```
NAME                    ID              SIZE      MODIFIED
qwen2.5:7b              abc123def456    4.7 GB    2 hours ago
nomic-embed-text        ghi789jkl012    275 MB    2 hours ago
```

#### 5. Start Ollama Server

```bash
# Start in background
ollama serve

# Verify server
curl http://localhost:11434/api/tags
```

#### 6. Prepare Database

**Option A: Use Existing SQLite Database**
```bash
# Place your database file
cp /path/to/your/database.db ./analysis.db
```

**Option B: Convert CSV to Database**
```bash
python "PRE PROCESSING/csv_to_db.py" data.csv --db analysis.db
```

#### 7. Analyze Database (Create Vector Database)

```bash
python "PRE PROCESSING/analyze_existing_db.py" analysis.db
```

**Expected output**:
```
🔍 DATABASE ANALYZER (Vector DB Edition)
════════════════════════════════════════
Source Database: analysis.db
Vector Database: ./chroma_db_768dim
LLM Model: qwen2.5:7b
════════════════════════════════════════

📊 Found 3 table(s) to analyze: ['sales', 'products', 'customers']

[1/3] Processing: sales
🔍 Analyzing table: sales
   Found 10000 rows and 8 columns
   Analyzing column 1/8: transaction_id
   ...
✅ Successfully analyzed and saved: sales

[2/3] Processing: products
...

🎉 Analysis complete!
════════════════════════════════════════
📊 ANALYSIS SUMMARY
════════════════════════════════════════
Tables Analyzed: 3
Total Columns: 24
Vector Database: ./chroma_db_768dim
════════════════════════════════════════
```

**Time**: ~5-10 minutes depending on database size

#### 8. Launch Application

```bash
python app_gradio_enhanced.py
```

**Expected output**:
```
🚀 Starting UI...
Running on local URL:  http://0.0.0.0:6969

To create a public link, set `share=True` in `launch()`.
```

#### 9. Open in Browser

Navigate to: `http://localhost:6969`

#### 10. Initialize Agent in UI

1. Enter database path: `analysis.db`
2. Enter vector DB path: `./chroma_db_768dim`
3. Select model: `qwen2.5:7b`
4. Click "Initialize the LLM Agent"
5. Wait for "✅ Agent Ready"

### Production Deployment

#### Using Docker

**Dockerfile**:
```dockerfile
FROM python:3.10-slim

# Install Ollama
RUN curl -fsSL https://ollama.com/install.sh | sh

# Copy application
WORKDIR /app
COPY . /app

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Pull models
RUN ollama serve & \
    sleep 5 && \
    ollama pull qwen2.5:7b && \
    ollama pull nomic-embed-text

# Expose port
EXPOSE 6969

# Start services
CMD ["bash", "-c", "ollama serve & python app_gradio_enhanced.py"]
```

**Build and Run**:
```bash
docker build -t data-analytics-ai .
docker run -p 6969:6969 -v $(pwd)/conversations:/app/conversations data-analytics-ai
```

#### Nginx Reverse Proxy

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:6969;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

#### Systemd Service (Linux)

**File**: `/etc/systemd/system/data-analytics.service`
```ini
[Unit]
Description=Data Analytics AI System
After=network.target

[Service]
Type=simple
User=youruser
WorkingDirectory=/path/to/app
ExecStartPre=/usr/local/bin/ollama serve &
ExecStart=/path/to/venv/bin/python app_gradio_enhanced.py
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

**Enable and Start**:
```bash
sudo systemctl enable data-analytics
sudo systemctl start data-analytics
sudo systemctl status data-analytics
```

### Troubleshooting

#### Issue: "Ollama not running"

**Solution**:
```bash
# Check if Ollama is running
ps aux | grep ollama

# Start Ollama
ollama serve

# Check port
netstat -an | grep 11434
```

#### Issue: "Vector database not found"

**Solution**:
```bash
# Verify ChromaDB directory exists
ls -la ./chroma_db_768dim

# If missing, re-run analyzer
python "PRE PROCESSING/analyze_existing_db.py" analysis.db
```

#### Issue: "Slow response times"

**Solution**:
1. Check system resources: `top` or Task Manager
2. Reduce model size: Use `qwen2.5:3b` instead of `7b`
3. Limit conversation history: Set `max_context_messages=5`
4. Close other applications

#### Issue: "Chart not displaying"

**Solution**:
1. Check browser console for JavaScript errors
2. Verify Plotly is installed: `pip show plotly`
3. Clear browser cache
4. Try different browser (Chrome recommended)

---

## APPENDIX

### A. File Structure Summary

```
Ollama 2/
├── app_gradio_enhanced.py          # Main Gradio UI application
├── QueryAgent_Ollama_Enhanced.py   # Core query processing logic
├── conversation_manager.py         # Conversation state management
├── requirements.txt                # Python dependencies
│
├── PRE PROCESSING/
│   ├── analyze_existing_db.py      # Database analyzer (creates vector DB)
│   ├── csv_to_db.py                # CSV to SQLite converter
│   ├── ARCHITECTURE.md             # This documentation (Part 1)
│   └── ARCHITECTURE_PART2.md       # This file (Part 2)
│
├── conversations/                  # Saved conversation files
│   ├── <uuid>.json
│   └── ...
│
├── chroma_db_768dim/               # Vector database (created by analyzer)
│   ├── chroma.sqlite3
│   ├── <collection-id>/
│   └── ...
│
└── analysis.db                     # User's SQLite database
```

### B. API Quick Reference

**Initialize Agent**:
```python
from QueryAgent_Ollama_Enhanced import QueryAgentEnhanced
from conversation_manager import ConversationState

conversation_state = ConversationState()
agent = QueryAgentEnhanced(
    source_db_path="analysis.db",
    vector_db_path="./chroma_db_768dim",
    llm_model="qwen2.5:7b",
    conversation_state=conversation_state
)
```

**Ask Question**:
```python
result = agent.answer_question_with_context("What are the top 5 sales?")

print(result['answer'])          # Natural language answer
print(result['sql_query'])       # Generated SQL
print(result['data'])            # pandas DataFrame
print(result['visualization'])   # Plotly figure (if any)
```

**Save Conversation**:
```python
import json

data = conversation_state.export_conversation()
with open(f"conversations/{conversation_state.conversation_id}.json", 'w') as f:
    json.dump(data, f, indent=2)
```

**Load Conversation**:
```python
with open("conversations/uuid.json", 'r') as f:
    data = json.load(f)

conversation_state = ConversationState()
conversation_state.import_conversation(data)
agent.conversation_state = conversation_state
```

### C. Glossary

- **CTE**: Common Table Expression (SQL WITH clause)
- **ChromaDB**: Vector database for semantic search
- **Embeddings**: Numerical representations of text (768-dim vectors)
- **Intent**: User's goal (NEW_QUERY, RE_VISUALIZE, TRANSFORM, etc.)
- **LLM**: Large Language Model (qwen2.5:7b)
- **Ollama**: Local LLM server
- **Plotly**: Interactive charting library
- **Pydantic**: Data validation using Python type hints
- **Semantic Search**: Finding relevant data by meaning, not exact keywords
- **Temperature**: LLM randomness parameter (0.0-1.0)
- **Vector Database**: Database optimized for similarity search

### D. References

- **Ollama Documentation**: https://ollama.com/docs
- **LangChain Documentation**: https://python.langchain.com/docs
- **ChromaDB Documentation**: https://docs.trychroma.com/
- **Gradio Documentation**: https://www.gradio.app/docs
- **Plotly Documentation**: https://plotly.com/python/

### E. Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | Oct 2024 | Initial system with basic query support |
| 1.5 | Nov 2024 | Added conversation management |
| 2.0 | Nov 2025 | Complete multi-turn context, visualization, persistence |

---

## END OF DOCUMENTATION

For questions or support, refer to the code comments or create an issue in the repository.

**Last Updated**: November 21, 2025  
**Document Author**: AI Architecture Documentation Generator  
**Total Pages**: ~150 equivalent pages
