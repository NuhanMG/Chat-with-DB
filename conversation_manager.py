"""
Conversation State Management for Multi-Turn Analytics
Handles conversation history, data context, and visualization tracking
"""
from typing import Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass, field
import uuid
import pandas as pd


# Dataclass to structure individual messages in the conversation
@dataclass
class Message:
    """Represents a single message in the conversation"""
    # The role of the message sender: 'user' or 'assistant'
    role: str  # "user" or "assistant"
    # The actual text content of the message
    content: str
    # Timestamp when the message was created
    timestamp: datetime = field(default_factory=datetime.now)
    # Optional SQL query associated with the message (for assistant responses)
    sql_query: Optional[str] = None
    # Optional snapshot of the dataframe metadata (not the full data)
    dataframe_snapshot: Optional[Dict] = None  # Store metadata, not full DF
    # Optional type of visualization generated
    visualization: Optional[str] = None  # Chart type
    # Optional JSON string representation of the Plotly figure
    figure_json: Optional[str] = None  # Store Plotly figure as JSON string
    # Additional metadata dictionary for extensibility
    metadata: Dict = field(default_factory=dict)


# Dataclass to store context about data retrieved during the conversation
@dataclass
class DataContext:
    """Represents a dataset context in the conversation"""
    # The query used to retrieve this data
    query: str
    # List of column names in the dataset
    columns: List[str]
    # Number of rows in the dataset
    row_count: int
    # A sample of the data for preview/context
    sample_data: Dict
    # Timestamp when this data context was created
    timestamp: datetime = field(default_factory=datetime.now)


# Dataclass to keep a record of visualizations generated
@dataclass
class VisualizationRecord:
    """Records a visualization created during conversation"""
    # The user question that prompted the visualization
    question: str
    # The type of chart generated (e.g., 'bar', 'line')
    chart_type: str
    # Summary of the data being visualized
    data_summary: str
    # Timestamp when the visualization was created
    timestamp: datetime = field(default_factory=datetime.now)


class ConversationState:
    """Manages conversation state across multiple turns"""
    
    def __init__(self, conversation_id: Optional[str] = None):
        # Initialize conversation ID, generating a new UUID if not provided
        self.conversation_id = conversation_id or str(uuid.uuid4())
        # List to store the history of messages
        self.messages: List[Message] = []
        # List to store data contexts (query results)
        self.data_contexts: List[DataContext] = []
        # List to store records of visualizations created
        self.visualizations: List[VisualizationRecord] = []
        # Record the start time of the conversation session
        self.start_time = datetime.now()
    
    def add_message(self, message: Message):
        """Add a message to conversation history"""
        # Append the new message object to the messages list
        self.messages.append(message)
    
    def add_data_context(self, context: DataContext):
        """Add a data context (query result) to history"""
        # Append the new data context to the list
        self.data_contexts.append(context)
        # Keep only last N contexts to manage memory
        # Limit the number of stored contexts to manage memory usage
        if len(self.data_contexts) > 10:
            self.data_contexts = self.data_contexts[-10:]
    
    def add_visualization(self, viz: VisualizationRecord):
        """Add a visualization record"""
        # Append the new visualization record to the list
        self.visualizations.append(viz)
    
    def get_recent_messages(self, n: int = 5) -> List[Message]:
        """Get last N messages"""
        # Return the last n messages if there are enough, otherwise return all
        return self.messages[-n:] if len(self.messages) >= n else self.messages
    
    def get_latest_dataframe(self) -> Optional[pd.DataFrame]:
        """Try to reconstruct latest DataFrame from context"""
        if not self.messages:
            return None
        
        # Iterate backwards through messages to find the most recent dataframe snapshot
        for msg in reversed(self.messages):
            if msg.role == "assistant" and msg.dataframe_snapshot:
                # For now, return None as we only store metadata
                # In full implementation, this could reconstruct from snapshot
                return None
        
        # Return None if no dataframe snapshot is found
        return None
    
    def clear_old_contexts(self, max_keep: int = 3):
        """Clear old data contexts to save memory"""
        # If we have more contexts than the limit, slice the list to keep only the recent ones
        if len(self.data_contexts) > max_keep:
            self.data_contexts = self.data_contexts[-max_keep:]
    
    def export_conversation(self) -> Dict:
        """Export conversation state to dict for persistence"""
        # Create a dictionary representation of the entire conversation state
        return {
            "conversation_id": self.conversation_id,
            "start_time": self.start_time.isoformat(),
            "message_count": len(self.messages),
            # Serialize all messages
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
            # Serialize all data contexts
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
            # Serialize all visualization records
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
    
    def import_conversation(self, data: Dict):
        """Import conversation state from dict"""
        # Restore conversation ID and start time from the dictionary
        self.conversation_id = data.get("conversation_id", str(uuid.uuid4()))
        self.start_time = datetime.fromisoformat(data.get("start_time", datetime.now().isoformat()))
        
        # Import messages
        self.messages = [
            Message(
                role=msg["role"],
                content=msg["content"],
                timestamp=datetime.fromisoformat(msg["timestamp"]),
                sql_query=msg.get("sql_query"),
                dataframe_snapshot=msg.get("dataframe_snapshot"),
                visualization=msg.get("visualization"),
                figure_json=msg.get("figure_json"),
                metadata=msg.get("metadata", {})
            )
            for msg in data.get("messages", [])
        ]
        
        # Import data contexts
        self.data_contexts = [
            DataContext(
                query=ctx["query"],
                columns=ctx["columns"],
                row_count=ctx["row_count"],
                sample_data=ctx.get("sample_data", {}),
                timestamp=datetime.fromisoformat(ctx["timestamp"])
            )
            for ctx in data.get("data_contexts", [])
        ]
        
        # Import visualizations
        self.visualizations = [
            VisualizationRecord(
                question=viz["question"],
                chart_type=viz["chart_type"],
                data_summary=viz["data_summary"],
                timestamp=datetime.fromisoformat(viz["timestamp"])
            )
            for viz in data.get("visualizations", [])
        ]
