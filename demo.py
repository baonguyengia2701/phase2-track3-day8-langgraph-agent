import os
import json
from langgraph_agent_lab.graph import build_graph
from langgraph_agent_lab.state import AgentState
from langgraph.checkpoint.sqlite import SqliteSaver
import sqlite3

def print_step(event):
    for key, val in event.items():
        print(f"[{key}]")
        if "events" in val:
            for e in val["events"]:
                print(f"  -> {e['node']}: {e['message']}")
        if "messages" in val:
            print(f"  -> messages: {val['messages'][-1]}")
        if "final_answer" in val:
            print(f"  -> ANSWER: {val['final_answer']}")

def run_demo():
    print("="*50)
    print("DEMO LANGGRAPH AGENT")
    print("="*50)
    
    # 1. Khởi tạo graph với SQLite Checkpointer
    conn = sqlite3.connect("checkpoints.db", check_same_thread=False)
    checkpointer = SqliteSaver(conn)
    graph = build_graph(checkpointer=checkpointer)
    
    print("\n--- SCENARIO 1: AUTOMATIC PROCESSING (SIMPLE) ---")
    state1 = {"query": "How do I reset my password?", "thread_id": "demo-thread-1", "max_attempts": 3}
    config1 = {"configurable": {"thread_id": "demo-thread-1"}}
    for event in graph.stream(state1, config1):
        print_step(event)
        
    print("\n--- SCENARIO 2: TRANSIENT FAILURE AND DEAD LETTER (S07) ---")
    state2 = {"query": "System failure cannot recover after multiple attempts", "thread_id": "demo-thread-2", "max_attempts": 1}
    config2 = {"configurable": {"thread_id": "demo-thread-2"}}
    for event in graph.stream(state2, config2):
        print_step(event)

    print("\n--- SCENARIO 3: HUMAN-IN-THE-LOOP (RISKY) ---")
    print("*(Simulating LANGGRAPH_INTERRUPT=true)*")
    os.environ["LANGGRAPH_INTERRUPT"] = "true"
    
    state3 = {"query": "Please refund this customer immediately", "thread_id": "demo-thread-3", "max_attempts": 3}
    config3 = {"configurable": {"thread_id": "demo-thread-3"}}
    
    # Run 1: Will be interrupted at Approval node
    for event in graph.stream(state3, config3):
        print_step(event)
        
    print("\n[SYSTEM PAUSED WAITING FOR HUMAN APPROVAL - HITL]")
    
    # Run 2: Resume by approving
    print(">> Admin clicks Approve (Approved=True)...")
    for event in graph.stream(None, config3):
        print_step(event)

if __name__ == "__main__":
    run_demo()
