# COMPREHENSIVE SYSTEM ARCHITECTURE DOCUMENTATION
# Conversational Data Analytics System with Multi-Turn Context & Visualization

**Version:** 2.0  
**Last Updated:** November 21, 2025  
**Target Audience:** Developers, System Administrators, Technical Architects

---

## TABLE OF CONTENTS

1. [System Overview](#system-overview)
2. [High-Level Architecture](#high-level-architecture)
3. [Core Components Deep Dive](#core-components-deep-dive)
4. [Data Flow & Workflows](#data-flow--workflows)
5. [Conversation Management System](#conversation-management-system)
6. [Visualization Pipeline](#visualization-pipeline)
7. [Database & Vector Storage](#database--vector-storage)
8. [Class & Function Reference](#class--function-reference)
9. [Configuration & Parameters](#configuration--parameters)
10. [Data Structures & Examples](#data-structures--examples)
11. [Error Handling & Recovery](#error-handling--recovery)
12. [Performance & Optimization](#performance--optimization)
13. [Complete Deployment Guide - From Zero to Production](#complete-deployment-guide---from-zero-to-production)
14. [End-to-End User Guide - Getting Final Answers](#end-to-end-user-guide---getting-final-answers)

---

## SYSTEM OVERVIEW

### Purpose
This system is a **conversational data analytics platform** that enables natural language querying of SQLite databases with:
- **Multi-turn conversation support** with full context retention
- **Intelligent SQL generation** using LLM (Large Language Models)
- **Automatic visualization recommendation** and generation
- **Vector database-powered metadata retrieval** for semantic search
- **Persistent conversation history** with ability to restore sessions
- **Interactive web interface** using Gradio

### Key Capabilities
1. **Natural Language to SQL**: Convert user questions into executable SQL queries
2. **Contextual Awareness**: Remember previous queries and reference them in follow-up questions
3. **Smart Visualization**: Automatically detect when to visualize and choose appropriate chart types
4. **Data Transformation**: Filter, sort, and manipulate previous results without re-querying
5. **Conversation Persistence**: Save and restore complete conversation sessions
6. **Metadata-Driven Intelligence**: Use LLM-analyzed metadata for better SQL generation

### Technology Stack
- **Language**: Python 3.10+
- **LLM Framework**: LangChain + Ollama (qwen2.5:7b model)
- **Vector Database**: ChromaDB (with nomic-embed-text embeddings, 768-dim)
- **SQL Database**: SQLite
- **Visualization**: Plotly (interactive charts)
- **Web Interface**: Gradio
- **Data Processing**: Pandas

---

## HIGH-LEVEL ARCHITECTURE

### System Layers

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          PRESENTATION LAYER                             │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  Gradio Web Interface (app_gradio_enhanced.py)                   │   │
│  │  - Chat Interface with History Sidebar                           │   │
│  │  - Interactive Visualizations (Plotly Charts)                    │   │
│  │  - Data Tables (HTML)                                            │   │
│  │  - Conversation Management (New/Load/Delete)                     │   │
│  └──────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
                                    ↓↑
┌─────────────────────────────────────────────────────────────────────────┐
│                          APPLICATION LAYER                              │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  QueryAgentEnhanced (QueryAgent_Ollama_Enhanced.py)             │   │
│  │  - Question Intent Analysis                                      │   │
│  │  - SQL Generation & Validation                                   │   │
│  │  - Result Processing                                             │   │
│  │  - Visualization Decision Making                                 │   │
│  │  - Context Management                                            │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  ConversationState (conversation_manager.py)                     │   │
│  │  - Message History Tracking                                      │   │
│  │  - Data Context Storage                                          │   │
│  │  - Visualization Records                                         │   │
│  │  - Import/Export Functionality                                   │   │
│  └──────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
                                    ↓↑
┌─────────────────────────────────────────────────────────────────────────┐
│                          INTELLIGENCE LAYER                             │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  Ollama LLM (qwen2.5:7b)                                         │   │
│  │  - Intent Classification                                         │   │
│  │  - SQL Query Generation                                          │   │
│  │  - Natural Language Answer Generation                            │   │
│  │  - Visualization Recommendations                                 │   │
│  │  - Metadata Analysis (during setup)                              │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  LangChain Framework                                             │   │
│  │  - Prompt Templates                                              │   │
│  │  - Output Parsers (Pydantic Models)                              │   │
│  │  - SQL Query Chain                                               │   │
│  └──────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
                                    ↓↑
┌─────────────────────────────────────────────────────────────────────────┐
│                          DATA LAYER                                     │
│  ┌─────────────────┐  ┌─────────────────┐  ┌────────────────────────┐  │
│  │  ChromaDB       │  │  SQLite         │  │  Conversation Files    │  │
│  │  (Vector DB)    │  │  (Source DB)    │  │  (JSON)                │  │
│  │                 │  │                 │  │                        │  │
│  │  • Table        │  │  • User Tables  │  │  • Message History     │  │
│  │    Metadata     │  │  • Business     │  │  • Data Snapshots      │  │
│  │  • Column       │  │    Data         │  │  • Visualizations      │  │
│  │    Metadata     │  │                 │  │  • Timestamps          │  │
│  │  • Embeddings   │  │                 │  │                        │  │
│  │    (768-dim)    │  │                 │  │                        │  │
│  └─────────────────┘  └─────────────────┘  └────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
```

### Component Interaction Flow

```
User Question
    ↓
[Gradio UI] → process_question()
    ↓
[QueryAgentEnhanced] → answer_question_with_context()
    ↓
┌───────────────────────────────────────────────┐
│ Step 1: Intent Analysis                       │
│ _analyze_question_intent()                    │
│ • Detect: NEW_QUERY, RE_VISUALIZE,            │
│   TRANSFORM, COMBINE, COMPARE, CLARIFY        │
│ • Check for previous data references          │
└───────────────────────────────────────────────┘
    ↓
┌───────────────────────────────────────────────┐
│ Step 2: Context Retrieval                     │
│ • Search Vector DB for relevant metadata      │
│ • Build context from conversation history     │
│ • Retrieve previous DataFrame if referenced   │
└───────────────────────────────────────────────┘
    ↓
┌───────────────────────────────────────────────┐
│ Step 3: Query Processing (Intent-Based)       │
│                                                │
│ NEW_QUERY → _process_new_query()              │
│   ├→ Generate SQL via LLM                     │
│   ├→ Clean & Validate SQL                     │
│   ├→ Execute Query                            │
│   └→ Return DataFrame                         │
│                                                │
│ RE_VISUALIZE → _handle_revisualization()      │
│   ├→ Apply previous filters                   │
│   ├→ Generate new visualization               │
│   └→ Return with preserved context            │
│                                                │
│ TRANSFORM → _handle_transformation()          │
│   ├→ Generate pandas transformation code      │
│   ├→ Execute safely                           │
│   └→ Return transformed DataFrame             │
└───────────────────────────────────────────────┘
    ↓
┌───────────────────────────────────────────────┐
│ Step 4: Answer Generation                     │
│ _generate_answer()                            │
│ • LLM generates natural language response     │
│ • Includes data insights and statistics       │
└───────────────────────────────────────────────┘
    ↓
┌───────────────────────────────────────────────┐
│ Step 5: Visualization Decision                │
│ _should_visualize()                           │
│ • Analyze question for viz keywords           │
│ • LLM recommends chart type                   │
│ • Return VisualizationResponse model          │
└───────────────────────────────────────────────┘
    ↓
┌───────────────────────────────────────────────┐
│ Step 6: Chart Creation                        │
│ _create_visualization()                       │
│ • Create Plotly figure based on type          │
│ • Configure axes, colors, legends             │
│ • Return interactive chart                    │
└───────────────────────────────────────────────┘
    ↓
┌───────────────────────────────────────────────┐
│ Step 7: State Update                          │
│ _update_conversation_state()                  │
│ • Add user message                            │
│ • Add assistant message with metadata         │
│ • Store DataFrame snapshot                    │
│ • Store visualization as JSON                 │
│ • Update data contexts                        │
└───────────────────────────────────────────────┘
    ↓
┌───────────────────────────────────────────────┐
│ Step 8: Conversation Persistence              │
│ save_current_conversation()                   │
│ • Export conversation state to JSON           │
│ • Save to conversations/<uuid>.json           │
│ • Update conversation list in UI              │
└───────────────────────────────────────────────┘
    ↓
[Gradio UI] Display:
├→ Text Answer
├→ Interactive Chart (Plotly)
└→ Data Table (HTML)

└→ Data Table (HTML)
```

---

## CORE COMPONENTS DEEP DIVE

### 1. QueryAgentEnhanced Class

**File**: `QueryAgent_Ollama_Enhanced.py`  
**Primary Responsibility**: Orchestrate question answering with context awareness

#### Constructor Parameters

```python
QueryAgentEnhanced(
    source_db_path: str,              # Path to SQLite database
    vector_db_path: str = "./chroma_db_768dim",  # Path to ChromaDB
    llm_model: str = "qwen2.5:7b",    # Ollama model name
    conversation_state: Optional[ConversationState] = None,
    max_context_messages: int = 10,   # Max messages to keep in context
    max_data_contexts: int = 20,      # Max data contexts to retain
    temperature: float = 0.1,         # LLM temperature (0.0-1.0)
    ollama_base_url: str = "http://localhost:11434",
    embedding_model: str = "nomic-embed-text"  # 768-dim embeddings
)
```

**What Happens During Initialization:**

1. **Database Connection**:
   ```python
   self.conn = sqlite3.connect(source_db_path, check_same_thread=False)
   self.db = SQLDatabase.from_uri(f"sqlite:///{source_db_path}")
   ```
   - Creates persistent SQLite connection
   - Initializes LangChain SQLDatabase wrapper
   - Allows thread-safe operations

2. **Vector Database Setup**:
   ```python
   self._setup_vector_database()
   ```
   - Connects to ChromaDB at specified path
   - Retrieves `table_metadata` and `column_metadata` collections
   - Loads all metadata into memory for fast access

3. **LLM Initialization**:
   ```python
   self.llm = ChatOllama(
       model=llm_model,
       base_url=ollama_base_url,
       temperature=temperature,
       num_ctx=4096,          # Context window size
       num_predict=1024,      # Max tokens to generate
       repeat_penalty=1.1,    # Prevent repetition
       timeout=120            # Request timeout
   )
   ```

4. **Chain Creation**:
   ```python
   self.query_chain = create_sql_query_chain(self.llm, self.db)
   ```
   - Creates LangChain SQL query generation chain
   - Automatically includes schema information

5. **Parser Setup**:
   ```python
   self.viz_parser = PydanticOutputParser(pydantic_object=VisualizationResponse)
   ```
   - Initializes structured output parsers
   - Ensures LLM responses match expected format

#### Core Methods

##### `answer_question_with_context(question: str, reuse_data: bool = False) -> Dict[str, Any]`

**Purpose**: Main entry point for processing user questions with full context awareness.

**Algorithm Flow**:

```
INPUT: User question string
↓
1. Analyze Intent
   _analyze_question_intent(question)
   ↓
   • Send question + recent conversation to LLM
   • LLM returns IntentAnalysis:
     - intent: NEW_QUERY | RE_VISUALIZE | TRANSFORM | COMBINE | COMPARE | CLARIFY
     - references_previous: bool
     - referenced_concepts: List[str]
     - needs_context: bool
     - confidence: float (0.0-1.0)
   
2. Check Previous Reference
   _check_previous_reference(question)
   ↓
   • Search for keywords: "that", "this", "previous", etc.
   • If found, retrieve latest DataFrame from conversation_state
   • Return (references_found: bool, df: Optional[DataFrame])

3. Route Based on Intent & Data Availability
   ↓
   ├─ [Has Previous DF + RE_VISUALIZE Intent]
   │  └→ _handle_revisualization(question, df)
   │     ├→ Extract filters from previous SQL
   │     ├→ Apply filters to DataFrame
   │     ├→ Generate new visualization
   │     └→ Preserve context and filters
   │
   ├─ [Has Previous DF + TRANSFORM Intent]
   │  └→ _handle_transformation(question, df)
   │     ├→ LLM generates pandas code
   │     ├→ Execute in safe environment
   │     └→ Return transformed data
   │
   └─ [NEW_QUERY or No Previous DF]
      └→ _process_new_query(question, intent)
         ├→ Search vector DB for metadata
         ├→ Build context prompt
         ├→ Generate SQL with retry logic
         ├→ Clean & validate SQL
         ├→ Execute query
         └→ Return results

4. Generate Natural Language Answer
   _generate_answer(question, df, sql_query)
   ↓
   • Create prompt with question + data summary
   • LLM generates insights and explanations
   • Return human-readable answer

5. Step5: Determine Visualization
   _should_visualize(question, df)
   ↓
   • Check for viz keywords in question
   • If requested, LLM analyzes data structure
   • Returns VisualizationResponse with:
     - should_visualize: bool
     - primary_chart: str (bar/line/pie/scatter/box/etc.)
     - x_axis, y_axis, color_by: column names
     - title: str
     - rationale: str

6. Create Visualization
   _create_visualization(df, viz_response)
   ↓
   • Based on chart type, create Plotly figure
   • Configure styling, axes, legends
   • Return interactive chart object

7. Update Conversation State
   _update_conversation_state(question, result, intent)
   ↓
   • Add Message objects for user and assistant
   • Create DataFrame snapshot (first 50 rows as dict)
   • Serialize Plotly figure to JSON string
   • Add DataContext with query info
   • Add VisualizationRecord
   • Auto-cleanup old contexts (keep last 10)

OUTPUT: Dict {
    success: bool,
    question: str,
    sql_query: str,
    answer: str,
    data: DataFrame,
    visualization: {chart: Figure, type: str, rationale: str},
    intent: str,
    reused_data: bool,
    conversation_id: str
}
```

**Key Features**:
- **Retry Logic**: SQL generation retries up to 2 times on failure
- **Error Recovery**: If execution fails, feeds error back to LLM for correction
- **Context Preservation**: Maintains conversation flow across multiple turns
- **Smart Caching**: Reuses previous DataFrames when appropriate

##### `_analyze_question_intent(question: str) -> IntentAnalysis`

**Purpose**: Classify user's question to determine processing strategy.

**Implementation**:

```python
def _analyze_question_intent(self, question: str) -> IntentAnalysis:
    # Get recent conversation context
    recent_messages = self.conversation_state.get_recent_messages(10)
    context_str = "\n".join([f"- {msg.role}: {msg.content}" for msg in recent_messages])
    
    # Build intent analysis prompt
    intent_prompt = f"""Analyze this question and determine the user's intent.

Recent conversation:
{context_str if context_str else "No previous conversation"}

Current question: "{question}"

Keywords indicating intent:
- NEW_QUERY: "show me", "what are", "list all", "find", "get"
- RE_VISUALIZE: "show as", "visualize as", "make a", "create chart", "different chart"
- TRANSFORM: "calculate", "add", "filter", "sort", "group by"
- COMBINE: "merge with", "combine", "join with", "add to"
- COMPARE: "compare", "difference between", "vs", "versus"
- CLARIFY: "what do you mean", "explain", "why"

Words indicating reference to previous: "that", "this", "these", "those", "previous", "last", "earlier", "above"

Return JSON with:
- intent: one of [new_query, re_visualize, transform, combine, compare, clarify]
- references_previous: true/false
- referenced_concepts: list of concepts mentioned (e.g., ["sales", "products"])
- needs_context: true if previous data is needed
- confidence: 0.0 to 1.0

Only return valid JSON, no other text."""
    
    # Invoke LLM
    response = self.llm.invoke(intent_prompt)
    content = response.content.strip()
    
    # Extract JSON from response (handles markdown code blocks)
    if "```json" in content:
        content = content.split("```json")[1].split("```")[0].strip()
    elif "```" in content:
        content = content.split("```")[1].split("```")[0].strip()
    
    # Parse to Pydantic model
    intent_data = json.loads(content)
    return IntentAnalysis(**intent_data)
```

**Output Example**:
```python
IntentAnalysis(
    intent="re_visualize",
    references_previous=True,
    referenced_concepts=["profit margin", "categories"],
    needs_context=True,
    confidence=0.9
)
```

##### `_generate_sql_with_retry(question: str, context_prompt: str, metadata_str: str, max_retries: int = 2) -> str`

**Purpose**: Generate SQL with automatic retry on failure.

**Algorithm**:

```
FOR attempt IN range(max_retries):
    TRY:
        1. Combine context_prompt + metadata_str
        2. Invoke query_chain with combined prompt
        3. IF sql_query is empty:
           - Log warning
           - Continue to next attempt
        4. RETURN sql_query
    
    EXCEPT Exception as e:
        - Log error with attempt number
        - IF last attempt:
          - RAISE exception
        - ELSE:
          - Continue to next attempt

IF all attempts fail:
    RAISE Exception("Failed to generate SQL after all retries")
```

##### `_clean_sql(query: str) -> str`

**Purpose**: Comprehensive SQL cleaning and sanitization.

**Steps**:

1. **Remove Markdown Fences**:
   ```python
   q = re.sub(r"```\w*", "", q)
   ```

2. **Extract Last SQL Marker**:
   ```python
   marker_iter = list(re.finditer(r"(?i)(sqlquery|sql query|sql|query)\s*:", q))
   if marker_iter:
       q = q[marker_iter[-1].end():]
   ```

3. **Remove Explanatory Text**:
   ```python
   q = re.sub(r"(?i)^.*?(?:here'?s?\s+(?:the\s+)?(?:sql\s+)?query[:\s]+)", "", q)
   ```

4. **Extract SELECT/WITH**:
   ```python
   cte_match = re.search(r"(?i)\bwith\s+[A-Za-z_][\w]*\s+as", q)
   select_match = re.search(r"(?i)\bselect\b", q)
   
   if cte_match and (not select_match or cte_match.start() <= select_match.start()):
       q = q[cte_match.start():]
   elif select_match:
       q = q[select_match.start():]
   ```

5. **Balance Quotes**:
   ```python
   single_quote_count = query.count("'")
   if single_quote_count % 2 == 1:
       query = query + "'"
   ```

6. **Fix Common Syntax Issues**:
   - Adjacent quoted strings: `AS "Total" "Sales"` → `AS "Total Sales"`
   - Unquoted aliases with spaces
   - Missing closing quotes in GROUP BY/ORDER BY

7. **Collapse Whitespace**:
   ```python
   q = re.sub(r"\s+", " ", q).strip()
   ```

##### `_validate_and_fix_tables(sql_query: str) -> str`

**Purpose**: Validate table/column references and fix invalid ones.

**Algorithm**:

```
1. Get Valid Tables
   - Query SQLite master table
   - Extract CTE names from query
   - Combine into valid_tables set

2. Build Column Map
   FOR each table IN valid_tables:
       - Get columns via PRAGMA table_info
       - Map column_name.lower() → (table, original_column_name)

3. Analyze Query Aliases
   _analyze_query_aliases(sql_query)
   - Extract FROM/JOIN aliases
   - Track: valid_aliases, base_to_alias, alias_to_table

4. Find Invalid JOIN Tables
   - Scan for JOIN patterns
   - Identify tables not in valid_tables
   - Mark as invalid_tables

5. Fix Invalid References
   IF invalid_tables exist:
       - Remove JOIN clauses with invalid tables
       - Replace invalid_table.column with valid_table.column
       - Fix aggregate functions: SUM(invalid.col) → SUM(valid.col)
       - Cleanup broken clauses (empty WHERE, trailing commas)

6. Fix Window Functions
   - Detect SUM(alias.column) OVER ()
   - Verify alias and column exist in subquery outputs
   - Replace with correct column references

7. Replace Unknown Aliases
   - Find all table.column references
   - If table not in valid_aliases:
     - Look up in base_to_alias mapping
     - Replace with known alias

RETURN: Fixed SQL query
```

**Example Fix**:
```sql
-- BEFORE (Invalid)
SELECT 
    s.region, 
    SUM(invalid_table.amount) as total
FROM sales s
LEFT JOIN invalid_table ON s.id = invalid_table.sale_id
GROUP BY s.region

-- AFTER (Fixed)
SELECT 
    s.region, 
    SUM(s.amount) as total
FROM sales s
GROUP BY s.region
```

##### `_should_visualize(question: str, df: pd.DataFrame) -> VisualizationResponse`

**Purpose**: Determine if visualization is appropriate and recommend type.

**Decision Logic**:

```
1. Early Rejection Checks:
   IF df.empty OR len(df) < 2:
       RETURN VisualizationResponse(
           should_visualize=False,
           rationale="Not enough data"
       )

2. Keyword Detection:
   viz_keywords = ['visualize', 'plot', 'chart', 'graph', 'show', 
                   'display', 'pie', 'bar', 'line', 'scatter']
   IF NO keywords in question:
       RETURN should_visualize=False

3. LLM Analysis:
   Prompt:
   - Question
   - Data info (rows, columns, types)
   - Sample data (first 5 rows)
   
   LLM Returns:
   {
       "should_visualize": true,
       "chart_types": ["bar", "line"],
       "primary_chart": "bar",
       "x_axis": "category",
       "y_axis": "sales",
       "color_by": "region",
       "title": "Sales by Category",
       "visualization_rationale": "Bar chart best shows comparison across categories"
   }

4. Fallback to Simple Rules:
   IF LLM fails:
       - Box plot if "box" or "distribution" in question
       - Bar chart as default
       - Auto-select first categorical for X, first numeric for Y
```

##### `_create_visualization(df: pd.DataFrame, viz_response: VisualizationResponse) -> go.Figure`

**Purpose**: Create Plotly visualization based on recommendations.

**Chart Types Supported**:

1. **Bar Chart**:
   ```python
   fig = px.bar(df, x=x_axis, y=y_axis, color=color_by, title=title)
   if color_by:
       fig.update_layout(showlegend=True)
   ```

2. **Multiple Bar Chart** (Grouped):
   ```python
   # If y_axis is a list of columns
   df_melted = df.melt(
       id_vars=[x_axis],
       value_vars=y_axis,
       var_name='Series',
       value_name='Value'
   )
   fig = px.bar(df_melted, x=x_axis, y='Value', color='Series', 
                barmode='group', title=title)
   ```

3. **Line Chart**:
   ```python
   fig = px.line(df, x=x_axis, y=y_axis, color=color_by, 
                 title=title, markers=True)
   ```

4. **Pie Chart**:
   ```python
   # Limit to top 10 for readability
   df_pie = df.nlargest(10, y_axis) if len(df) > 10 else df
   fig = px.pie(df_pie, names=x_axis, values=y_axis, title=title)
   fig.update_traces(textposition='inside', textinfo='percent+label')
   fig.update_layout(showlegend=True)
   ```

5. **Scatter Plot**:
   ```python
   fig = px.scatter(df, x=x_axis, y=y_axis, color=color_by, title=title)
   ```

6. **Histogram**:
   ```python
   fig = px.histogram(df, x=x_axis, title=title)
   ```

7. **Box Plot**:
   ```python
   fig = px.box(df, x=x_axis, y=y_axis, color=x_axis, 
                title=title, points="outliers")
   fig.update_traces(marker=dict(size=4, opacity=0.6), boxmean='sd')
   ```

**Common Styling**:
```python
fig.update_layout(
    template="plotly",
    title_font_size=16,
    showlegend=True,
    hovermode='closest',
    height=500,
    xaxis=dict(showgrid=True, gridwidth=1, gridcolor='LightGray'),
    yaxis=dict(showgrid=True, gridwidth=1, gridcolor='LightGray'),
    legend=dict(
        orientation="v",
        yanchor="top",
        y=0.99,
        xanchor="left",
        x=1.01,
        bgcolor="rgba(255, 255, 255, 0.8)",
        bordercolor="rgba(0, 0, 0, 0.2)",
        borderwidth=1
    )
)
```

---

### 2. ConversationState Class

**File**: `conversation_manager.py`  
**Primary Responsibility**: Manage conversation history, data contexts, and persistence

#### Data Classes

##### `Message`
```python
@dataclass
class Message:
    role: str              # "user" or "assistant"
    content: str           # Message text
    timestamp: datetime    # When message was created
    sql_query: Optional[str] = None           # Generated SQL (assistant only)
    dataframe_snapshot: Optional[Dict] = None # Data metadata
    visualization: Optional[str] = None       # Chart type
    figure_json: Optional[str] = None         # Plotly figure as JSON
    metadata: Dict = field(default_factory=dict)
```

**DataFrame Snapshot Structure**:
```python
{
    "columns": ["col1", "col2", "col3"],
    "row_count": 1000,
    "sample": {
        "col1": {"0": "val1", "1": "val2", ...},  # First 50 rows
        "col2": {"0": 10, "1": 20, ...},
        "col3": {"0": "A", "1": "B", ...}
    }
}
```

##### `DataContext`
```python
@dataclass
class DataContext:
    query: str             # SQL query executed
    columns: List[str]     # Column names in result
    row_count: int         # Number of rows returned
    sample_data: Dict      # First 5 rows as dict
    timestamp: datetime    # When context was created
```

##### `VisualizationRecord`
```python
@dataclass
class VisualizationRecord:
    question: str          # User's question
    chart_type: str        # Type of chart created
    data_summary: str      # Brief description of data
    timestamp: datetime    # When viz was created
```

#### Core Methods

##### `add_message(message: Message)`

**Purpose**: Add a message to conversation history.

**Implementation**:
```python
def add_message(self, message: Message):
    self.messages.append(message)
```

**Usage Pattern**:
```python
# User message
conversation_state.add_message(Message(
    role="user",
    content="What are the top 5 sales?",
    metadata={"intent": "new_query"}
))

# Assistant message
conversation_state.add_message(Message(
    role="assistant",
    content="Here are the top 5 sales...",
    sql_query="SELECT * FROM sales ORDER BY amount DESC LIMIT 5",
    dataframe_snapshot={
        "columns": ["id", "amount", "date"],
        "row_count": 5,
        "sample": {...}
    },
    visualization="bar",
    figure_json='{"data": [...], "layout": {...}}',
    metadata={"intent": "new_query", "success": True}
))
```

##### `add_data_context(context: DataContext)`

**Purpose**: Store query result metadata.

**Implementation**:
```python
def add_data_context(self, context: DataContext):
    self.data_contexts.append(context)
    # Keep only last 10 contexts to manage memory
    if len(self.data_contexts) > 10:
        self.data_contexts = self.data_contexts[-10:]
```

**Auto-Cleanup**: Automatically limits to last 10 contexts to prevent memory bloat.

##### `get_recent_messages(n: int = 5) -> List[Message]`

**Purpose**: Retrieve last N messages for context building.

**Implementation**:
```python
def get_recent_messages(self, n: int = 5) -> List[Message]:
    return self.messages[-n:] if len(self.messages) >= n else self.messages
```

**Usage**: Used by `_analyze_question_intent()` and `_build_context_prompt()` to provide conversation history to LLM.

##### `export_conversation() -> Dict`

**Purpose**: Serialize conversation state for persistence.

**Implementation**:
```python
def export_conversation(self) -> Dict:
    return {
        "conversation_id": self.conversation_id,
        "start_time": self.start_time.isoformat(),
        "message_count": len(self.messages),
        "messages": [
            {
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat(),
                "sql_query": msg.sql_query,
                "dataframe_snapshot": msg.dataframe_snapshot,
                "visualization": msg.visualization,
                "figure_json": msg.figure_json,
                "metadata": msg.metadata
            }
            for msg in self.messages
        ],
        "data_contexts": [
            {
                "query": ctx.query,
                "columns": ctx.columns,
                "row_count": ctx.row_count,
                "sample_data": ctx.sample_data,
                "timestamp": ctx.timestamp.isoformat()
            }
            for ctx in self.data_contexts
        ],
        "visualizations": [
            {
                "question": viz.question,
                "chart_type": viz.chart_type,
                "data_summary": viz.data_summary,
                "timestamp": viz.timestamp.isoformat()
            }
            for viz in self.visualizations
        ]
    }
```

**Output Format**: See [Data Structures & Examples](#data-structures--examples) section for full JSON example.

##### `import_conversation(data: Dict)`

**Purpose**: Restore conversation state from JSON.

**Algorithm**:
```
1. Parse conversation_id and start_time
2. FOR each message in data["messages"]:
   - Create Message object
   - Parse ISO timestamps to datetime
   - Restore all fields including metadata
3. FOR each context in data["data_contexts"]:
   - Create DataContext object
   - Parse timestamps
4. FOR each viz in data["visualizations"]:
   - Create VisualizationRecord object
5. Update self.messages, self.data_contexts, self.visualizations
```

---

### 3. Gradio UI (app_gradio_enhanced.py)

**Primary Responsibility**: Web interface for user interaction

#### Global State Management

```python
# Global variables (module-level)
agent: Optional[QueryAgentEnhanced] = None
conversation_state: Optional[ConversationState] = None
CONVERSATIONS_DIR = "conversations"
```

**Why Global**: Gradio functions are stateless; global state persists across invocations.

#### Key Functions

##### `initialize_agent(db_path: str, vector_db: str, model: str) -> Tuple[str, gr.update]`

**Purpose**: Initialize the QueryAgentEnhanced with user-specified parameters.

**Steps**:
1. Validate database file exists
2. Create new ConversationState
3. Initialize QueryAgentEnhanced with parameters
4. Load conversation list from disk
5. Return status message and updated history dropdown

**Returns**:
- Status message: "✅ Agent Ready" or error
- Gradio update for history dropdown

##### `process_question(question: str, history: List) -> Tuple[List, gr.update]`

**Purpose**: Process user question and update chat history.

**Algorithm**:
```
INPUT: question (str), history (List of tuples)

1. Validate agent exists
2. Call agent.answer_question_with_context(question)
3. Extract result components:
   - answer (text)
   - visualization (Plotly figure)
   - data (DataFrame)

4. Update history list:
   history.append((question, answer))
   
   IF visualization exists:
       history.append((None, gr.Plot(value=fig)))
   
   IF data exists:
       df_display = data.head(100)
       html_table = df_display.to_html()
       history.append((None, table_html))

5. Save conversation to disk:
   save_current_conversation()

6. Update conversation list in sidebar:
   new_list = get_conversation_list()

OUTPUT: (updated_history, gr.update(choices=new_list))
```

**History Format**:
```python
[
    ("User question 1", "Assistant answer 1"),
    (None, gr.Plot(...)),                    # Chart
    (None, "<div>HTML Table</div>"),        # Data table
    ("User question 2", "Assistant answer 2"),
    ...
]
```

##### `load_conversation(filename: str) -> Tuple[List, str]`

**Purpose**: Load and reconstruct a saved conversation.

**Algorithm**:
```
1. Read JSON file from conversations/<filename>
2. Create new ConversationState
3. Import data using conversation_state.import_conversation(data)
4. Update global conversation_state and agent.conversation_state
5. Reconstruct history for display:
   FOR each message in conversation_state.messages:
       IF role == "user":
           pending_user = content
       ELIF role == "assistant":
           - Add (user, assistant) text tuple
           - IF figure_json exists:
               - Parse JSON to Plotly figure
               - Add (None, gr.Plot(fig)) tuple
           - IF dataframe_snapshot exists:
               - Reconstruct DataFrame from sample
               - Convert to HTML table
               - Add (None, table_html) tuple
6. RETURN (history, status_message)
```

**Reconstruction Challenges**:
- Plotly figures stored as JSON strings must be deserialized
- DataFrames reconstructed from sample data (only first 50 rows saved)
- Order must be preserved: user → assistant → chart → table

##### `save_current_conversation()`

**Purpose**: Persist current conversation to disk.

**Implementation**:
```python
def save_current_conversation():
    if conversation_state and conversation_state.messages:
        ensure_conversations_dir()  # Create dir if not exists
        data = conversation_state.export_conversation()
        filename = f"{conversation_state.conversation_id}.json"
        filepath = os.path.join(CONVERSATIONS_DIR, filename)
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
```

**Trigger Points**:
- After every successful question processing
- Automatic (no user action required)

##### `get_conversation_list() -> List[Tuple[str, str]]`

**Purpose**: Get list of saved conversations for sidebar dropdown.

**Implementation**:
```python
def get_conversation_list() -> List[Tuple[str, str]]:
    ensure_conversations_dir()
    files = [f for f in os.listdir(CONVERSATIONS_DIR) if f.endswith('.json')]
    files.sort(key=lambda x: os.path.getmtime(os.path.join(CONVERSATIONS_DIR, x)), 
               reverse=True)
    
    choices = []
    for f in files:
        path = os.path.join(CONVERSATIONS_DIR, f)
        with open(path, 'r') as file:
            data = json.load(file)
        
        # Extract title from first user message
        title = "New Conversation"
        for msg in data.get('messages', []):
            if msg['role'] == 'user':
                title = msg['content'][:30] + "..." if len(msg['content']) > 30 else msg['content']
                break
        
        # Format timestamp
        ts = data.get('start_time', datetime.now().isoformat())
        dt = datetime.fromisoformat(ts)
        date_str = dt.strftime("%m/%d %H:%M")
        
        label = f"{date_str} - {title}"
        choices.append((label, f))  # (display_label, filename)
    
    return choices
```

**Output Example**:
```python
[
    ("11/20 22:50 - I'm trying to understand ou...", "2e6a2e96-1a3f-43f8-95cb-2a1debc1135a.json"),
    ("11/19 15:30 - Show me top 5 sales...", "df8d33d4-744a-4f66-8330-d03ce7f17844.json"),
    ...
]
```

#### UI Layout

**Sidebar** (Left Column):
```python
with gr.Column(scale=1, elem_classes="sidebar", min_width=300):
    gr.Markdown("### 🗄️ Chat History")
    with gr.Row():
        new_chat_btn = gr.Button("+ New Chat")
        delete_btn = gr.Button("🗑️")
    
    history_list = gr.Radio(
        label="Recent Conversations",
        choices=get_conversation_list(),
        interactive=True
    )
    
    with gr.Accordion("⚙️ Settings", open=True):
        db_input = gr.Textbox(label="Database Path", value="analysis.db")
        vec_input = gr.Textbox(label="Vector DB", value="./chroma_db_768dim")
        model_input = gr.Dropdown(label="Model", choices=["qwen2.5:7b", "llama3", "mistral"])
        init_btn = gr.Button("Initialize the LLM Agent")
        init_status = gr.Markdown("Not Connected")
```

**Main Chat Area** (Right Column):
```python
with gr.Column(scale=4, elem_classes="chat-area"):
    chatbot = gr.Chatbot(
        height=750,
        avatar_images=(None, "https://cdn-icons-png.flaticon.com/512/4712/4712027.png"),
        render_markdown=True,
        type="tuples",
        sanitize_html=False  # Allow HTML tables
    )
    
    with gr.Row():
        msg_input = gr.Textbox(
            scale=9,
            placeholder="Ask a question about your data...",
            lines=1
        )
        submit_btn = gr.Button("➤", scale=1, variant="primary")
```

#### Event Wiring

```python
# Initialize agent
init_btn.click(
    fn=initialize_agent,
    inputs=[db_input, vec_input, model_input],
    outputs=[init_status, history_list]
)

# New chat
new_chat_btn.click(
    fn=start_new_chat,
    outputs=[chatbot, init_status]
)

# Delete current conversation
delete_btn.click(
    fn=delete_conversation,
    outputs=[chatbot, history_list, init_status]
)

# Load conversation from sidebar
history_list.select(
    fn=load_conversation,
    inputs=[history_list],
    outputs=[chatbot, init_status]
)

# Submit question (two triggers: button click and Enter key)
submit_args = {
    "fn": process_question,
    "inputs": [msg_input, chatbot],
    "outputs": [chatbot, history_list]
}
msg_input.submit(**submit_args).then(lambda: "", outputs=msg_input)  # Clear input
submit_btn.click(**submit_args).then(lambda: "", outputs=msg_input)
```

#### Custom CSS

```css
.sidebar {
    padding: 20px;
    border-right: 1px solid var(--border-color-primary);
    height: 100vh;
    overflow-y: auto;
}

.chat-area {
    padding: 20px;
    height: 100vh;
    overflow-y: auto;
}

.data-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.9em;
}

.data-table th {
    background-color: var(--background-fill-secondary);
    padding: 8px;
    text-align: left;
    border-bottom: 2px solid var(--border-color-primary);
}

.data-table td {
    padding: 8px;
    border-bottom: 1px solid var(--border-color-primary);
}

.table-container {
    overflow-x: auto;
    border: 1px solid var(--border-color-primary);
    border-radius: 8px;
    padding: 10px;
}
```

---

## DATA FLOW & WORKFLOWS

### Workflow 1: First-Time Setup (Database Analysis)

**Script**: `analyze_existing_db.py`  
**Purpose**: One-time analysis to create vector database with metadata

```
┌────────────────────────────────────────────────────────┐
│ Step 1: User Runs Analyzer                            │
│ $ python analyze_existing_db.py analysis.db           │
└────────────────────────────────────────────────────────┘
                        ↓
┌────────────────────────────────────────────────────────┐
│ Step 2: Initialize Connections                         │
│ • Connect to source SQLite database                    │
│ • Initialize Ollama LLM (qwen2.5:7b)                   │
│ • Create/connect to ChromaDB                           │
│ • Setup prompt templates                               │
└────────────────────────────────────────────────────────┘
                        ↓
┌────────────────────────────────────────────────────────┐
│ Step 3: Discover Tables                                │
│ get_table_names()                                      │
│ • Query sqlite_master for table names                  │
│ • Exclude system tables (sqlite_%)                     │
│ • Return list: ["sales", "products", "customers"]      │
└────────────────────────────────────────────────────────┘
                        ↓
┌────────────────────────────────────────────────────────┐
│ Step 4: For Each Table - Analyze Metadata             │
│ _analyze_table_metadata(table_name, df)               │
│                                                        │
│ LLM Input:                                             │
│ - Table name                                           │
│ - Column list                                          │
│ - First 5 rows sample                                  │
│ - Row count                                            │
│                                                        │
│ LLM Output (MetadataResponse):                         │
│ {                                                      │
│   "table_name": "sales",                               │
│   "description": "Transaction records for product      │
│                   sales with timestamps and amounts",  │
│   "category": "financial",                             │
│   "business_context": "Core revenue tracking system",  │
│   "suggested_primary_key": "transaction_id",           │
│   "data_quality_notes": [                              │
│     "Some null values in customer_id",                 │
│     "Date range: 2023-01-01 to 2024-12-31"            │
│   ]                                                    │
│ }                                                      │
└────────────────────────────────────────────────────────┘
                        ↓
┌────────────────────────────────────────────────────────┐
│ Step 5: For Each Column - Analyze Details             │
│ _analyze_column(table_name, column_name, column_data) │
│                                                        │
│ LLM Input:                                             │
│ - Table and column names                               │
│ - Sample values (first 10)                             │
│ - Unique count, null count                             │
│                                                        │
│ LLM Output (DataTypeResponse):                         │
│ {                                                      │
│   "sql_type": "REAL",                                  │
│   "python_type": "float",                              │
│   "description": "Transaction amount in USD",          │
│   "business_meaning": "Revenue generated from sale",   │
│   "constraints": ["NOT NULL", "CHECK > 0"],            │
│   "is_nullable": false,                                │
│   "suggested_index": true                              │
│ }                                                      │
└────────────────────────────────────────────────────────┘
                        ↓
┌────────────────────────────────────────────────────────┐
│ Step 6: Generate Embeddings                            │
│ _get_embedding(text)                                   │
│                                                        │
│ For Table:                                             │
│ text = "Table: sales\nDescription: Transaction         │
│         records...\nCategory: financial..."            │
│ → POST to Ollama /api/embeddings                       │
│ → Model: nomic-embed-text                              │
│ → Returns: [0.123, -0.456, ...] (768 dimensions)       │
│                                                        │
│ For Each Column:                                       │
│ text = "Table: sales\nColumn: amount\nType: REAL..."   │
│ → Generate 768-dim embedding                           │
└────────────────────────────────────────────────────────┘
                        ↓
┌────────────────────────────────────────────────────────┐
│ Step 7: Store in ChromaDB                              │
│ save_analysis(analysis)                                │
│                                                        │
│ Table Collection:                                      │
│ • ID: "table_sales"                                    │
│ • Document: "Table: sales\nDescription: ..."           │
│ • Embedding: [768 floats]                              │
│ • Metadata: {table_name, description, category, ...}   │
│                                                        │
│ Column Collection:                                     │
│ • ID: "column_sales_amount"                            │
│ • Document: "Table: sales\nColumn: amount..."          │
│ • Embedding: [768 floats]                              │
│ • Metadata: {table_name, column_name, sql_type, ...}   │
└────────────────────────────────────────────────────────┘
                        ↓
┌────────────────────────────────────────────────────────┐
│ Step 8: Repeat for All Tables                         │
│ • Process next table                                   │
│ • Accumulate metadata in ChromaDB                      │
│ • Log progress                                         │
└────────────────────────────────────────────────────────┘
                        ↓
┌────────────────────────────────────────────────────────┐
│ Step 9: Analysis Complete                              │
│ print_summary()                                        │
│ ════════════════════════════════════════════           │
│ 📊 ANALYSIS SUMMARY                                    │
│ ════════════════════════════════════════════           │
│ Tables Analyzed: 3                                     │
│ Total Columns: 45                                      │
│ Vector Database: ./chroma_db_768dim                    │
│ ════════════════════════════════════════════           │
└────────────────────────────────────────────────────────┘
```

**Time Estimate**: 5-10 minutes for database with 3-5 tables  
**Output**: ChromaDB at `./chroma_db_768dim/` with:
- `table_metadata` collection
- `column_metadata` collection
- All embeddings and metadata

---

### Workflow 2: CSV to Database Conversion

**Script**: `csv_to_db.py`  
**Purpose**: Convert CSV files to SQLite with LLM-inferred schema

```
┌────────────────────────────────────────────────────────┐
│ Step 1: User Runs Converter                            │
│ $ python csv_to_db.py sales.csv --db analysis.db      │
└────────────────────────────────────────────────────────┘
                        ↓
┌────────────────────────────────────────────────────────┐
│ Step 2: Load CSV                                        │
│ df = pd.read_csv("sales.csv")                          │
│ • Detect encoding automatically                         │
│ • Parse dates if possible                               │
│ • Load entire file into memory                          │
└────────────────────────────────────────────────────────┘
                        ↓
┌────────────────────────────────────────────────────────┐
│ Step 3: Analyze File Metadata                          │
│ analyze_metadata(df, filename)                         │
│                                                        │
│ LLM Prompt:                                            │
│ - Sheet/table name: "sales"                            │
│ - Columns: "transaction_id, date, amount, category"    │
│ - Sample data (first 5 rows)                           │
│                                                        │
│ LLM Response:                                          │
│ {                                                      │
│   "table_name": "sales_transactions",                  │
│   "description": "E-commerce sales records",           │
│   "category": "sales",                                 │
│   "business_context": "Online store transaction log",  │
│   "suggested_primary_key": "transaction_id",           │
│   "data_quality_notes": ["All dates in YYYY-MM-DD"]   │
│ }                                                      │
└────────────────────────────────────────────────────────┘
                        ↓
┌────────────────────────────────────────────────────────┐
│ Step 4: Analyze Each Column                            │
│ FOR col IN df.columns:                                 │
│     analyze_column(col, df[col])                       │
│                                                        │
│ Example for "amount" column:                           │
│ LLM Input:                                             │
│ - Column name: "amount"                                │
│ - Sample values: [45.50, 120.00, 67.25, ...]          │
│ - Unique count: 8,543                                  │
│ - Null count: 0                                        │
│                                                        │
│ LLM Output:                                            │
│ {                                                      │
│   "sql_type": "REAL",                                  │
│   "python_type": "float",                              │
│   "description": "Transaction amount in currency",     │
│   "business_meaning": "Sale price paid by customer",   │
│   "constraints": ["NOT NULL", "CHECK > 0"],            │
│   "is_nullable": false,                                │
│   "suggested_index": false                             │
│ }                                                      │
│                                                        │
│ Fallback: If LLM fails, use pandas type detection      │
│ • is_integer_dtype → INTEGER                           │
│ • is_float_dtype → REAL                                │
│ • is_datetime64_any_dtype → DATE                       │
│ • else → TEXT                                          │
└────────────────────────────────────────────────────────┘
                        ↓
┌────────────────────────────────────────────────────────┐
│ Step 5: Create Database Schema                         │
│ create_database(df, metadata, column_analysis)         │
│                                                        │
│ 1. Clean column names:                                 │
│    "Transaction ID" → "transaction_id"                 │
│    "Sale Amount ($)" → "sale_amount"                   │
│                                                        │
│ 2. Build CREATE TABLE DDL:                             │
│    CREATE TABLE IF NOT EXISTS sales_transactions (     │
│        transaction_id TEXT NOT NULL,                   │
│        date DATE,                                      │
│        amount REAL NOT NULL CHECK (amount > 0),        │
│        category TEXT                                   │
│    )                                                   │
│                                                        │
│ 3. Execute DDL to create table                         │
└────────────────────────────────────────────────────────┘
                        ↓
┌────────────────────────────────────────────────────────┐
│ Step 6: Type Conversion & Data Insertion               │
│                                                        │
│ Type Conversions:                                      │
│ • DATE columns → pd.to_datetime()                      │
│ • INTEGER columns → pd.to_numeric(downcast='integer')  │
│ • REAL columns → pd.to_numeric()                       │
│                                                        │
│ Bulk Insert:                                           │
│ df_clean.to_sql(                                       │
│     "sales_transactions",                              │
│     conn,                                              │
│     if_exists='replace',                               │
│     index=False                                        │
│ )                                                      │
└────────────────────────────────────────────────────────┘
                        ↓
┌────────────────────────────────────────────────────────┐
│ Step 7: Verification                                    │
│ SELECT COUNT(*) FROM sales_transactions                │
│ Expected: 10,000                                       │
│ Actual: 10,000 ✅                                      │
└────────────────────────────────────────────────────────┘
                        ↓
┌────────────────────────────────────────────────────────┐
│ Step 8: Success Report                                 │
│ ════════════════════════════════════════════           │
│ ✅ CONVERSION COMPLETE                                 │
│ ════════════════════════════════════════════           │
│ Database: analysis.db                                  │
│ Table: sales_transactions                              │
│ Description: E-commerce sales records                  │
│ Category: sales                                        │
│ Rows: 10,000                                           │
│ ════════════════════════════════════════════           │
└────────────────────────────────────────────────────────┘
```

**Time Estimate**: 2-5 minutes for 10,000 rows with 10 columns  
**Next Step**: Run `analyze_existing_db.py` to create vector database

---

### Workflow 3: Query Processing (Multi-Turn)

**Primary Script**: QueryAgent interacting through Gradio UI

#### Scenario: New Query (No Context)

**User**: "What are the top 5 sales by amount?"

```
┌────────────────────────────────────────────────────────┐
│ UI: process_question() receives user input            │
└────────────────────────────────────────────────────────┘
                        ↓
┌────────────────────────────────────────────────────────┐
│ agent.answer_question_with_context(question)          │
└────────────────────────────────────────────────────────┘
                        ↓
┌────────────────────────────────────────────────────────┐
│ Step 1: Intent Analysis                                │
│ _analyze_question_intent()                            │
│                                                        │
│ Input to LLM:                                          │
│ - Question: "What are the top 5 sales by amount?"      │
│ - Recent conversation: []                              │
│                                                        │
│ LLM Response:                                          │
│ {                                                      │
│   "intent": "new_query",                               │
│   "references_previous": false,                        │
│   "referenced_concepts": ["sales", "amount", "top 5"], │
│   "needs_context": false,                              │
│   "confidence": 0.95                                   │
│ }                                                      │
└────────────────────────────────────────────────────────┘
                        ↓
┌────────────────────────────────────────────────────────┐
│ Step 2: Metadata Retrieval                             │
│ _retrieve_metadata(question, top_k=5)                 │
│                                                        │
│ 1. Generate embedding for question:                    │
│    [0.234, -0.567, 0.123, ...] (768 dims)             │
│                                                        │
│ 2. Query ChromaDB table_collection:                    │
│    Similar tables ranked by semantic similarity        │
│    Result: ["sales", "transactions", "revenue"]        │
│                                                        │
│ 3. Query ChromaDB column_collection:                   │
│    Relevant columns: ["amount", "total_sales",         │
│                       "quantity", "price"]             │
│                                                        │
│ 4. Format metadata string:                             │
│    "Table: sales                                       │
│     Description: Transaction records...                │
│     Columns: amount (REAL), date (DATE)..."            │
└────────────────────────────────────────────────────────┘
                        ↓
┌────────────────────────────────────────────────────────┐
│ Step 3: SQL Generation                                 │
│ _generate_sql_with_retry()                            │
│                                                        │
│ Attempt 1:                                             │
│ LLM Input:                                             │
│ - Database schema (from SQLDatabase)                   │
│ - Metadata context (from ChromaDB)                     │
│ - Question: "What are the top 5 sales by amount?"      │
│                                                        │
│ LLM Output:                                            │
│ ```sql                                                 │
│ SELECT * FROM sales                                    │
│ ORDER BY amount DESC                                   │
│ LIMIT 5                                                │
│ ```                                                    │
└────────────────────────────────────────────────────────┘
                        ↓
┌────────────────────────────────────────────────────────┐
│ Step 4: SQL Cleaning & Validation                      │
│ _clean_sql() + _validate_and_fix_tables()             │
│                                                        │
│ Cleaning:                                              │
│ • Remove markdown fences                               │
│ • Extract SELECT statement                             │
│ • Balance quotes                                       │
│ • Fix syntax issues                                    │
│                                                        │
│ Validation:                                            │
│ • Check table exists: "sales" ✅                       │
│ • Check columns exist: "amount" ✅                     │
│ • Validate JOINs (if any)                              │
│                                                        │
│ Final SQL:                                             │
│ SELECT * FROM sales                                    │
│ ORDER BY amount DESC                                   │
│ LIMIT 5                                                │
└────────────────────────────────────────────────────────┘
                        ↓
┌────────────────────────────────────────────────────────┐
│ Step 5: Query Execution                                │
│ pd.read_sql_query(sql, conn)                           │
│                                                        │
│ Result DataFrame:                                      │
│   transaction_id    amount      date        category  │
│ 0    TXN-1234       1536.17   2024-03-15   Electronics│
│ 1    TXN-5678       1112.25   2024-02-28   Home       │
│ 2    TXN-9012        765.28   2024-01-12   Sports     │
│ 3    TXN-3456        508.85   2024-04-03   Fashion    │
│ 4    TXN-7890        246.47   2024-03-22   Beauty     │
│                                                        │
│ Shape: (5, 4)                                          │
└────────────────────────────────────────────────────────┘
                        ↓
┌────────────────────────────────────────────────────────┐
│ Step 6: Answer Generation                              │
│ _generate_answer(question, df, sql)                   │
│                                                        │
│ LLM Prompt:                                            │
│ - Question                                             │
│ - Data summary: "Found 5 rows with columns..."         │
│ - Sample data (first 10 rows)                          │
│                                                        │
│ LLM Response:                                          │
│ "The top 5 sales by amount are:                        │
│  1. $1,536.17 from Electronics (TXN-1234)              │
│  2. $1,112.25 from Home (TXN-5678)                     │
│  3. $765.28 from Sports (TXN-9012)                     │
│  4. $508.85 from Fashion (TXN-3456)                    │
│  5. $246.47 from Beauty (TXN-7890)                     │
│  The highest transaction was in Electronics."          │
└────────────────────────────────────────────────────────┘
                        ↓
┌────────────────────────────────────────────────────────┐
│ Step 7: Visualization Decision                         │
│ _should_visualize(question, df)                       │
│                                                        │
│ Check keywords: "top", "5", "sales" → No viz keywords │
│ Result: should_visualize = False                       │
│ (User didn't explicitly request visualization)         │
└────────────────────────────────────────────────────────┘
                        ↓
┌────────────────────────────────────────────────────────┐
│ Step 8: State Update                                   │
│ _update_conversation_state()                          │
│                                                        │
│ Add User Message:                                      │
│ Message(role="user",                                   │
│         content="What are the top 5 sales?",           │
│         metadata={"intent": "new_query"})              │
│                                                        │
│ Add Assistant Message:                                 │
│ Message(role="assistant",                              │
│         content="The top 5 sales...",                  │
│         sql_query="SELECT * FROM sales...",            │
│         dataframe_snapshot={                           │
│             "columns": ["transaction_id", ...],        │
│             "row_count": 5,                            │
│             "sample": {first 50 rows as dict}          │
│         },                                             │
│         visualization=None,                            │
│         metadata={"success": True})                    │
│                                                        │
│ Add Data Context:                                      │
│ DataContext(query="SELECT * FROM sales...",            │
│             columns=["transaction_id", "amount", ...], │
│             row_count=5)                               │
└────────────────────────────────────────────────────────┘
                        ↓
┌────────────────────────────────────────────────────────┐
│ Step 9: UI Display                                     │
│ process_question() returns updated history             │
│                                                        │
│ Gradio Chat Display:                                   │
│ ┌──────────────────────────────────────────┐          │
│ │ User: What are the top 5 sales by amount?│          │
│ │                                           │          │
│ │ Assistant: The top 5 sales by amount are:│          │
│ │ 1. $1,536.17 from Electronics...          │          │
│ │ 2. $1,112.25 from Home...                 │          │
│ │ ...                                       │          │
│ │                                           │          │
│ │ [Data Table with 5 rows displayed]        │          │
│ └──────────────────────────────────────────┘          │
└────────────────────────────────────────────────────────┘
                        ↓
┌────────────────────────────────────────────────────────┐
│ Step 10: Conversation Persistence                      │
│ save_current_conversation()                           │
│                                                        │
│ File: conversations/a1b2c3d4-uuid.json                 │
│ Content: Full conversation state as JSON               │
└────────────────────────────────────────────────────────┘
```

#### Scenario: Follow-Up Query with Visualization

**User**: "Show me those sales as a bar chart"

```
┌────────────────────────────────────────────────────────┐
│ Step 1: Intent Analysis                                │
│ _analyze_question_intent()                            │
│                                                        │
│ Input to LLM:                                          │
│ - Question: "Show me those sales as a bar chart"       │
│ - Recent conversation:                                 │
│   "- user: What are the top 5 sales by amount?         │
│    - assistant: The top 5 sales are..."                │
│                                                        │
│ LLM Response:                                          │
│ {                                                      │
│   "intent": "re_visualize",                            │
│   "references_previous": true,                         │
│   "referenced_concepts": ["those sales", "bar chart"], │
│   "needs_context": true,                               │
│   "confidence": 0.92                                   │
│ }                                                      │
└────────────────────────────────────────────────────────┘
                        ↓
┌────────────────────────────────────────────────────────┐
│ Step 2: Retrieve Previous Data                         │
│ _check_previous_reference()                           │
│                                                        │
│ Keywords detected: "those"                             │
│ → Search conversation_state for latest DataFrame       │
│                                                        │
│ Found: DataFrame from previous query (5 rows)          │
│   transaction_id    amount      date        category  │
│ 0    TXN-1234       1536.17   2024-03-15   Electronics│
│ 1    TXN-5678       1112.25   2024-02-28   Home       │
│ ...                                                    │
└────────────────────────────────────────────────────────┘
                        ↓
┌────────────────────────────────────────────────────────┐
│ Step 3: Route to Re-visualization Handler              │
│ _handle_revisualization(question, df)                 │
│                                                        │
│ 1. Extract filters from previous SQL:                  │
│    Previous SQL: SELECT * FROM sales ORDER BY          │
│                  amount DESC LIMIT 5                   │
│    Filters found: None                                 │
│                                                        │
│ 2. Apply filters to DataFrame: N/A                     │
│                                                        │
│ 3. Generate visualization recommendation:              │
│    _should_visualize(question, df)                    │
└────────────────────────────────────────────────────────┘
                        ↓
┌────────────────────────────────────────────────────────┐
│ Step 4: Visualization Decision                         │
│                                                        │
│ Detect keywords: "bar chart" ✅                        │
│                                                        │
│ LLM Prompt:                                            │
│ - Question: "Show me those sales as a bar chart"       │
│ - Data info: 5 rows, columns [transaction_id,          │
│               amount, date, category]                  │
│ - Numeric columns: [amount]                            │
│ - Sample data                                          │
│                                                        │
│ LLM Response:                                          │
│ {                                                      │
│   "should_visualize": true,                            │
│   "chart_types": ["bar"],                              │
│   "primary_chart": "bar",                              │
│   "x_axis": "category",                                │
│   "y_axis": "amount",                                  │
│   "color_by": "category",                              │
│   "title": "Top 5 Sales by Amount",                    │
│   "visualization_rationale": "Bar chart effectively    │
│        shows comparison of amounts across categories"  │
│ }                                                      │
└────────────────────────────────────────────────────────┘
                        ↓
┌────────────────────────────────────────────────────────┐
│ Step 5: Create Plotly Chart                            │
│ _create_visualization(df, viz_response)               │
│                                                        │
│ Code executed:                                         │
│ fig = px.bar(                                          │
│     df,                                                │
│     x="category",                                      │
│     y="amount",                                        │
│     color="category",                                  │
│     title="Top 5 Sales by Amount"                      │
│ )                                                      │
│ fig.update_layout(                                     │
│     showlegend=True,                                   │
│     height=500,                                        │
│     xaxis=dict(showgrid=True),                         │
│     yaxis=dict(showgrid=True)                          │
│ )                                                      │
│                                                        │
│ Result: Interactive Plotly Figure object               │
└────────────────────────────────────────────────────────┘
                        ↓
┌────────────────────────────────────────────────────────┐
│ Step 6: Generate Answer                                │
│ _generate_answer(question, filtered_df, previous_sql) │
│                                                        │
│ LLM Response:                                          │
│ "I've created a bar chart showing the top 5 sales      │
│  by amount. Electronics leads with $1,536.17,          │
│  followed by Home at $1,112.25. The visualization      │
│  clearly shows the distribution of high-value          │
│  transactions across different categories."            │
└────────────────────────────────────────────────────────┘
                        ↓
┌────────────────────────────────────────────────────────┐
│ Step 7: State Update                                   │
│ _update_conversation_state()                          │
│                                                        │
│ Add User Message:                                      │
│ Message(role="user",                                   │
│         content="Show me those sales as a bar chart",  │
│         metadata={"intent": "re_visualize"})           │
│                                                        │
│ Add Assistant Message:                                 │
│ Message(role="assistant",                              │
│         content="I've created a bar chart...",         │
│         sql_query="SELECT * FROM sales..."  (preserved)│
│         dataframe_snapshot={...},                      │
│         visualization="bar",                           │
│         figure_json='{"data": [...], "layout": {...}}',│
│         metadata={"success": True, "reused_data": True})│
│                                                        │
│ Add Visualization Record:                              │
│ VisualizationRecord(                                   │
│     question="Show me those sales as a bar chart",     │
│     chart_type="bar",                                  │
│     data_summary="5 rows"                              │
│ )                                                      │
└────────────────────────────────────────────────────────┘
                        ↓
┌────────────────────────────────────────────────────────┐
│ Step 8: UI Display                                     │
│                                                        │
│ Gradio Chat Display:                                   │
│ ┌──────────────────────────────────────────┐          │
│ │ User: Show me those sales as a bar chart │          │
│ │                                           │          │
│ │ Assistant: I've created a bar chart...    │          │
│ │                                           │          │
│ │ [Interactive Plotly Bar Chart Displayed]  │          │
│ │  - X-axis: Category                       │          │
│ │  - Y-axis: Amount                         │          │
│ │  - Bars colored by category               │          │
│ │  - Hover tooltips with exact values       │          │
│ │                                           │          │
│ │ [Data Table - same 5 rows]                │          │
│ └──────────────────────────────────────────┘          │
└────────────────────────────────────────────────────────┘
```

#### Scenario: Data Transformation

**User**: "Filter only Electronics category"

```
┌────────────────────────────────────────────────────────┐
│ Step 1: Intent Analysis → "transform"                  │
└────────────────────────────────────────────────────────┘
                        ↓
┌────────────────────────────────────────────────────────┐
│ Step 2: Retrieve Previous DataFrame (5 rows)           │
└────────────────────────────────────────────────────────┘
                        ↓
┌────────────────────────────────────────────────────────┐
│ Step 3: Generate Transformation Code                   │
│ _handle_transformation(question, df)                  │
│                                                        │
│ LLM Prompt:                                            │
│ - DataFrame columns: [transaction_id, amount, ...]     │
│ - User request: "Filter only Electronics category"     │
│ - Instructions: Generate pandas code using 'df' var    │
│                                                        │
│ LLM Response:                                          │
│ df[df['category'] == 'Electronics']                    │
└────────────────────────────────────────────────────────┘
                        ↓
┌────────────────────────────────────────────────────────┐
│ Step 4: Execute Transformation Safely                  │
│                                                        │
│ local_vars = {"df": df.copy(), "pd": pd}               │
│ exec(code, {"__builtins__": {}}, local_vars)           │
│ transformed_df = local_vars["df"]                      │
│                                                        │
│ Result:                                                │
│   transaction_id    amount      date        category  │
│ 0    TXN-1234       1536.17   2024-03-15   Electronics│
│                                                        │
│ Shape: (1, 4)                                          │
└────────────────────────────────────────────────────────┘
                        ↓
┌────────────────────────────────────────────────────────┐
│ Step 5: Generate Answer                                │
│ "I've filtered the data to show only Electronics       │
│  category. Found 1 transaction with amount $1,536.17." │
└────────────────────────────────────────────────────────┘
                        ↓
┌────────────────────────────────────────────────────────┐
│ Step 6: State Update & UI Display                      │
│ (Similar pattern as previous scenarios)                │
└────────────────────────────────────────────────────────┘
```

---

## CONVERSATION MANAGEMENT SYSTEM

### State Persistence Architecture

```
Memory (Runtime)                    Disk (Persistent)
┌──────────────────┐               ┌────────────────────┐
│ ConversationState│               │ conversations/     │
│ ├─ messages[]    │  ──save()──>  │ ├─ uuid1.json      │
│ ├─ data_contexts[]│               │ ├─ uuid2.json      │
│ └─ visualizations[]│              │ └─ uuid3.json      │
└──────────────────┘               └────────────────────┘
         ↑                                    │
         └──────────load()───────────────────┘
```

### Message Flow Timeline

```
Time: T0
─────────────────────────────────────────────
User: "What are top sales?"
  ↓
[Intent: NEW_QUERY] → Generate SQL → Execute
  ↓
conversation_state.add_message(user_msg)
conversation_state.add_message(assistant_msg with SQL & snapshot)
conversation_state.add_data_context(DataContext)
  ↓
save_current_conversation()
  ↓
File: conversations/a1b2c3d4.json created
─────────────────────────────────────────────

Time: T1 (5 seconds later)
─────────────────────────────────────────────
User: "Show as pie chart"
  ↓
[Intent: RE_VISUALIZE] → Retrieve previous DF
  ↓
conversation_state.add_message(user_msg)
conversation_state.add_message(assistant_msg with figure_json)
conversation_state.add_visualization(VisualizationRecord)
  ↓
save_current_conversation()
  ↓
File: conversations/a1b2c3d4.json updated
─────────────────────────────────────────────

Time: T2 (Next day)
─────────────────────────────────────────────
User: Clicks on conversation in sidebar
  ↓
load_conversation("a1b2c3d4.json")
  ↓
conversation_state.import_conversation(data)
  ↓
Reconstruct full history with charts & tables
  ↓
Display in UI
─────────────────────────────────────────────
```

### Memory Management Strategy

**Problem**: Long conversations can consume excessive memory.

**Solution**: Multi-level cleanup

┌─────────────────┐
│  Existing DB    │
│  (analysis.db)  │
│                 │
│  ┌────────────┐ │
│  │ Table 1    │ │
│  │ Table 2    │ │
│  │ Table 3    │ │
│  └────────────┘ │
└────────┬────────┘
         │
         │ python analyze_existing_db.py analysis.db
         │
         ↓
┌─────────────────────────────────┐
│  analyze_existing_db.py         │
│  ─────────────────────────────  │
│  • Read table structure         │
│  • Sample data                  │
│  • Call Ollama LLM              │
│  • Analyze metadata             │
│  • Analyze each column          │
└─────────────┬───────────────────┘
              │
              ↓
    ┌──────────────────┐
    │   Ollama LLM     │
    │   (qwen2.5:7b)     │
    │  ──────────────  │
    │  Understanding:  │
    │  • Business      │
    │    context       │
    │  • Data types    │
    │  • Constraints   │
    │  • Relationships │
    └──────┬───────────┘
           │
           ↓
┌───────────────────────────────┐
│  metadata.db (Generated)      │
│  ───────────────────────────  │
│                               │
│  table_metadata               │
│  ├─ table_name                │
│  ├─ description               │
│  ├─ category                  │
│  ├─ business_context          │
│  ├─ suggested_primary_key     │
│  └─ data_quality_notes        │
│                               │
│  column_metadata              │
│  ├─ column_name               │
│  ├─ sql_type                  │
│  ├─ python_type               │
│  ├─ description               │
│  ├─ business_meaning          │
│  ├─ constraints               │
│  └─ statistics                │
└───────────┬───────────────────┘
            │
            │ ⚠️ ONE-TIME PROCESS
            │ Re-run only when schema changes
            │
            ↓

╔═══════════════════════════════════════════════════════════════════════════╗
║                    PHASE 2: QUERY & VISUALIZATION                         ║
║                         (Fast, Anytime)                                   ║
╚═══════════════════════════════════════════════════════════════════════════╝

┌───────────────────────────────┐
│  User Question                │
│  (Natural Language)           │
│                               │
│  "What are the top 10 sales?" │
└───────────┬───────────────────┘
            │
            │ python main_query_agent.py --interactive
            │
            ↓
┌────────────────────────────────────────┐
│  QueryAgent_Ollama.py                  │
│  ────────────────────────────────────  │
│  1. Load metadata from metadata.db     │
│  2. Connect to source DB               │
│  3. Send question to Ollama            │
└───────────┬────────────────────────────┘
            │
            ↓
    ┌──────────────────┐        ┌────────────────────┐
    │   Ollama LLM     │◄───────┤  Metadata Context  │
    │   (qwen2.5:7b)     │        │  • Table meanings  │
    │  ──────────────  │        │  • Column types    │
    │  Generates:      │        │  • Business rules  │
    │  • SQL Query     │        └────────────────────┘
    │  • Answer text   │
    │  • Viz strategy  │
    └──────┬───────────┘
           │
           ↓
┌───────────────────────────────┐
│  SQL Query Execution          │
│  ───────────────────────────  │
│  SELECT * FROM sales          │
│  ORDER BY amount DESC         │
│  LIMIT 10                     │
└───────────┬───────────────────┘
            │
            ↓
┌───────────────────────────────┐
│  analysis.db                  │
│  (Source Database)            │
│  ───────────────────────────  │
│  Execute query                │
│  Return results               │
└───────────┬───────────────────┘
            │
            ↓
┌────────────────────────────────────────┐
│  Results Processing                    │
│  ────────────────────────────────────  │
│  1. Format results as DataFrame        │
│  2. Generate detailed answer (LLM)     │
│  3. Check if visualization needed      │
│  4. Create Plotly chart                │
└───────────┬────────────────────────────┘
            │
            ↓
┌────────────────────────────────────────┐
│  Output to User                        │
│  ────────────────────────────────────  │
│  📊 DETAILED ANSWER                    │
│  ├─ Natural language explanation       │
│  ├─ Key findings                       │
│  └─ Specific numbers                   │
│                                        │
│  🔍 SQL QUERY USED                     │
│  └─ Formatted SQL                      │
│                                        │
│  📋 QUERY RESULTS                      │
│  └─ Data table                         │
│                                        │
│  📊 VISUALIZATION (if requested)       │
│  ├─ Interactive Plotly chart           │
│  └─ Export to HTML                     │
└────────────────────────────────────────┘
```

## Data Flow Comparison

### Old System (CSV/Excel → Analysis → Query)
```
┌──────┐   ┌─────────┐   ┌──────┐   ┌───────┐
│ CSV  │──→│ Analyze │──→│  DB  │──→│ Query │
└──────┘   └─────────┘   └──────┘   └───────┘
           (Every time)              (Every time)
```

### New System (Pre-analyzed → Query)
```
┌──────────┐   ┌─────────┐   ┌──────────┐
│ Existing │──→│ Analyze │──→│ Metadata │
│    DB    │   │ (Once)  │   │    DB    │
└──────────┘   └─────────┘   └────┬─────┘
                                   │
                                   │ Fast lookup
                                   ↓
                              ┌─────────┐
                              │  Query  │
                              │ (Fast!) │
                              └─────────┘
```

## Component Interaction

```
┌─────────────────────────────────────────────────────────────┐
│                      Ollama LLM Server                      │
│                   (http://localhost:11434)                  │
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────────┐       │
│  │   qwen2.5:7b  │  │qwen2.5:7bb   │  │ Other Models │       │
│  └─────────────┘  └─────────────┘  └──────────────┘       │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           │ HTTP API calls
                           │
        ┌──────────────────┴──────────────────┐
        │                                     │
        ↓                                     ↓
┌───────────────────┐              ┌─────────────────────┐
│ analyze_existing  │              │  QueryAgent_Ollama  │
│     _db.py        │              │       .py           │
│                   │              │                     │
│ One-time analysis │              │  Query execution    │
└────────┬──────────┘              └──────────┬──────────┘
         │                                    │
         │ Writes                             │ Reads
         ↓                                    ↓
    ┌────────────┐                      ┌────────────┐
    │ metadata.db│◄─────────────────────┤ metadata.db│
    └────────────┘    Metadata lookup   └────────────┘
         │                                    │
         │ Reads                              │ Queries
         ↓                                    ↓
    ┌────────────┐                      ┌────────────┐
    │analysis.db │                      │analysis.db │
    │(Structure) │                      │  (Data)    │
    └────────────┘                      └────────────┘
```

## Workflow Timeline

```
Time: T0 (Initial Setup)
═══════════════════════════════════════════
│
│  [User runs analyzer]
│   python analyze_existing_db.py analysis.db
│
├─→ 🔍 Read database structure
├─→ 🤖 LLM analyzes tables/columns (5-10 min)
├─→ 💾 Save to metadata.db
│
│  ✅ Setup complete!
│
═══════════════════════════════════════════
Time: T1, T2, T3... (Subsequent queries)
═══════════════════════════════════════════
│
│  [User asks question]
│   python main_query_agent.py --interactive
│
├─→ ⚡ Load metadata (instant)
├─→ 🤖 Generate SQL (2-3 sec)
├─→ 📊 Execute & visualize (1-2 sec)
│
│  ✅ Fast response!
│
═══════════════════════════════════════════
```

## File Dependencies

```
analyze_existing_db.py
    │
    ├── pandas
    ├── sqlite3
    ├── langchain_ollama (ChatOllama)
    ├── langchain_core (PromptTemplate, StrOutputParser)
    ├── pydantic (BaseModel, Field)
    └── langchain_core.output_parsers (PydanticOutputParser)

QueryAgent_Ollama.py
    │
    ├── pandas
    ├── sqlite3
    ├── plotly (express, graph_objects)
    ├── langchain_ollama (ChatOllama)
    ├── langchain_core (PromptTemplate, StrOutputParser)
    ├── langchain_community (SQLDatabase, QuerySQLDatabaseTool)
    ├── langchain_classic (create_sql_query_chain)
    └── pydantic (BaseModel, Field)

main_query_agent.py
    │
    ├── argparse
    ├── json
    ├── os
    ├── QueryAgent_Ollama (QueryAgent)
    └── plotly.graph_objects (for viz export)
```

## Database Schema

```
metadata.db
│
├── table_metadata
│   ├── table_name (PK)
│   ├── description
│   ├── category
│   ├── business_context
│   ├── suggested_primary_key
│   ├── data_quality_notes (JSON)
│   ├── row_count
│   ├── column_count
│   └── analyzed_at
│
└── column_metadata
    ├── id (PK)
    ├── table_name (FK)
    ├── column_name
    ├── sql_type
    ├── python_type
    ├── description
    ├── business_meaning
    ├── constraints (JSON)
    ├── is_nullable
    ├── suggested_index
    ├── unique_count
    ├── null_count
    └── analyzed_at
```

## Performance Characteristics

```
Operation                   Old System    New System
─────────────────────────────────────────────────────
Initial Setup               N/A           5-10 min
Subsequent Startup          30-60 sec     <1 sec
Query Generation            3-5 sec       3-5 sec
Total Response Time         33-65 sec     3-6 sec
Memory Usage               High          Low
Reusability                No            Yes
```

## Error Handling Flow

```
User Question
    │
    ↓
┌────────────────┐
│ Test Ollama    │──→ Not running? → Return error
└────────┬───────┘
         │ Running
         ↓
┌────────────────┐
│ Generate SQL   │──→ Failed? → Return error with details
└────────┬───────┘
         │ Success
         ↓
┌────────────────┐
│ Execute Query  │──→ SQL error? → Log & return friendly error
└────────┬───────┘
         │ Success
         ↓
┌────────────────┐
│ Generate Answer│──→ Failed? → Return raw results
└────────┬───────┘
         │ Success
         ↓
┌────────────────┐
│ Create Viz     │──→ Failed? → Skip viz, return answer
└────────┬───────┘
         │ Success
         ↓
  Return Complete Results
```

---

## COMPLETE DEPLOYMENT GUIDE - FROM ZERO TO PRODUCTION

This section provides a comprehensive, step-by-step guide to deploy the Conversational Data Analytics System on a completely new machine from scratch to getting your first answer.

### Prerequisites Check

Before starting, verify you have:

**Hardware Requirements**:
- **CPU**: Multi-core processor (4+ cores recommended)
- **RAM**: Minimum 8 GB, 16 GB recommended for production
- **Storage**: At least 10 GB free space for models and data
- **GPU** (Optional): NVIDIA GPU with CUDA for faster inference

**Operating Systems Supported**:
- ✅ Windows 10/11 (64-bit)
- ✅ Linux (Ubuntu 20.04+, Debian 11+, RHEL 8+)
- ✅ macOS 11+ (Big Sur or later)

### Phase 1: Environment Setup (15-20 minutes)

#### Step 1.1: Install Python 3.10+

**Windows**:
```powershell
# Download from python.org or use winget
winget install Python.Python.3.10

# Verify installation
python --version
# Expected: Python 3.10.x or higher
```

**Linux (Ubuntu/Debian)**:
```bash
sudo apt update
sudo apt install python3.10 python3.10-venv python3-pip -y
python3.10 --version
```

**macOS**:
```bash
# Using Homebrew
brew install python@3.10
python3.10 --version
```

#### Step 1.2: Install Ollama

**Windows**:
1. Download installer from: https://ollama.com/download/windows
2. Run `OllamaSetup.exe`
3. Follow installation wizard
4. Ollama will start automatically

**Linux**:
```bash
# One-line install script
curl -fsSL https://ollama.com/install.sh | sh

# Verify installation
ollama --version
# Expected: ollama version is x.x.x
```

**macOS**:
```bash
# Download from ollama.com/download/mac or use Homebrew
brew install ollama

# Start Ollama service
ollama serve &
```

#### Step 1.3: Verify Ollama is Running

```powershell
# Test Ollama API
curl http://localhost:11434/api/tags

# Expected response (JSON with available models)
# {"models":[]}  # Empty initially, we'll add models next
```

**Troubleshooting**:
- **Connection refused**: Start Ollama manually with `ollama serve`
- **Port 11434 in use**: Another process is using the port, restart Ollama
- **Firewall blocking**: Allow Ollama through firewall

#### Step 1.4: Download Required Models

```powershell
# Pull main LLM model (qwen2.5:7b - approximately 4.7 GB)
ollama pull qwen2.5:7b

# Expected output:
# pulling manifest
# pulling <hash>... 100% ▕████████████████████▏ 4.7 GB
# pulling <hash>... 100% ▕████████████████████▏ 1.5 KB
# pulling <hash>... 100% ▕████████████████████▏ 6.9 KB
# verifying sha256 digest
# writing manifest
# success

# Pull embedding model (nomic-embed-text - approximately 275 MB)
ollama pull nomic-embed-text

# Expected output:
# pulling manifest
# pulling <hash>... 100% ▕████████████████████▏ 274 MB
# ...
# success
```

**Verify Models**:
```powershell
ollama list

# Expected output:
# NAME                    ID              SIZE      MODIFIED
# qwen2.5:7b              abc123...       4.7 GB    2 minutes ago
# nomic-embed-text        def456...       274 MB    1 minute ago
```

**Time**: ~10-15 minutes depending on internet speed

---

### Phase 2: Project Setup (5-10 minutes)

#### Step 2.1: Get the Project Files

**Option A: Clone from Repository** (if available):
```powershell
git clone <repository-url>
cd "Ollama 2"
```

**Option B: Manual Setup** (if files provided separately):
```powershell
# Create project directory
mkdir "Ollama 2"
cd "Ollama 2"

# Copy provided files:
# - app_gradio_enhanced.py
# - QueryAgent_Ollama_Enhanced.py
# - conversation_manager.py
# - requirements.txt
# - PRE PROCESSING/ folder with scripts
```

#### Step 2.2: Create Virtual Environment

```powershell
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
.\venv\Scripts\activate

# Linux/macOS:
# source venv/bin/activate

# Verify activation (prompt should show (venv))
# (venv) PS C:\Users\...\Ollama 2>
```

#### Step 2.3: Install Python Dependencies

```powershell
# Install all required packages
pip install -r requirements.txt

# Expected packages:
# pandas==2.1.3
# plotly==5.18.0
# gradio==4.8.0
# langchain==0.1.0
# langchain-community==0.0.10
# langchain-ollama==0.0.3
# chromadb==0.4.18
# pydantic==2.5.2
# python-dotenv==1.0.0
# requests==2.31.0

# Verify installation
pip list | Select-String "gradio|langchain|chromadb|plotly"

# Expected output:
# chromadb                 0.4.18
# gradio                   4.8.0
# langchain                0.1.0
# langchain-community      0.0.10
# langchain-ollama         0.0.3
# plotly                   5.18.0
```

**If Installation Fails**:
```powershell
# Upgrade pip first
python -m pip install --upgrade pip

# Try installing packages individually
pip install pandas plotly gradio
pip install langchain langchain-community langchain-ollama
pip install chromadb pydantic requests
```

#### Step 2.4: Verify Project Structure

```powershell
# Check directory structure
tree /F /A

# Expected structure:
# Ollama 2/
# ├── app_gradio_enhanced.py
# ├── QueryAgent_Ollama_Enhanced.py
# ├── conversation_manager.py
# ├── requirements.txt
# ├── PRE PROCESSING/
# │   ├── analyze_existing_db.py
# │   ├── csv_to_db.py
# │   ├── ARCHITECTURE.md
# │   └── ...
# └── venv/
```

---

### Phase 3: Data Preparation (10-30 minutes depending on data size)

#### Step 3.1: Prepare Your Database

**Option A: You Have an Existing SQLite Database**

```powershell
# Copy your database to project root
Copy-Item "C:\path\to\your\database.db" -Destination ".\analysis.db"

# Verify database is readable
sqlite3 analysis.db ".tables"
# Expected: List of your tables
```

**Option B: You Have CSV Files**

```powershell
# Place CSV file in project directory
Copy-Item "C:\path\to\your\data.csv" -Destination ".\data.csv"

# Convert CSV to SQLite using our script
python "PRE PROCESSING/csv_to_db.py" data.csv --db analysis.db

# Script will:
# 1. Load CSV
# 2. Ask LLM to analyze structure
# 3. Infer column types
# 4. Create optimized database schema
# 5. Insert all data
```

**Example Output**:
```
🔄 CSV TO DATABASE CONVERTER
════════════════════════════════════════
Input CSV: data.csv
Output Database: analysis.db
LLM Model: qwen2.5:7b
════════════════════════════════════════

📊 Loading CSV...
   Detected: 10,000 rows, 8 columns

🧠 Analyzing metadata with LLM...
   Table name: sales_transactions
   Category: sales
   Description: E-commerce sales data

🔍 Analyzing columns...
   [1/8] transaction_id → TEXT (unique identifier)
   [2/8] date → DATE (transaction timestamp)
   [3/8] amount → REAL (sale amount)
   [4/8] category → TEXT (product category)
   [5/8] customer_id → TEXT (customer identifier)
   [6/8] product_name → TEXT (product description)
   [7/8] quantity → INTEGER (items sold)
   [8/8] payment_method → TEXT (payment type)

💾 Creating database schema...
   CREATE TABLE sales_transactions (
       transaction_id TEXT NOT NULL,
       date DATE,
       amount REAL NOT NULL CHECK (amount > 0),
       category TEXT,
       customer_id TEXT,
       product_name TEXT,
       quantity INTEGER,
       payment_method TEXT
   )

📥 Inserting data...
   Progress: 10,000/10,000 rows

✅ CONVERSION COMPLETE
════════════════════════════════════════
Database: analysis.db
Table: sales_transactions
Rows: 10,000
Time: 4m 32s
════════════════════════════════════════
```

**Time**: 2-5 minutes for small datasets (<50K rows), 10-30 minutes for larger datasets

#### Step 3.2: Analyze Database (Create Vector Database)

This is a **critical one-time step** that creates the intelligence layer for metadata-driven SQL generation.

```powershell
# Run the analyzer
python "PRE PROCESSING/analyze_existing_db.py" analysis.db

# What this does:
# 1. Connects to your SQLite database
# 2. For each table:
#    - Asks LLM to analyze table purpose
#    - Asks LLM to analyze each column's meaning
#    - Generates semantic embeddings (768-dim vectors)
#    - Stores everything in ChromaDB
# 3. Creates ./chroma_db_768dim/ directory
```

**Example Output**:
```
🔍 DATABASE ANALYZER (Vector DB Edition)
════════════════════════════════════════
Source Database: analysis.db
Vector Database: ./chroma_db_768dim
LLM Model: qwen2.5:7b
════════════════════════════════════════

📊 Discovering tables...
   Found 3 table(s): ['sales_transactions', 'products', 'customers']

[1/3] ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔍 Analyzing table: sales_transactions
   Rows: 10,000
   Columns: 8

   🧠 Table Analysis:
      Description: E-commerce transaction records with sales data
      Category: sales
      Business Context: Core revenue tracking system
      Primary Key: transaction_id
      Data Quality: Good - minimal nulls, consistent formatting

   📋 Column Analysis:
      [1/8] transaction_id
            Type: TEXT → Unique transaction identifier
            Business Meaning: Order tracking number
            ✅ Embedding generated (768-dim)

      [2/8] date
            Type: DATE → Transaction timestamp
            Business Meaning: When sale occurred
            ✅ Embedding generated (768-dim)

      [3/8] amount
            Type: REAL → Sale total in USD
            Business Meaning: Revenue per transaction
            ✅ Embedding generated (768-dim)

      [4/8] category
            Type: TEXT → Product classification
            Business Meaning: Grouping for analytics
            ✅ Embedding generated (768-dim)

      [5/8] customer_id
            Type: TEXT → Customer identifier
            Business Meaning: Links to customer records
            ✅ Embedding generated (768-dim)

      [6/8] product_name
            Type: TEXT → Product description
            Business Meaning: What was sold
            ✅ Embedding generated (768-dim)

      [7/8] quantity
            Type: INTEGER → Number of items
            Business Meaning: Order quantity
            ✅ Embedding generated (768-dim)

      [8/8] payment_method
            Type: TEXT → How customer paid
            Business Meaning: Payment channel tracking
            ✅ Embedding generated (768-dim)

✅ Successfully analyzed and saved: sales_transactions

[2/3] ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔍 Analyzing table: products
   ...
   (similar detailed output)

[3/3] ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔍 Analyzing table: customers
   ...

🎉 Analysis complete!
════════════════════════════════════════
📊 ANALYSIS SUMMARY
════════════════════════════════════════
Tables Analyzed: 3
Total Columns: 24
Vector Database: ./chroma_db_768dim
Collections Created:
  • table_metadata (3 documents)
  • column_metadata (24 documents)
Total Embeddings: 27
Storage Size: ~2.1 MB
Time: 8m 15s
════════════════════════════════════════

✨ Next Step: Launch the UI with:
   python app_gradio_enhanced.py
```

**Time**: 5-10 minutes for 3-5 tables with 30-50 total columns

**What Just Happened**:
- Created `./chroma_db_768dim/` directory with ChromaDB collections
- Each table has semantic metadata (description, category, context)
- Each column has detailed metadata (type, meaning, constraints)
- All metadata is searchable via semantic similarity
- This enables intelligent SQL generation without manually writing schemas

**Verify Vector Database**:
```powershell
# Check directory exists
Test-Path ".\chroma_db_768dim"
# Expected: True

# Check size
(Get-ChildItem ".\chroma_db_768dim" -Recurse | Measure-Object -Property Length -Sum).Sum / 1MB
# Expected: ~2-5 MB depending on data
```

---

### Phase 4: Launch the Application (1-2 minutes)

#### Step 4.1: Start the Gradio UI

```powershell
# Ensure virtual environment is activated
# (venv) should be in your prompt

# Launch the application
python app_gradio_enhanced.py
```

**Expected Output**:
```
🚀 Starting Conversational Data Analytics System...
════════════════════════════════════════════════

📁 Conversations directory: .\conversations
   Status: ✅ Ready

🌐 Launching Gradio interface...

Running on local URL:  http://0.0.0.0:6969

To create a public link, set `share=True` in `launch()`.
```

**What This Means**:
- Web server started on port 6969
- Accessible from any device on your local network
- `0.0.0.0` means listening on all network interfaces

#### Step 4.2: Open Web Browser

```powershell
# Open browser automatically
Start-Process "http://localhost:6969"

# Or manually navigate to:
# http://localhost:6969
# or
# http://127.0.0.1:6969
```

**You Should See**:
```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  🗄️ Chat History          │  💬 Conversational Data Analytics  │
│                            │                                    │
│  [+ New Chat] [🗑️]        │  ┌──────────────────────────────┐  │
│                            │  │                              │  │
│  Recent Conversations:     │  │     (Empty chat area)        │  │
│  (None yet)                │  │                              │  │
│                            │  │                              │  │
│  ⚙️ Settings               │  └──────────────────────────────┘  │
│  Database Path:            │                                    │
│  [analysis.db        ]     │  ┌──────────────────────────────┐  │
│                            │  │ Ask a question...            │➤│
│  Vector DB Path:           │  └──────────────────────────────┘  │
│  [./chroma_db_768dim ]     │                                    │
│                            │                                    │
│  Model:                    │                                    │
│  [qwen2.5:7b        ▼]     │                                    │
│                            │                                    │
│  [Initialize LLM Agent]    │                                    │
│                            │                                    │
│  Status: Not Connected     │                                    │
│                            │                                    │
└─────────────────────────────────────────────────────────────────┘
```

#### Step 4.3: Initialize the Agent

**Steps in UI**:

1. **Verify Settings** (should be pre-filled):
   - Database Path: `analysis.db`
   - Vector DB Path: `./chroma_db_768dim`
   - Model: `qwen2.5:7b`

2. **Click "Initialize the LLM Agent"**

**What Happens**:
```
Initializing...
├─ Checking database: analysis.db ✅
├─ Connecting to SQLite... ✅
├─ Loading ChromaDB collections... ✅
│  ├─ table_metadata (3 documents) ✅
│  └─ column_metadata (24 documents) ✅
├─ Connecting to Ollama (localhost:11434)... ✅
├─ Loading model: qwen2.5:7b... ✅
├─ Creating conversation state... ✅
└─ Agent ready!
```

**Status Changes To**:
```
Status: ✅ Agent Ready
Database: analysis.db (3 tables, 24 columns)
Model: qwen2.5:7b
```

**Troubleshooting**:
- **"Database not found"**: Check path, use absolute path if needed
- **"Vector database not found"**: Run `analyze_existing_db.py` first
- **"Cannot connect to Ollama"**: Ensure `ollama serve` is running
- **"Model not found"**: Run `ollama pull qwen2.5:7b`

---

### Phase 5: Verification Test (2-3 minutes)

Let's test the system with a simple query to ensure everything works.

#### Test 1: Simple Query

**In the chat input, type**:
```
What tables are available in the database?
```

**Click ➤ or press Enter**

**Expected Response** (appears in ~3-5 seconds):
```
Assistant:
The database contains the following tables:

1. **sales_transactions** (10,000 rows)
   - E-commerce transaction records with sales data
   - Columns: transaction_id, date, amount, category, customer_id, 
     product_name, quantity, payment_method

2. **products** (500 rows)
   - Product catalog with details
   - Columns: product_id, name, category, price, stock_quantity

3. **customers** (2,500 rows)
   - Customer information records
   - Columns: customer_id, name, email, join_date, loyalty_tier

You can ask me questions about any of these tables!
```

**What Just Happened**:
1. ✅ UI sent question to agent
2. ✅ Agent analyzed intent (NEW_QUERY)
3. ✅ Agent retrieved metadata from ChromaDB
4. ✅ LLM generated natural language answer
5. ✅ Answer displayed in chat
6. ✅ Conversation auto-saved to `conversations/<uuid>.json`

#### Test 2: Data Query with Visualization

**Type**:
```
Show me the top 5 sales by amount as a bar chart
```

**Expected Response** (~4-6 seconds):
```
Assistant:
Here are the top 5 sales by amount:

1. $1,536.17 - Electronics (TXN-1234) on 2024-03-15
2. $1,112.25 - Home (TXN-5678) on 2024-02-28
3. $765.28 - Sports (TXN-9012) on 2024-01-12
4. $508.85 - Fashion (TXN-3456) on 2024-04-03
5. $246.47 - Beauty (TXN-7890) on 2024-03-22

I've created a bar chart showing these top sales by amount.

[Interactive Plotly Bar Chart Appears]
┌────────────────────────────────────────┐
│  Top 5 Sales by Amount                 │
│                                        │
│  1,600│                                │
│  1,400│     ███                        │
│  1,200│     ███  ███                   │
│  1,000│     ███  ███                   │
│    800│     ███  ███  ███              │
│    600│     ███  ███  ███  ███         │
│    400│     ███  ███  ███  ███  ███    │
│    200│     ███  ███  ███  ███  ███    │
│      0└─────────────────────────────────│
│        Elec Home Sport Fash Beau       │
└────────────────────────────────────────┘

[Data Table Appears]
  transaction_id   amount      date       category
0     TXN-1234     1536.17   2024-03-15  Electronics
1     TXN-5678     1112.25   2024-02-28  Home
2     TXN-9012      765.28   2024-01-12  Sports
3     TXN-3456      508.85   2024-04-03  Fashion
4     TXN-7890      246.47   2024-03-22  Beauty
```

**What Just Happened**:
1. ✅ Intent detected: NEW_QUERY + visualization requested
2. ✅ Semantic search found "sales_transactions" table
3. ✅ SQL generated: `SELECT * FROM sales_transactions ORDER BY amount DESC LIMIT 5`
4. ✅ SQL validated and executed
5. ✅ Natural language answer generated
6. ✅ Visualization recommendation: bar chart
7. ✅ Plotly bar chart created and displayed
8. ✅ Data table rendered
9. ✅ Conversation saved with all data

#### Test 3: Follow-Up Question (Context Test)

**Type**:
```
Show those as a pie chart instead
```

**Expected Response** (~2-3 seconds, faster than first query):
```
Assistant:
I've converted the top 5 sales data into a pie chart showing the 
proportion of sales amount by category.

[Interactive Plotly Pie Chart Appears]
┌────────────────────────────────────────┐
│  Top 5 Sales Distribution by Amount    │
│                                        │
│          ╱───────╲                     │
│      ╱───  37.5%  ───╲                 │
│    ╱   Electronics    ╲                │
│   │                    │               │
│   │  27.2%            │ 18.7%          │
│   │  Home              Sports          │
│    ╲                  ╱                │
│      ╲─── 12.4% ───╱                   │
│         Fashion                        │
│           6.2% Beauty                  │
└────────────────────────────────────────┘

[Same Data Table]
```

**What Just Happened**:
1. ✅ Intent detected: RE_VISUALIZE (context-aware)
2. ✅ Referenced "those" → retrieved previous DataFrame from memory
3. ✅ **No new SQL query** (reused existing data)
4. ✅ Created new pie chart visualization
5. ✅ Displayed with same data
6. ✅ Faster response (skipped SQL generation)

**🎉 SUCCESS! Your system is fully operational!**

---

### Phase 6: Production Deployment (Optional)

#### Option A: Run as Background Service (Windows)

**Create PowerShell Script** (`start-analytics.ps1`):
```powershell
# Start Ollama if not running
$ollama = Get-Process ollama -ErrorAction SilentlyContinue
if (-not $ollama) {
    Start-Process "ollama" -ArgumentList "serve" -WindowStyle Hidden
    Start-Sleep -Seconds 3
}

# Activate virtual environment and start app
cd "C:\path\to\Ollama 2"
.\venv\Scripts\activate
python app_gradio_enhanced.py
```

**Create Scheduled Task**:
```powershell
# Run on system startup
$action = New-ScheduledTaskAction -Execute "PowerShell.exe" `
    -Argument "-File C:\path\to\start-analytics.ps1"

$trigger = New-ScheduledTaskTrigger -AtStartup

Register-ScheduledTask -TaskName "DataAnalyticsAI" `
    -Action $action -Trigger $trigger -RunLevel Highest
```

#### Option B: Docker Deployment

**Create Dockerfile**:
```dockerfile
FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y curl && \
    curl -fsSL https://ollama.com/install.sh | sh

# Set working directory
WORKDIR /app

# Copy application files
COPY . /app

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Pull Ollama models
RUN ollama serve & \
    sleep 10 && \
    ollama pull qwen2.5:7b && \
    ollama pull nomic-embed-text

# Expose Gradio port
EXPOSE 6969

# Create startup script
RUN echo '#!/bin/bash\nollama serve &\nsleep 5\npython app_gradio_enhanced.py' > /app/start.sh && \
    chmod +x /app/start.sh

# Run application
CMD ["/app/start.sh"]
```

**Build and Run**:
```powershell
# Build image
docker build -t data-analytics-ai .

# Run container
docker run -d `
    -p 6969:6969 `
    -v ${PWD}/conversations:/app/conversations `
    -v ${PWD}/analysis.db:/app/analysis.db `
    -v ${PWD}/chroma_db_768dim:/app/chroma_db_768dim `
    --name analytics-system `
    data-analytics-ai

# View logs
docker logs -f analytics-system

# Access at http://localhost:6969
```

#### Option C: Linux systemd Service

**Create service file** (`/etc/systemd/system/data-analytics.service`):
```ini
[Unit]
Description=Conversational Data Analytics AI System
After=network.target

[Service]
Type=simple
User=youruser
WorkingDirectory=/home/youruser/Ollama 2
Environment="PATH=/home/youruser/Ollama 2/venv/bin:/usr/local/bin:/usr/bin:/bin"
ExecStartPre=/usr/local/bin/ollama serve &
ExecStart=/home/youruser/Ollama 2/venv/bin/python app_gradio_enhanced.py
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Enable and start**:
```bash
sudo systemctl daemon-reload
sudo systemctl enable data-analytics
sudo systemctl start data-analytics
sudo systemctl status data-analytics

# View logs
sudo journalctl -u data-analytics -f
```

---

## END-TO-END USER GUIDE - GETTING FINAL ANSWERS

This section demonstrates how to interact with the system to get answers, from simple queries to complex multi-turn conversations with visualizations.

### Understanding the Interface

```
┌────────────────────────────────────────────────────────────────────┐
│                                                                    │
│  SIDEBAR (Left)              │  MAIN CHAT AREA (Right)            │
│  ────────────────             │  ──────────────────────            │
│                               │                                    │
│  🗄️ Chat History             │  💬 Conversation Display           │
│  • New Chat button           │  • User messages (right-aligned)   │
│  • Delete button             │  • Assistant messages (left)       │
│  • List of saved chats       │  • Charts (interactive Plotly)     │
│                               │  • Data tables (HTML)              │
│  ⚙️ Settings                  │                                    │
│  • Database path             │  📝 Input Area                     │
│  • Vector DB path            │  • Text input box                  │
│  • Model selection           │  • Send button (➤)                 │
│  • Initialize button         │                                    │
│  • Status indicator          │                                    │
│                               │                                    │
└────────────────────────────────────────────────────────────────────┘
```

### Query Types and Examples

#### 1. Exploratory Questions

**Goal**: Understand what data is available

**Examples**:

```
Q: "What data do you have?"
A: Lists all tables with descriptions and row counts

Q: "What columns are in the sales table?"
A: Lists all columns with their types and meanings

Q: "How many records are in the database?"
A: Provides row counts for all tables with total
```

**Example Interaction**:
```
┌─────────────────────────────────────────────────────────┐
│ User: What data is available?                           │
│                                                         │
│ Assistant:                                              │
│ I have access to 3 tables in your database:            │
│                                                         │
│ 1. **sales_transactions** (10,000 rows)                │
│    Transaction records with sales data including:      │
│    • Transaction ID and date                           │
│    • Sale amounts                                      │
│    • Product categories                                │
│    • Customer information                              │
│    • Payment methods                                   │
│                                                         │
│ 2. **products** (500 rows)                             │
│    Product catalog with details like:                  │
│    • Product names and IDs                             │
│    • Categories and prices                             │
│    • Stock quantities                                  │
│                                                         │
│ 3. **customers** (2,500 rows)                          │
│    Customer records containing:                        │
│    • Customer IDs and names                            │
│    • Contact information                               │
│    • Join dates                                        │
│    • Loyalty tiers                                     │
│                                                         │
│ What would you like to explore?                        │
└─────────────────────────────────────────────────────────┘
```

#### 2. Simple Aggregation Queries

**Goal**: Get summary statistics

**Examples**:

```
Q: "What is the total sales amount?"
Q: "How many transactions were there last month?"
Q: "What's the average order value?"
Q: "Show me sales by category"
```

**Example Interaction**:
```
┌─────────────────────────────────────────────────────────┐
│ User: What is the total sales amount?                   │
│                                                         │
│ Assistant:                                              │
│ The total sales amount across all transactions is      │
│ **$4,523,876.45**.                                     │
│                                                         │
│ This represents 10,000 transactions with an average    │
│ order value of $452.39.                                │
│                                                         │
│ Breakdown by category:                                 │
│ • Electronics: $1,234,567.89 (27.3%)                   │
│ • Home: $987,654.32 (21.8%)                            │
│ • Fashion: $876,543.21 (19.4%)                         │
│ • Sports: $765,432.10 (16.9%)                          │
│ • Beauty: $659,678.93 (14.6%)                          │
│                                                         │
│ [Data Table with detailed breakdown]                   │
│   category      total_sales    percentage              │
│ 0 Electronics   1234567.89     27.3%                   │
│ 1 Home           987654.32     21.8%                   │
│ 2 Fashion        876543.21     19.4%                   │
│ 3 Sports         765432.10     16.9%                   │
│ 4 Beauty         659678.93     14.6%                   │
└─────────────────────────────────────────────────────────┘
```

#### 3. Top N / Bottom N Queries

**Goal**: Find extremes in data

**Examples**:

```
Q: "Show me the top 10 customers by spending"
Q: "What are the 5 least selling products?"
Q: "Find the highest value transactions"
```

**Example Interaction**:
```
┌─────────────────────────────────────────────────────────┐
│ User: Show me the top 5 customers by total spending    │
│                                                         │
│ Assistant:                                              │
│ Here are your top 5 customers by total spending:       │
│                                                         │
│ 1. **Sarah Johnson** (CUST-1023)                       │
│    • Total: $15,678.45                                 │
│    • Transactions: 47                                  │
│    • Avg Order: $333.58                                │
│    • Loyalty: Platinum                                 │
│                                                         │
│ 2. **Michael Chen** (CUST-2156)                        │
│    • Total: $14,234.12                                 │
│    • Transactions: 38                                  │
│    • Avg Order: $374.58                                │
│    • Loyalty: Platinum                                 │
│                                                         │
│ 3. **Emily Rodriguez** (CUST-0789)                     │
│    • Total: $12,987.33                                 │
│    • Transactions: 41                                  │
│    • Avg Order: $316.76                                │
│    • Loyalty: Gold                                     │
│                                                         │
│ 4. **David Kim** (CUST-1445)                           │
│    • Total: $11,543.67                                 │
│    • Transactions: 35                                  │
│    • Avg Order: $329.82                                │
│    • Loyalty: Gold                                     │
│                                                         │
│ 5. **Amanda White** (CUST-0334)                        │
│    • Total: $10,876.54                                 │
│    • Transactions: 29                                  │
│    • Avg Order: $375.05                                │
│    • Loyalty: Gold                                     │
│                                                         │
│ These 5 customers account for $65,319.11 (1.4% of      │
│ total revenue). Consider VIP treatment programs!       │
│                                                         │
│ [Data Table with full details]                         │
└─────────────────────────────────────────────────────────┘
```

#### 4. Visualization Requests

**Goal**: See data as charts

**Visualization Keywords**: chart, graph, plot, visualize, show as, pie, bar, line, scatter

**Examples**:

```
Q: "Show sales by month as a line chart"
Q: "Visualize category distribution as a pie chart"
Q: "Create a bar chart of top products"
Q: "Plot sales trend over time"
```

**Example Interaction**:
```
┌─────────────────────────────────────────────────────────┐
│ User: Show me monthly sales as a line chart             │
│                                                         │
│ Assistant:                                              │
│ Here's the monthly sales trend for 2024:               │
│                                                         │
│ [Interactive Plotly Line Chart]                         │
│                                                         │
│  $600K │                           ╱─────╲             │
│        │                         ╱         ╲           │
│  $500K │                       ╱             ╲         │
│        │                     ╱                 ╲       │
│  $400K │           ╱───────╱                     ╲     │
│        │         ╱                                 ╲   │
│  $300K │       ╱                                     ╲ │
│        │     ╱                                         │
│  $200K │   ╱                                           │
│        │ ╱                                             │
│  $100K │                                               │
│        └───────────────────────────────────────────────│
│         Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec│
│                                                         │
│ **Key Insights**:                                      │
│ • Steady growth from Jan ($250K) to Jul ($580K)        │
│ • Peak sales in July coinciding with summer season     │
│ • Slight dip in Aug-Sep, recovered in Oct              │
│ • Year-over-year growth: +34%                          │
│ • Best performing months: Jul, Jun, Oct                │
│                                                         │
│ Hover over the chart for exact values!                 │
│                                                         │
│ [Data Table]                                            │
│   month    total_sales    growth_pct                   │
│ 0 Jan      250,234.56     --                           │
│ 1 Feb      278,567.89     +11.3%                       │
│ 2 Mar      312,456.78     +12.2%                       │
│ ...                                                     │
└─────────────────────────────────────────────────────────┘
```

#### 5. Multi-Turn Conversations (Context-Aware)

**Goal**: Build on previous answers

**Examples**:

```
# Turn 1
Q: "Show me sales by category"
A: [Table with categories]

# Turn 2 (references "those")
Q: "Show those as a bar chart"
A: [Bar chart with same data, no new SQL query]

# Turn 3 (references "that")
Q: "Sort that by highest to lowest"
A: [Re-sorted chart]

# Turn 4 (transformation)
Q: "Only show categories over $500K"
A: [Filtered data]
```

**Example Interaction**:
```
┌─────────────────────────────────────────────────────────┐
│ User: What are the total sales by category?             │
│                                                         │
│ Assistant:                                              │
│ Here are the total sales by category:                  │
│                                                         │
│ [Data Table]                                            │
│   category      total_sales                             │
│ 0 Electronics   1,234,567.89                            │
│ 1 Home            987,654.32                            │
│ 2 Fashion         876,543.21                            │
│ 3 Sports          765,432.10                            │
│ 4 Beauty          659,678.93                            │
│                                                         │
│ Total across all categories: $4,523,876.45              │
├─────────────────────────────────────────────────────────┤
│ User: Show those as a bar chart                         │
│                                                         │
│ Assistant:                                              │
│ I've created a bar chart for the sales by category:    │
│                                                         │
│ [Interactive Plotly Bar Chart]                          │
│                                                         │
│  $1.4M │                                                │
│        │     ███                                        │
│  $1.2M │     ███                                        │
│        │     ███                                        │
│  $1.0M │     ███     ███                                │
│        │     ███     ███                                │
│  $800K │     ███     ███     ███                        │
│        │     ███     ███     ███     ███                │
│  $600K │     ███     ███     ███     ███     ███        │
│        │     ███     ███     ███     ███     ███        │
│  $400K │     ███     ███     ███     ███     ███        │
│        │     ███     ███     ███     ███     ███        │
│  $200K │     ███     ███     ███     ███     ███        │
│        └──────────────────────────────────────────────  │
│         Elec    Home    Fash    Sport   Beau           │
│                                                         │
│ [Same Data Table]                                       │
├─────────────────────────────────────────────────────────┤
│ User: Only show categories above $800K                  │
│                                                         │
│ Assistant:                                              │
│ Filtered to show only categories with sales over $800K:│
│                                                         │
│ [Updated Bar Chart with 3 bars]                         │
│                                                         │
│ [Filtered Data Table]                                   │
│   category      total_sales                             │
│ 0 Electronics   1,234,567.89                            │
│ 1 Home            987,654.32                            │
│ 2 Fashion         876,543.21                            │
│                                                         │
│ These 3 categories represent 70% of total revenue.      │
├─────────────────────────────────────────────────────────┤
│ User: What percentage does Electronics represent?       │
│                                                         │
│ Assistant:                                              │
│ Electronics represents **27.3%** of total sales.        │
│                                                         │
│ Calculation:                                            │
│ • Electronics: $1,234,567.89                            │
│ • Total Sales: $4,523,876.45                            │
│ • Percentage: 1,234,567.89 ÷ 4,523,876.45 = 0.273       │
│                                                         │
│ This makes Electronics your #1 category, outperforming  │
│ the second-place Home category by 5.5 percentage points.│
└─────────────────────────────────────────────────────────┘
```

**What Happened Behind the Scenes**:
1. **Turn 1**: New SQL query generated
2. **Turn 2**: Detected "those" → reused DataFrame, created visualization (faster)
3. **Turn 3**: Detected "only show" → generated pandas filter code
4. **Turn 4**: Detected "percentage" → calculated from existing data in memory

#### 6. Comparative Analysis

**Goal**: Compare different segments

**Examples**:

```
Q: "Compare Q1 vs Q2 sales"
Q: "Which category grew the most year-over-year?"
Q: "Show the difference between weekday and weekend sales"
```

**Example Interaction**:
```
┌─────────────────────────────────────────────────────────┐
│ User: Compare sales between Q1 and Q2 of 2024           │
│                                                         │
│ Assistant:                                              │
│ **Q1 vs Q2 Sales Comparison (2024)**                   │
│                                                         │
│ 📊 Overall Performance:                                │
│ • Q1 (Jan-Mar): $1,234,567.00                          │
│ • Q2 (Apr-Jun): $1,456,789.00                          │
│ • Difference: +$222,222.00 (+18.0%)                    │
│                                                         │
│ 📈 Growth by Category:                                 │
│                                                         │
│ [Grouped Bar Chart]                                     │
│                                                         │
│  $600K │                                                │
│        │     ███                                        │
│  $500K │     ███ ███                                    │
│        │     ███ ███     ███                            │
│  $400K │     ███ ███     ███ ███                        │
│        │     ███ ███     ███ ███     ███                │
│  $300K │     ███ ███     ███ ███     ███ ███            │
│        │     ███ ███     ███ ███     ███ ███     ███    │
│  $200K │     ███ ███     ███ ███     ███ ███     ███ ███│
│        └──────────────────────────────────────────────  │
│         Elec        Home        Fash        Sport  Beau │
│         █ Q1  █ Q2                                      │
│                                                         │
│ **Key Findings**:                                      │
│                                                         │
│ 🔥 Strongest Growth:                                   │
│ 1. Electronics: +45% ($280K → $406K)                   │
│ 2. Home: +32% ($245K → $323K)                          │
│ 3. Fashion: +15% ($267K → $307K)                       │
│                                                         │
│ 📉 Slower Growth:                                      │
│ • Sports: +8% ($234K → $253K)                          │
│ • Beauty: +5% ($208K → $218K)                          │
│                                                         │
│ 💡 Insights:                                           │
│ • Electronics momentum driven by new product launches   │
│ • Home category benefited from seasonal promotions     │
│ • Consider targeted campaigns for Sports and Beauty    │
│   to boost Q3 performance                              │
│                                                         │
│ [Detailed Data Table]                                   │
│   category      q1_sales    q2_sales    growth_pct     │
│ 0 Electronics   280,123.45  406,234.56  +45.0%         │
│ 1 Home          245,678.90  323,456.78  +31.7%         │
│ 2 Fashion       267,345.12  307,123.89  +14.9%         │
│ 3 Sports        233,567.89  252,678.34  +8.2%          │
│ 4 Beauty        207,851.64  217,295.43  +4.5%          │
└─────────────────────────────────────────────────────────┘
```

#### 7. Time-Based Analysis

**Goal**: Understand trends over time

**Examples**:

```
Q: "Show daily sales for the last 30 days"
Q: "What day of week has highest sales?"
Q: "How do sales vary by hour?"
```

**Example Interaction**:
```
┌─────────────────────────────────────────────────────────┐
│ User: What day of the week has the highest sales?       │
│                                                         │
│ Assistant:                                              │
│ **Sales by Day of Week Analysis**                      │
│                                                         │
│ [Bar Chart]                                             │
│                                                         │
│  $800K │                                                │
│        │                         ███                    │
│  $700K │                         ███                    │
│        │                 ███     ███                    │
│  $600K │         ███     ███     ███     ███            │
│        │         ███     ███     ███     ███            │
│  $500K │         ███     ███     ███     ███            │
│        │         ███     ███     ███     ███     ███    │
│  $400K │         ███     ███     ███     ███     ███    │
│        │   ███   ███     ███     ███     ███     ███    │
│  $300K │   ███   ███     ███     ███     ███     ███    │
│        └──────────────────────────────────────────────  │
│         Mon   Tue   Wed   Thu   Fri   Sat   Sun        │
│                                                         │
│ **Winner: Friday** 🏆                                  │
│ • Total: $782,345.67                                   │
│ • Avg Order: $487.92                                   │
│ • Transactions: 1,604                                  │
│ • 19.2% above weekly average                           │
│                                                         │
│ **Full Breakdown**:                                    │
│ 1. Friday: $782K (22.4%)                               │
│ 2. Saturday: $723K (20.7%)                             │
│ 3. Thursday: $691K (19.8%)                             │
│ 4. Wednesday: $634K (18.2%)                            │
│ 5. Tuesday: $567K (16.2%)                              │
│ 6. Sunday: $489K (14.0%)                               │
│ 7. Monday: $345K (9.9%)                                │
│                                                         │
│ 📊 Patterns:                                           │
│ • Weekend (Fri-Sun): 57.1% of weekly sales             │
│ • Weekday (Mon-Thu): 42.9% of weekly sales             │
│ • Monday is slowest (53% below Friday)                 │
│                                                         │
│ 💡 Recommendations:                                    │
│ • Schedule promotions Thursday-Saturday                │
│ • Consider Monday special offers to boost traffic      │
│ • Ensure adequate staffing Friday-Sunday               │
│                                                         │
│ [Data Table]                                            │
│   day_of_week   total_sales   avg_order   transactions │
│ 0 Friday        782,345.67    487.92      1,604        │
│ 1 Saturday      723,456.78    451.23      1,604        │
│ ...                                                     │
└─────────────────────────────────────────────────────────┘
```

#### 8. Distribution Analysis

**Goal**: Understand spread and outliers

**Examples**:

```
Q: "Show the distribution of order amounts"
Q: "What's the profit margin distribution by category?"
Q: "Are there any outliers in customer spending?"
```

**Example Interaction**:
```
┌─────────────────────────────────────────────────────────┐
│ User: Show profit margin distribution by category       │
│      using a box plot                                   │
│                                                         │
│ Assistant:                                              │
│ Here's the profit margin distribution across categories:│
│                                                         │
│ [Interactive Plotly Box Plot]                           │
│                                                         │
│  60% │                                  ⚬               │
│      │                                                  │
│  50% │         ┌───┐                                    │
│      │         │   │         ┌───┐                      │
│  40% │    ┌────┤   ├────┐   │   │    ┌───┐             │
│      │    │    │   │    │   │   │    │   │             │
│  30% │    │    └───┘    │   │   │    │   │    ┌───┐    │
│      │    │      █      │   └───┘    │   │    │   │    │
│  20% │    │             │     █      └───┘    │   │    │
│      │    └─────────────┘             █       └───┘    │
│  10% │                                          █       │
│      │              ⚬                                   │
│   0% │                                                  │
│      └──────────────────────────────────────────────    │
│         Elec    Home    Fash    Sport   Beau           │
│                                                         │
│ **Key Statistics**:                                    │
│                                                         │
│ 📊 Electronics:                                        │
│ • Median: 32.5%                                        │
│ • Range: 15.2% to 55.8%                                │
│ • IQR: 28.1% - 38.9%                                   │
│ • Outliers: 2 high (>55%)                              │
│                                                         │
│ 📊 Home:                                               │
│ • Median: 28.7%                                        │
│ • Range: 12.3% to 48.9%                                │
│ • IQR: 24.5% - 34.2%                                   │
│ • Consistent profitability                             │
│                                                         │
│ 📊 Fashion:                                            │
│ • Median: 35.2%                                        │
│ • Range: 18.7% to 52.1%                                │
│ • IQR: 30.1% - 41.3%                                   │
│ • Highest median margin                                │
│                                                         │
│ 📊 Sports:                                             │
│ • Median: 22.3%                                        │
│ • Range: 8.9% to 38.7%                                 │
│ • IQR: 18.4% - 28.1%                                   │
│ • Lower margins, competitive pricing                   │
│                                                         │
│ 📊 Beauty:                                             │
│ • Median: 18.5%                                        │
│ • Range: 5.2% to 32.4%                                 │
│ • IQR: 14.7% - 23.8%                                   │
│ • Lowest margins, review pricing strategy              │
│                                                         │
│ 💡 Insights:                                           │
│ • Fashion offers best profit margins (35.2% median)    │
│ • Beauty needs pricing optimization (18.5% median)     │
│ • Electronics shows high variability (outliers exist)  │
│ • Consider focusing on high-margin Fashion items       │
│                                                         │
│ [Detailed Statistics Table]                             │
└─────────────────────────────────────────────────────────┘
```

### Advanced Features

#### Conversation Management

**Save and Resume Conversations**:

1. **Auto-Save**: Every interaction is automatically saved
   - Location: `conversations/<uuid>.json`
   - Includes: All messages, data, visualizations

2. **Load Previous Conversation**:
   - Click conversation in sidebar
   - Entire history restored
   - Can continue asking questions

3. **New Conversation**:
   - Click "+ New Chat"
   - Starts fresh (previous data not accessible)
   - Previous conversation remains saved

4. **Delete Conversation**:
   - Select conversation
   - Click 🗑️ button
   - Permanently removed

**Example**:
```
# Session 1 (Monday)
Q: "Show me last week's sales"
[Get answer and close browser]

# Session 2 (Tuesday)
[Open browser, select Monday's conversation from sidebar]
Q: "How does that compare to the week before?"
[System knows "that" refers to last week's data]
```

#### Data Transformation

**Transform previous results without re-querying**:

```
# Get initial data
Q: "Show all sales from last month"
[Returns 1,000 rows]

# Transform without new SQL
Q: "Filter only amounts over $500"
[Uses pandas to filter existing DataFrame]

Q: "Sort by date descending"
[Sorts existing data]

Q: "Group by category and sum amounts"
[Aggregates existing data]
```

**How It Works**:
- System detects transformation intent
- LLM generates pandas code
- Code executed safely on existing DataFrame
- Much faster than new SQL query

#### Export and Share

**Export Visualizations**:
```python
# Charts are interactive Plotly figures
# Right-click on chart → Download as PNG/SVG/PDF
# Or use built-in Plotly controls:
# 📷 Camera icon → Save as PNG
# 🔍 Zoom, pan, reset tools available
```

**Export Data**:
```python
# Data tables displayed as HTML
# Can be copied and pasted into Excel
# Or right-click → Copy
```

### Troubleshooting Common Issues

#### Issue 1: "Agent not responding"

**Symptoms**: Spinning indicator, no answer

**Causes**:
1. Ollama not running
2. Model not loaded
3. Database connection lost

**Solutions**:
```powershell
# Check Ollama status
curl http://localhost:11434/api/tags

# Restart Ollama if needed
ollama serve

# Reload page and reinitialize agent
```

#### Issue 2: "SQL execution error"

**Symptoms**: Error message in chat

**Causes**:
1. Invalid table/column reference
2. Syntax error in generated SQL
3. Database locked

**Solutions**:
- **Automatic**: System retries with error feedback to LLM
- **Manual**: Rephrase question with explicit table/column names
- **Example**: Instead of "Show sales", try "Show data from sales_transactions table"

#### Issue 3: "No visualization created"

**Symptoms**: Answer but no chart

**Causes**:
1. No viz keywords in question
2. Data not suitable for visualization
3. Chart creation failed

**Solutions**:
```
# Be explicit about visualization
❌ "Show me sales data"
✅ "Show me sales data as a bar chart"

# Or ask for viz after getting data
Q: "Show me sales by category"
[Get table]
Q: "Visualize that as a bar chart"
[Get chart]
```

#### Issue 4: "Can't find previous data"

**Symptoms**: "Show me those" doesn't work

**Causes**:
1. Started new conversation (data not persisted across chats)
2. Too many turns (data contexts auto-cleaned after 10)

**Solutions**:
- Use same conversation
- Re-run original query if needed
- Loaded conversations restore all data

#### Issue 5: "Slow responses"

**Symptoms**: Takes >10 seconds per answer

**Causes**:
1. Large database (many tables/columns)
2. Complex query
3. System resources limited

**Solutions**:
```powershell
# Use smaller, faster model (if accuracy acceptable)
ollama pull qwen2.5:3b  # Half the size of 7b

# Or optimize ChromaDB
# Reduce metadata verbosity
# Limit semantic search results

# Or increase system resources
# Close other applications
# Use GPU if available
```

### Best Practices for Getting Good Answers

#### 1. Be Specific

```
❌ "Show me data"
✅ "Show me the top 10 sales transactions by amount"

❌ "What about last month?"
✅ "What were the total sales for March 2024?"
```

#### 2. Use Visualization Keywords

```
✅ "Show me sales by category as a bar chart"
✅ "Visualize the trend"
✅ "Create a pie chart of distribution"
✅ "Plot the correlation"
```

#### 3. Build on Previous Questions

```
Q1: "What are the total sales by region?"
Q2: "Show those as a map"  # References Q1 results
Q3: "Which region grew the most?"  # Still in context
Q4: "Show me the top customers in that region"  # Still connected
```

#### 4. Provide Context When Needed

```
✅ "Show me sales for Q1 2024"  # Clear time period
✅ "Compare Electronics vs Home categories"  # Clear comparison
✅ "Filter transactions above $1000"  # Clear threshold
```

#### 5. Ask for Explanations

```
Q: "Why is Electronics the best category?"
Q: "What factors contributed to July's peak?"
Q: "Explain the correlation between price and quantity"
```

### Summary: Getting From Zero to Answer

**Complete Flow**:

```
1. ✅ Install Python 3.10+ and Ollama
2. ✅ Pull models (qwen2.5:7b, nomic-embed-text)
3. ✅ Setup project and install dependencies
4. ✅ Prepare database (existing or convert from CSV)
5. ✅ Run analyzer to create vector database
6. ✅ Launch Gradio UI
7. ✅ Initialize agent in browser
8. ✅ Ask question in natural language
9. ✅ Get answer with optional visualization
10. ✅ Continue conversation with follow-ups
```

**Time Investment**:
- Initial setup: 20-30 minutes
- Database analysis: 5-10 minutes
- Ongoing usage: 3-6 seconds per query

**Result**:
- Natural language interface to your data
- No SQL knowledge required
- Intelligent visualizations
- Conversation memory
- Production-ready system

---

## CONCLUSION

This system transforms complex data analysis into natural conversation. By combining:
- **LLM intelligence** (qwen2.5:7b) for understanding and generation
- **Vector database** (ChromaDB) for semantic metadata search
- **Context management** (conversation state) for multi-turn awareness
- **Automatic visualization** (Plotly) for insights
- **Web interface** (Gradio) for accessibility

You get a powerful analytics assistant that:
- ✅ Understands natural language questions
- ✅ Generates accurate SQL automatically
- ✅ Provides insightful answers
- ✅ Creates beautiful visualizations
- ✅ Remembers conversation context
- ✅ Requires no technical knowledge to use

**Start asking questions and let the AI do the heavy lifting!** 🚀
