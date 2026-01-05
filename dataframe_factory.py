"""
Unified DataFrame Factory - Automatically routes to Pandas or Dask
based on data size for optimal performance with large datasets.

This module provides transparent handling of both Pandas and Dask DataFrames,
enabling seamless scaling from small to large datasets without code changes.
"""
from typing import Union, Optional, List, Any
import pandas as pd
import dask.dataframe as dd
import sqlite3
import logging
import time

logger = logging.getLogger(__name__)

# Type alias for unified DataFrame (can be either Pandas or Dask)
UnifiedDataFrame = Union[pd.DataFrame, dd.DataFrame]


class DataFrameFactory:
    """
    Factory class to create appropriate DataFrame type based on data size.
    Automatically routes to Pandas for small data and Dask for large data.
    """
    
    # Thresholds for routing decisions (tunable via environment or config)
    SMALL_DATA_THRESHOLD = 100_000      # < 100K rows -> Pure Pandas
    MEDIUM_DATA_THRESHOLD = 10_000_000  # 100K-10M rows -> Dask
    DASK_PARTITIONS = 8                 # Number of partitions for Dask
    
    # Feature flag to enable/disable Dask (for easy rollback)
    ENABLE_DASK = True
    
    @staticmethod
    def estimate_row_count(sql: str, conn: sqlite3.Connection) -> int:
        """
        Estimate the number of rows a SQL query will return.
        
        Args:
            sql: The SQL query
            conn: SQLite connection
            
        Returns:
            Estimated row count (0 if estimation fails)
        """
        try:
            # Simple heuristic: wrap query in COUNT(*)
            # Handle queries that might have ORDER BY or LIMIT
            clean_sql = sql.strip().rstrip(';')
            
            # Remove ORDER BY clause for counting (not needed and can cause issues)
            import re
            count_sql_base = re.sub(r'\s+ORDER\s+BY\s+.*?(?=LIMIT|$)', ' ', clean_sql, flags=re.IGNORECASE)
            
            # Remove existing LIMIT for accurate count
            count_sql_base = re.sub(r'\s+LIMIT\s+\d+', '', count_sql_base, flags=re.IGNORECASE)
            
            count_sql = f"SELECT COUNT(*) FROM ({count_sql_base}) AS subquery"
            cursor = conn.cursor()
            result = cursor.execute(count_sql).fetchone()
            return result[0] if result else 0
        except Exception as e:
            logger.warning(f"Could not estimate row count: {e}. Defaulting to 0")
            return 0
    
    @classmethod
    def from_sql(
        cls, 
        sql: str, 
        conn: sqlite3.Connection,
        force_pandas: bool = False,
        force_dask: bool = False,
        params: tuple = None
    ) -> UnifiedDataFrame:
        """
        Load data from SQL using appropriate DataFrame backend.
        
        Args:
            sql: SQL query string
            conn: SQLite connection
            force_pandas: Force Pandas even for large data
            force_dask: Force Dask even for small data
            params: Optional query parameters
            
        Returns:
            Either pd.DataFrame or dd.DataFrame based on data size
        """
        start_time = time.time()
        
        # If Dask is disabled globally, always use Pandas
        if not cls.ENABLE_DASK:
            logger.info("Dask disabled globally, using Pandas")
            if params:
                return pd.read_sql_query(sql, conn, params=params)
            return pd.read_sql_query(sql, conn)
        
        if force_pandas:
            logger.info("🐼 Forcing Pandas backend (manual override)")
            if params:
                return pd.read_sql_query(sql, conn, params=params)
            return pd.read_sql_query(sql, conn)
        
        # For parameterized queries, use Pandas directly (simpler handling)
        if params:
            logger.info("🐼 Using Pandas for parameterized query")
            return pd.read_sql_query(sql, conn, params=params)
        
        # Estimate data size
        estimated_rows = cls.estimate_row_count(sql, conn)
        logger.info(f"📊 Estimated row count: {estimated_rows:,}")
        
        # Route to appropriate backend
        if force_dask or estimated_rows > cls.MEDIUM_DATA_THRESHOLD:
            result = cls._load_with_dask(sql, conn, estimated_rows)
            backend = "Dask (large)"
        elif estimated_rows > cls.SMALL_DATA_THRESHOLD:
            result = cls._load_with_dask_optimized(sql, conn, estimated_rows)
            backend = "Dask (medium)"
        else:
            logger.info(f"🐼 Using Pandas backend (small dataset: {estimated_rows:,} rows)")
            result = pd.read_sql_query(sql, conn)
            backend = "Pandas"
        
        duration = time.time() - start_time
        logger.info(f"✅ Data loaded in {duration:.2f}s using {backend}")
        
        return result
    
    @classmethod
    def _load_with_dask(
        cls, 
        sql: str, 
        conn: sqlite3.Connection, 
        estimated_rows: int
    ) -> dd.DataFrame:
        """
        Load large dataset using Dask with partitioning.
        
        Args:
            sql: SQL query
            conn: Database connection
            estimated_rows: Estimated number of rows
            
        Returns:
            Dask DataFrame
        """
        logger.info(f"🚀 Using Dask backend (large dataset: {estimated_rows:,} rows)")
        
        # Load to Pandas first, then convert to Dask with partitioning
        # This works well for SQLite which doesn't support OFFSET efficiently
        pandas_df = pd.read_sql_query(sql, conn)
        
        # Calculate optimal partition count
        partition_count = min(
            cls.DASK_PARTITIONS * 2,  # More partitions for large data
            max(1, len(pandas_df) // 100_000)  # ~100K rows per partition
        )
        
        dask_df = dd.from_pandas(pandas_df, npartitions=partition_count)
        logger.info(f"🔧 Created Dask DataFrame with {partition_count} partitions")
        
        return dask_df
    
    @classmethod
    def _load_with_dask_optimized(
        cls, 
        sql: str, 
        conn: sqlite3.Connection,
        estimated_rows: int
    ) -> dd.DataFrame:
        """
        Load medium-sized dataset with optimized Dask configuration.
        
        Args:
            sql: SQL query
            conn: Database connection
            estimated_rows: Estimated rows
            
        Returns:
            Dask DataFrame with optimal partitioning
        """
        logger.info(f"⚡ Using optimized Dask backend (medium dataset: {estimated_rows:,} rows)")
        
        pandas_df = pd.read_sql_query(sql, conn)
        
        # Use fewer partitions for medium data
        partition_count = max(2, min(4, len(pandas_df) // 50_000))
        
        dask_df = dd.from_pandas(pandas_df, npartitions=partition_count)
        logger.info(f"🔧 Created Dask DataFrame with {partition_count} partitions")
        
        return dask_df
    
    @staticmethod
    def to_pandas(df: UnifiedDataFrame) -> pd.DataFrame:
        """
        Convert any DataFrame type to Pandas.
        
        Args:
            df: Either Pandas or Dask DataFrame
            
        Returns:
            Pandas DataFrame
        """
        if isinstance(df, dd.DataFrame):
            logger.debug("Converting Dask DataFrame to Pandas")
            return df.compute()
        return df
    
    @staticmethod
    def is_dask(df: UnifiedDataFrame) -> bool:
        """Check if DataFrame is Dask type"""
        return isinstance(df, dd.DataFrame)
    
    @staticmethod
    def is_pandas(df: UnifiedDataFrame) -> bool:
        """Check if DataFrame is Pandas type"""
        return isinstance(df, pd.DataFrame) and not isinstance(df, dd.DataFrame)
    
    @staticmethod
    def get_length(df: UnifiedDataFrame) -> int:
        """
        Get DataFrame length (handles both Pandas and Dask).
        
        Note: For Dask, this triggers computation of length.
        
        Args:
            df: DataFrame of any type
            
        Returns:
            Row count
        """
        if isinstance(df, dd.DataFrame):
            return len(df)  # Dask computes length lazily
        return len(df)
    
    @staticmethod
    def get_columns(df: UnifiedDataFrame) -> List[str]:
        """Get column names (works for both types)"""
        return list(df.columns)
    
    @staticmethod
    def head(df: UnifiedDataFrame, n: int = 5) -> pd.DataFrame:
        """
        Get first N rows as Pandas DataFrame.
        
        Args:
            df: DataFrame of any type
            n: Number of rows
            
        Returns:
            Pandas DataFrame with first N rows
        """
        if isinstance(df, dd.DataFrame):
            return df.head(n, npartitions=-1)  # Get from all partitions if needed
        return df.head(n)
    
    @staticmethod
    def copy(df: UnifiedDataFrame) -> UnifiedDataFrame:
        """
        Create a copy of DataFrame (preserves type).
        
        For Dask DataFrames, this returns the same reference since they are immutable.
        For Pandas DataFrames, this creates a deep copy.
        """
        if isinstance(df, dd.DataFrame):
            # Dask DataFrames are immutable, operations return new DataFrames
            return df
        return df.copy()
    
    @staticmethod
    def empty_check(df: UnifiedDataFrame) -> bool:
        """
        Check if DataFrame is empty.
        
        Args:
            df: DataFrame of any type
            
        Returns:
            True if DataFrame has no rows
        """
        if isinstance(df, dd.DataFrame):
            # For Dask, check length (triggers computation)
            return len(df) == 0
        return df.empty
    
    @staticmethod
    def get_dtypes(df: UnifiedDataFrame) -> pd.Series:
        """Get data types of all columns"""
        return df.dtypes
    
    @staticmethod
    def select_dtypes(df: UnifiedDataFrame, include: List[str] = None, exclude: List[str] = None) -> UnifiedDataFrame:
        """
        Select columns by data type.
        
        Args:
            df: DataFrame
            include: Data types to include (e.g., ['number'])
            exclude: Data types to exclude
            
        Returns:
            DataFrame with only matching columns
        """
        if isinstance(df, dd.DataFrame):
            # Dask supports select_dtypes
            return df.select_dtypes(include=include, exclude=exclude)
        return df.select_dtypes(include=include, exclude=exclude)


# Convenience wrapper functions for cleaner code
def from_sql(sql: str, conn: sqlite3.Connection, **kwargs) -> UnifiedDataFrame:
    """Convenience function to create DataFrame from SQL"""
    return DataFrameFactory.from_sql(sql, conn, **kwargs)


def to_pandas(df: UnifiedDataFrame) -> pd.DataFrame:
    """Convenience function to convert to Pandas"""
    return DataFrameFactory.to_pandas(df)


def ensure_pandas(df: UnifiedDataFrame, max_rows: Optional[int] = None) -> pd.DataFrame:
    """
    Ensure we have a Pandas DataFrame, optionally limiting rows.
    
    This is the KEY function for visualization and display operations.
    It guarantees a Pandas DataFrame output regardless of input type.
    
    Args:
        df: Input DataFrame (Pandas or Dask)
        max_rows: Maximum rows to return (samples if larger)
        
    Returns:
        Pandas DataFrame (potentially sampled)
    """
    if isinstance(df, dd.DataFrame):
        total_rows = len(df)
        if max_rows and total_rows > max_rows:
            logger.info(f"📉 Sampling {max_rows} rows from {total_rows:,} total (Dask)")
            return df.head(max_rows, npartitions=-1)
        return df.compute()
    
    # Already Pandas
    if max_rows and len(df) > max_rows:
        logger.info(f"📉 Limiting to {max_rows} rows from {len(df):,} total (Pandas)")
        return df.head(max_rows)
    return df


def get_backend_name(df: UnifiedDataFrame) -> str:
    """Get a human-readable name for the DataFrame backend"""
    if isinstance(df, dd.DataFrame):
        return "Dask"
    return "Pandas"


def get_info(df: UnifiedDataFrame) -> dict:
    """
    Get comprehensive info about a DataFrame.
    
    Returns:
        Dictionary with DataFrame metadata
    """
    return {
        "backend": get_backend_name(df),
        "rows": DataFrameFactory.get_length(df),
        "columns": DataFrameFactory.get_columns(df),
        "column_count": len(df.columns),
        "is_dask": DataFrameFactory.is_dask(df),
        "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()}
    }
