# Libraries

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.graph import END, StateGraph
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.tools import tool
from langchain_core.messages import AIMessage
from langchain_core.messages import (
    BaseMessage,
    HumanMessage,
    ToolMessage,
)
from langgraph.prebuilt import ToolNode

import operator
from typing import Annotated, Sequence, TypedDict, Literal
import functools
import streamlit as st
import getpass
import os
from dotenv import load_dotenv
from langchain_ollama import ChatOllama
from langchain.callbacks.manager import CallbackManager
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from pydantic import BaseModel

load_dotenv()

# LLM Model
callback = CallbackManager([StreamingStdOutCallbackHandler()])
llm = ChatOllama(
    model="llama3.1",
    callback_manager=callback,
    temperature=0.0
)

# Agent Initialization
def Agent(llm, tools, system_message: str):
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                system_message
            ),
            MessagesPlaceholder(variable_name="messages"),
        ]
    )
    prompt = prompt.partial(system_message=system_message)
    prompt = prompt.partial(tool_names=", ".join([tool.name for tool in tools]))
    return prompt | llm.bind_tools(tools)

# Tavily Initialization
os.environ["TAVILY_API_KEY"] = "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"
tavily_tool = TavilySearchResults(max_results=20)

# Agent State
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    sender: str
    supervisor_invocations: int
    finalizing: bool

# Analysis Data
class AnalysisData(BaseModel):
    company_name: str
    competitor_analysis: str
    market_trends: str
    financial_analysis: str
    business_strategy: str


# Agent State Management
def agent_node(state, agent, name):
    if name == "research_supervisor":
        state["supervisor_invocations"] += 1
        if state["supervisor_invocations"] > 5:
            state["finalizing"] = True 
    
    if state['finalizing']:
        state["messages"].append(HumanMessage(content="Conclude research and compile all the information provided by other assistants and organize it as a competitor analysis report. Prefix the answer with 'FINAL ANSWER'."))

    result = agent.invoke(state)
    if isinstance(result, ToolMessage):
        pass
    else:
        result = AIMessage(**result.dict(exclude={"type", "name"}), name=name)
    return {
        "messages": [result],
        "sender": name,
        "supervisor_invocations": state["supervisor_invocations"],
        "finalizing": state["finalizing"],
    }

# Supervisor Agent
research_supervisor_agent = Agent(
    llm,
    [tavily_tool],
    system_message="You are the most senior and experienced competitor analysis manager. You have a team of assistants - 'market_trends_agent', 'financial_analysis_agent', 'business_strategy_agent', 'competition_analysis_agent'. For the company input, delegate each task to different assistants. Your task is to compile all the information provided by other assistants and organize it as a competitor analysis report. The final answer should include all the necessary information in a well-formatted manner."
)
research_supervisor_node = functools.partial(agent_node, agent=research_supervisor_agent, name="research_supervisor")

# Trend Analysis Agents
market_trends_agent = Agent(
    llm,
    [tavily_tool],
    system_message="You are an expert in analyzing market trends. Provide detailed information about the market trends relevant to the company name input."
)
market_trends_node = functools.partial(agent_node, agent=market_trends_agent, name="market_trends_agent")

# Financial Analysis Agent
financial_analysis_agent = Agent(
    llm,
    [tavily_tool],
    system_message="You are a skilled financial analyst. Provide detailed financial data about the company input."
)
financial_analysis_node = functools.partial(agent_node, agent=financial_analysis_agent, name="financial_analysis_agent")

# Business Strategy Agent
business_strategy_agent = Agent(
    llm,
    [tavily_tool],
    system_message="You are an expert in business strategies. Provide detailed business strategy analysis for the company input."
)
business_strategy_node = functools.partial(agent_node, agent=business_strategy_agent, name="business_strategy_agent")

# Competition Analysis Agent
competition_analysis_agent = Agent(
    llm,
    [tavily_tool],
    system_message="You are an expert in competitor analysis. Identify and assess key competitors of the company input, providing detailed strengths and weaknesses for each competitor."
)
competition_analysis_node = functools.partial(agent_node, agent=competition_analysis_agent, name="competition_analysis_agent")

# Tool Node
tools = [tavily_tool]
tool_node = ToolNode(tools)

# Responsible to transistion to next state
def router(state) -> Literal["call_tool", "__end__", "continue"]:
    messages = state["messages"]
    last_message = messages[-1]
    if state["finalizing"]:
        return "__end__"
    if last_message.tool_calls:
        return "call_tool"
    if "FINAL ANSWER" in last_message.content:
        return "__end__"
    return "continue"

# Graph Construction
workflow = StateGraph(AgentState)

workflow.add_node("research_supervisor", research_supervisor_node)
workflow.add_node("market_trends_agent", market_trends_node)
workflow.add_node("financial_analysis_agent", financial_analysis_node)
workflow.add_node("business_strategy_agent", business_strategy_node)
workflow.add_node("competition_analysis_agent", competition_analysis_node)
workflow.add_node("call_tool", tool_node)

workflow.add_edge("research_supervisor", END)

workflow.add_conditional_edges(
    "research_supervisor",
    router,
    {"continue": "competition_analysis_agent", "call_tool": "call_tool", "__end__": END},
)
workflow.add_conditional_edges(
    "competition_analysis_agent",
    router,
    {"continue": "market_trends_agent", "call_tool": "call_tool", "__end__": END},
)
workflow.add_conditional_edges(
    "market_trends_agent",
    router,
    {"continue": "financial_analysis_agent", "call_tool": "call_tool", "__end__": END},
)
workflow.add_conditional_edges(
    "financial_analysis_agent",
    router,
    {"continue": "business_strategy_agent", "call_tool": "call_tool", "__end__": END},
)
workflow.add_conditional_edges(
    "business_strategy_agent",
    router,
    {"continue": "research_supervisor", "call_tool": "call_tool", "__end__": END},
)
workflow.add_conditional_edges(
    "call_tool",
    lambda x: x["sender"],
    {
        "research_supervisor": "research_supervisor",
        "market_trends_agent": "market_trends_agent",
        "financial_analysis_agent": "financial_analysis_agent",
        "business_strategy_agent": "business_strategy_agent",
        "competition_analysis_agent": "competition_analysis_agent",
    },
)
workflow.set_entry_point("research_supervisor")

graph = workflow.compile()

# ###### Streamlit App #######
# Chat History
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

st.title("Competitor Analysis Assistant")
user_input_company_name = st.text_input("Enter company name:", key="user_input")

query_prompt = f"""Analyze the competitor {user_input_company_name}. The analysis should include the following:
1. Competitor Analysis (Identify key competitors, their strengths, and weaknesses)
2. Market Trends
3. Financial Analysis
4. Business Strategy
Once done, finish."""

if st.button("Submit"):
    if user_input_company_name:
        output = graph.invoke({"messages": [HumanMessage(content=query_prompt)], "supervisor_invocations": 0, "finalizing": False}, {"recursion_limit": 150})
        
        analysis_data = AnalysisData(
            company_name=user_input_company_name,
            competitor_analysis=output['messages'][0].content,
            market_trends=output['messages'][1].content,
            financial_analysis=output['messages'][2].content,
            business_strategy=output['messages'][3].content
        )
        
        st.session_state.chat_history.append({"You": user_input_company_name, "Researcher": analysis_data.json()})

        st.session_state.user_input_company_name = ""

for chat in st.session_state.chat_history:
    st.write(f"**You**: {chat['You']}")
    st.write(f"**Researcher**: {chat['Researcher']}")
    st.write('---')

    # Analysis data in a structured format
    analysis = AnalysisData.parse_raw(chat['Researcher'])
    st.write(f"**Company Name**: {analysis.company_name}")
    st.write(f"**Competitor Analysis**: {analysis.competitor_analysis}")
    st.write(f"**Market Trends**: {analysis.market_trends}")
    st.write(f"**Financial Analysis**: {analysis.financial_analysis}")
    st.write(f"**Business Strategy**: {analysis.business_strategy}")
    st.write('---')