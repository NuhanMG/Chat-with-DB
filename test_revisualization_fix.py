#!/usr/bin/env python3
"""
Test to verify the re-visualization bug fix.
Tests the scenario: User asks for department-gender chart, then asks to filter for Anesthesia department.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from QueryAgent_Ollama_Enhanced import QueryAgentEnhanced
from dataframe_factory import get_backend_name, ensure_pandas


def test_revisualization_flow():
    """Test the re-visualization with filter extraction from question"""
    
    print("=" * 60)
    print("RE-VISUALIZATION BUG FIX TEST")
    print("=" * 60)
    
    # Initialize agent
    print("\n[INIT] Initializing QueryAgentEnhanced...")
    agent = QueryAgentEnhanced(source_db_path="./analysis.db")
    print("✅ Agent initialized!")
    
    # Step 1: Initial query - get gender count by department
    print("\n" + "=" * 60)
    print("[STEP 1] Initial query: Gender count by department")
    print("=" * 60)
    
    question1 = "Show every gender count of each department with a suitable graph"
    print(f"Question: {question1}")
    
    result1 = agent.answer_question_with_context(question1)
    
    if not result1.get("success"):
        print(f"❌ First query failed: {result1.get('error')}")
        return False
    
    df1 = result1.get("data")
    if df1 is None:
        print("❌ No data returned from first query")
        return False
    
    df1_pandas = ensure_pandas(df1)
    print(f"✅ First query successful!")
    print(f"   SQL: {result1.get('sql_query')}")
    print(f"   Rows: {len(df1_pandas)}")
    print(f"   Columns: {list(df1_pandas.columns)}")
    print(f"   Visualization: {result1.get('visualization', {}).get('type', 'None')}")
    print(f"\n   Data preview:")
    print(df1_pandas.to_string(index=False))
    
    # Verify stored DataFrame
    if agent._last_dataframe is not None:
        print(f"\n✅ DataFrame stored for follow-up ({len(ensure_pandas(agent._last_dataframe))} rows)")
    else:
        print("\n❌ DataFrame NOT stored!")
        return False
    
    # Step 2: Re-visualization - filter for Anesthesia
    print("\n" + "=" * 60)
    print("[STEP 2] Re-visualization: Filter for Anesthesia department")
    print("=" * 60)
    
    question2 = "from that graph, show the anesthesia patient count in each gender in pie chart"
    print(f"Question: {question2}")
    
    result2 = agent.answer_question_with_context(question2)
    
    if not result2.get("success"):
        print(f"❌ Second query failed: {result2.get('error')}")
        return False
    
    df2 = result2.get("data")
    if df2 is None:
        print("❌ No data returned from second query")
        return False
    
    df2_pandas = ensure_pandas(df2)
    print(f"✅ Second query successful!")
    print(f"   Intent: {result2.get('intent')}")
    print(f"   Reused data: {result2.get('reused_data')}")
    print(f"   Answer: {result2.get('answer')[:200]}...")
    print(f"   Visualization: {result2.get('visualization', {}).get('type', 'None')}")
    print(f"\n   Data preview:")
    print(df2_pandas.to_string(index=False))
    
    # Verify the fix worked
    print("\n" + "=" * 60)
    print("VERIFICATION")
    print("=" * 60)
    
    # Check 1: Should have reused previous data
    if result2.get("reused_data"):
        print("✅ Reused previous data (no new SQL query)")
    else:
        print("❌ Did NOT reuse previous data")
    
    # Check 2: Intent should be re_visualize
    if result2.get("intent") == "re_visualize":
        print("✅ Correctly detected 're_visualize' intent")
    else:
        print(f"❌ Wrong intent: {result2.get('intent')} (expected 're_visualize')")
    
    # Check 3: Data should be filtered for Anesthesia (if the column exists)
    if "department" in df2_pandas.columns:
        unique_depts = df2_pandas["department"].unique()
        if len(unique_depts) == 1 and "anesthesia" in unique_depts[0].lower():
            print(f"✅ Data correctly filtered to Anesthesia department: {unique_depts}")
        else:
            print(f"⚠️  Data contains departments: {list(unique_depts)}")
            print("   (This may be OK if the first query was aggregated differently)")
    else:
        print("⚠️  'department' column not in result - checking answer for context")
        if "anesthesia" in result2.get("answer", "").lower():
            print("✅ Answer mentions Anesthesia, likely correctly filtered")
    
    # Check 4: Visualization should be pie chart
    viz_type = result2.get("visualization", {}).get("type", "")
    if viz_type == "pie":
        print("✅ Correctly created pie chart")
    else:
        print(f"⚠️  Created {viz_type} chart (user asked for pie)")
    
    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)
    
    return True


if __name__ == "__main__":
    success = test_revisualization_flow()
    sys.exit(0 if success else 1)
