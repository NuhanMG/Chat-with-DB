import gradio as gr
import pandas as pd
import plotly.graph_objects as go
import json
from PIL import Image
import io
from typing import Optional, List, Tuple
import os
import logging

from QueryAgent_Ollama_Enhanced import QueryAgentEnhanced
from conversation_manager import ConversationState

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global state
agent: Optional[QueryAgentEnhanced] = None
conversation_state: Optional[ConversationState] = None
stored_figures: dict = {}  # Store figures by message index for retrieval
chart_history: List[Tuple[int, str, go.Figure]] = []  # (message_idx, chart_type, figure)

def fig_to_pil(fig: go.Figure) -> Image.Image:
    """Convert Plotly figure to PIL Image for gallery"""
    try:
        # Convert to image bytes
        img_bytes = fig.to_image(format="png", width=400, height=300)
        # Convert to PIL Image
        return Image.open(io.BytesIO(img_bytes))
    except Exception as e:
        logger.error(f"Failed to convert figure to image: {e}")
        # Return a blank image if conversion fails
        return Image.new('RGB', (400, 300), color='lightgray')

def build_gallery_images() -> List[Tuple[Image.Image, str]]:
    """Create gallery-ready tuples from chart history"""
    gallery_images: List[Tuple[Image.Image, str]] = []
    for msg_idx, chart_type, fig in chart_history:
        try:
            img = fig_to_pil(fig)
            caption = f"#{msg_idx}: {chart_type.replace('_', ' ').title()}"
            gallery_images.append((img, caption))
        except Exception as e:
            logger.error(f"Failed to create thumbnail for chart #{msg_idx}: {e}")
    return gallery_images

def initialize_agent(
    db_path: str,
    vector_db: str = "./chroma_db_768dim",
    model: str = "qwen2.5:7b"
) -> str:
    """Initialize the query agent"""
    global agent, conversation_state
    
    try:
        if not os.path.exists(db_path):
            return f"❌ Error: Database not found at {db_path}"
        
        if not os.path.exists(vector_db):
            return f"❌ Error: Vector database not found at {vector_db}\n\nPlease run analyze_existing_db.py first to create the vector database."
        
        # Create new conversation state
        conversation_state = ConversationState()
        
        # Initialize enhanced agent
        agent = QueryAgentEnhanced(
            source_db_path=db_path,
            vector_db_path=vector_db,
            llm_model=model,
            conversation_state=conversation_state,
            max_context_messages=5,
            max_data_contexts=3
        )
        
        logger.info(f"Agent initialized with model: {model}")
        
        # Get database summary
        summary = agent.get_summary()
        
        summary_text = "✅ **Agent Initialized Successfully!**\n\n"
        summary_text += f"**Database:** {db_path}\n"
        summary_text += f"**Model:** {model}\n"
        summary_text += f"**Conversation ID:** {conversation_state.conversation_id[:8]}...\n"
        summary_text += f"**Total Tables:** {summary.get('tables', 0)}\n\n"
        
        if summary.get('table_details'):
            summary_text += "**Available Tables:**\n"
            for table_info in summary['table_details']:
                summary_text += f"- **{table_info['table_name']}**: {table_info.get('description', 'N/A')}\n"
                summary_text += f"  - Category: {table_info.get('category', 'unknown')}\n"
                summary_text += f"  - Rows: {table_info.get('rows', 0):,} | Columns: {table_info.get('columns', 0)}\n\n"

        
        return summary_text
        
    except Exception as e:
        logger.error(f"Failed to initialize agent: {e}", exc_info=True)
        error_msg = f"❌ Error initializing agent: {str(e)}\n\n"
        error_msg += "**Please ensure:**\n"
        error_msg += "1. Ollama is running (ollama serve)\n"
        error_msg += f"2. Model is pulled (ollama pull {model})\n"
        error_msg += "3. Database files exist\n"
        error_msg += "4. Vector database is created (run analyze_existing_db.py first)"
        return error_msg

def load_figure_from_json(figure_json: str) -> Optional[go.Figure]:
    """Load a Plotly figure from JSON string"""
    try:
        fig_dict = json.loads(figure_json)
        return go.Figure(fig_dict)
    except Exception as e:
        logger.error(f"Failed to load figure from JSON: {e}")
        return None

def get_chart_emoji(chart_type: str) -> str:
    """Get emoji for chart type"""
    emoji_map = {
        "bar": "📊",
        "line": "📈",
        "pie": "🥧",
        "scatter": "⚫",
        "histogram": "📶",
        "box": "📦",
        "multiple_bar": "📊"
    }
    return emoji_map.get(chart_type, "📊")

def process_question_with_history(
    question: str,
    chat_history: List
) -> Tuple[List, Optional[pd.DataFrame], Optional[go.Figure], str, str, List]:
    """
    Process question with conversation context
    
    Returns:
        - Updated chat history
        - DataFrame
        - Plotly figure
        - SQL query
        - Conversation info
        - Chart history for gallery
    """
    global agent, stored_figures, chart_history
    
    if agent is None:
        error_msg = "⚠️ Please initialize the agent first!"
        chat_history.append((question, error_msg))
        return chat_history, None, None, "", "", []
    
    if not question.strip():
        return chat_history, None, None, "", "", build_gallery_images()
    
    try:
        # Process with context awareness (automatically handles follow-up questions)
        result = agent.answer_question_with_context(
            question=question,
            reuse_data=False  # Let the agent decide based on context
        )
        
        if not result.get("success", False):
            error_msg = f"❌ Error: {result.get('error', 'Unknown error')}"
            chat_history.append((question, error_msg))
            return chat_history, None, None, "", "", build_gallery_images()
        
        # Build response message
        response_parts = []
        
        # Add intent information
        intent = result.get("intent", "unknown")
        intent_emoji = {
            "new_query": "🔍",
            "re_visualize": "📊",
            "transform": "🔧",
            "combine": "🔗",
            "compare": "⚖️",
            "clarify": "❓"
        }
        response_parts.append(f"{intent_emoji.get(intent, '💬')} **Intent**: {intent.replace('_', ' ').title()}")
        
        # Add data reuse indicator
        if result.get("reused_data"):
            response_parts.append("♻️ *Using previous data*")
        
        # Add answer
        response_parts.append(f"\n{result['answer']}")
        
        # Add visualization info and store figure
        chart = None
        if result.get("visualization"):
            viz_type = result["visualization"]["type"]
            chart = result["visualization"].get("chart")
            
            # Store figure in global dict using message index
            message_index = len(chat_history)
            if chart:
                stored_figures[message_index] = chart
                # Add to chart history
                chart_history.append((message_index, viz_type, chart))
            
            # Add chart indicator with message number for easy reference
            emoji = get_chart_emoji(viz_type)
            response_parts.append(f"\n{emoji} **Created {viz_type.replace('_', ' ').title()} Chart** (Message #{message_index})")
            response_parts.append("*💡 Click the thumbnail below to restore*")
        
        response = "\n".join(response_parts)
        
        # Update chat history - always add text response
        # Note: Charts are displayed in the separate plot_output area
        chat_history.append((question, response))
        
        # Extract components
        df = result.get("data")
        sql = result.get("sql_query", result.get("transformation", ""))
        
        # Get conversation summary
        summary = agent.get_conversation_summary()
        conv_info = f"""**Conversation Summary**
- Messages: {summary['message_count']}
- Data Contexts: {summary['data_contexts']}
- Visualizations: {summary['visualizations']}
- Conversation ID: {summary['conversation_id'][:8]}..."""
        
        return chat_history, df, chart, sql, conv_info, build_gallery_images()
        
    except Exception as e:
        logger.error(f"Error processing question: {e}", exc_info=True)
        error_msg = f"❌ Error: {str(e)}"
        chat_history.append((question, error_msg))
        return chat_history, None, None, "", "", build_gallery_images()

def reset_conversation() -> Tuple[List, str, List]:
    """Reset conversation and start fresh"""
    global agent, conversation_state, stored_figures, chart_history
    
    if agent is not None:
        # Create new conversation state
        conversation_state = ConversationState()
        agent.conversation_state = conversation_state
        # Clear stored figures and chart history
        stored_figures = {}
        chart_history = []
        return [], f"✅ Conversation reset! New ID: {conversation_state.conversation_id[:8]}...", []
    
    return [], "⚠️ No active agent", []

def restore_chart_from_history(message_index: int) -> Optional[go.Figure]:
    """Restore a chart from conversation history by message index"""
    global agent
    
    if agent is None:
        logger.warning("No active agent")
        return None
    
    try:
        # First check stored_figures dict
        if message_index in stored_figures:
            logger.info(f"Restoring chart from message #{message_index}")
            return stored_figures[message_index]
        
        # Otherwise, try to load from conversation state
        messages = agent.conversation_state.messages
        # Find assistant messages with visualizations
        viz_messages = [msg for msg in messages if msg.role == "assistant" and msg.figure_json]
        
        # Map assistant message index to actual message
        if message_index < len(viz_messages):
            figure_json = viz_messages[message_index].figure_json
            if figure_json:
                fig = load_figure_from_json(figure_json)
                # Cache it for future use
                stored_figures[message_index] = fig
                return fig
        
        logger.warning(f"No figure found for message index {message_index}")
        return None
        
    except Exception as e:
        logger.error(f"Error restoring chart: {e}")
        return None

def select_chart_from_gallery(evt: gr.SelectData) -> Optional[go.Figure]:
    """Handle gallery selection event - restore chart when thumbnail is clicked"""
    global chart_history
    
    try:
        selected_index = evt.index
        if selected_index < len(chart_history):
            message_idx, chart_type, figure = chart_history[selected_index]
            logger.info(f"Gallery: Restoring {chart_type} chart from message #{message_idx}")
            return figure
        return None
    except Exception as e:
        logger.error(f"Error selecting from gallery: {e}")
        return None

# Custom CSS for better UI
custom_css = """
.viz-history {
    max-height: 400px;
    overflow-y: auto;
    padding: 10px;
    border: 1px solid #ddd;
    border-radius: 5px;
}

.chat-message {
    padding: 10px;
    margin: 5px 0;
}

.intent-badge {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 12px;
    font-size: 0.85em;
    font-weight: bold;
    margin-right: 5px;
}

.sql-code {
    background-color: #f5f5f5;
    padding: 10px;
    border-radius: 5px;
    font-family: monospace;
    overflow-x: auto;
}
"""

# Build Gradio Interface
with gr.Blocks(title="SQL Query Agent", css=custom_css, theme=gr.themes.Soft()) as demo:
    
    gr.Markdown("""
    # 🤖 SQL Query Agent
    ### Ask questions about your database
    """)
    
    # Initialization Section
    with gr.Accordion("⚙️ Configuration", open=True):
        with gr.Row():
            with gr.Column(scale=2):
                db_path_input = gr.Textbox(
                    label="Source Database Path",
                    value="analysis.db",
                    placeholder="Path to your SQLite database"
                )
            with gr.Column(scale=2):
                vector_db_input = gr.Textbox(
                    label="Vector Database Path",
                    value="./chroma_db_768dim",
                    placeholder="Path to ChromaDB metadata"
                )
        
        with gr.Row():
            with gr.Column(scale=2):
                model_dropdown = gr.Dropdown(
                    label="Ollama Model",
                    choices=["qwen2.5:7b", "qwen2.5:3b"],
                    value="qwen2.5:7b",
                    allow_custom_value=True
                )
            with gr.Column(scale=2):
                ollama_url_input = gr.Textbox(
                    label="Ollama Server URL",
                    value="http://localhost:11434",
                    placeholder="http://localhost:11434"
                )
            with gr.Column(scale=1):
                init_button = gr.Button("🚀 Initialize Agent", variant="primary", size="lg")
    
    init_output = gr.Markdown(label="Initialization Status")
    
    gr.Markdown("---")
    
    # Main Interface
    with gr.Row():
        # Left side - Visualization & Data (70% width)
        with gr.Column(scale=7):
            gr.Markdown("## 📊 Visualization")
            
            plot_output = gr.Plot(label="Chart", show_label=False)
            
            with gr.Accordion("📋 Full Data Table", open=False):
                dataframe_output = gr.Dataframe(
                    label="Results",
                    interactive=False,
                    wrap=True
                )
            
            with gr.Accordion("🔍 SQL Query & Context Info", open=False):
                sql_output = gr.Code(
                    label="Generated SQL",
                    language="sql",
                    lines=5
                )
                conv_info = gr.Markdown("**No active conversation**")
        
        # Right side - Chat (30% width)
        with gr.Column(scale=3):
            gr.Markdown("## 💬 Chat")
            
            chatbot = gr.Chatbot(
                label="Conversation",
                height=600,
                show_label=False,
                type='tuples',
                bubble_full_width=False
            )
            
            question_input = gr.Textbox(
                label="Your Question",
                placeholder="Ask me anything about your data...",
                lines=3,
                show_label=False
            )
            
            with gr.Row():
                submit_btn = gr.Button("📤 Send", variant="primary", scale=3)
                stop_btn = gr.Button("⏹ Stop", variant="stop", scale=1)
                clear_btn = gr.Button("🗑️ Clear", scale=1)
                reset_btn = gr.Button("🔄 Reset", scale=1)
            
            gr.Markdown("---")
            gr.Markdown("### 📊 Chart Thumbnails")
            gr.Markdown("*Click any thumbnail to restore that chart*")
            
            # Gallery for chart thumbnails
            chart_gallery = gr.Gallery(
                label="Past Charts",
                show_label=False,
                columns=3,
                rows=2,
                height="auto",
                object_fit="contain",
                allow_preview=False
            )
    
    # Event Handlers
    init_button.click(
        fn=initialize_agent,
        inputs=[db_path_input, vector_db_input, model_dropdown],
        outputs=init_output
    )
    
    submit_event = submit_btn.click(
        fn=process_question_with_history,
        inputs=[question_input, chatbot],
        outputs=[chatbot, dataframe_output, plot_output, sql_output, conv_info, chart_gallery]
    )
    submit_event.then(
        fn=lambda: "",
        outputs=[question_input]
    )
    
    enter_event = question_input.submit(
        fn=process_question_with_history,
        inputs=[question_input, chatbot],
        outputs=[chatbot, dataframe_output, plot_output, sql_output, conv_info, chart_gallery]
    )
    enter_event.then(
        fn=lambda: "",
        outputs=[question_input]
    )
    
    clear_btn.click(
        fn=lambda: ([], None, None, "", "", []),
        outputs=[chatbot, dataframe_output, plot_output, sql_output, conv_info, chart_gallery]
    )
    
    reset_btn.click(
        fn=reset_conversation,
        outputs=[chatbot, conv_info, chart_gallery]
    )
    
    stop_btn.click(
        fn=lambda: None,
        inputs=None,
        outputs=None,
        cancels=[submit_event, enter_event]
    )
    
    # Click thumbnail in gallery to restore chart
    chart_gallery.select(
        fn=select_chart_from_gallery,
        outputs=[plot_output]
    )
    
    # Examples
    gr.Examples(
        examples=[
            ["Show me the top 5 products by sales"],
            ["Visualize that as a bar chart"],
            ["Show it as a pie chart instead"],
            ["Filter those with sales > 1000"],
            ["Compare that with last month's data"],
            ["Sort by price descending"],
        ],
        inputs=question_input,
        label="💡 Example Questions (Try having a conversation!)"
    )

if __name__ == "__main__":
    print("\n" + "="*80)
    print("🚀 Starting Enhanced Ollama Query Agent with Conversation Memory")
    print("="*80)
    print("\nMake sure:")
    print("1. Ollama is running (ollama serve)")
    print("2. Your model is pulled (e.g., ollama pull qwen2.5:7b)")
    print("3. Database files exist (analysis.db and ./chroma_db_768dim)")
    print("4. Vector database is created (run analyze_existing_db.py first)")

    print("\n" + "="*80 + "\n")
    
    demo.launch(
        server_name="0.0.0.0",
        server_port=6969,
        share=False,
        show_error=True
    )
