from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from PIL import Image as PILImage
from langchain_core.runnables.graph import MermaidDrawMethod
from io import BytesIO
from agents.supervisor import get_graph

load_dotenv()
llm = ChatOpenAI(
    model="gpt-4o",
    temperature=0
)
graph = get_graph(llm)

# ---------------------------------------------------------------------
#  Test run
# ---------------------------------------------------------------------

result = graph.invoke(
    {"messages": [
        HumanMessage(content="process these new bank statements."),
    ]}
)

print("\nFinal state:\n", result['messages'][-1].content)

result = graph.invoke(
    {"messages": [
        HumanMessage(content="Give me insights on last month's spending."),
    ]}
)

print("\nFinal state:\n", result['messages'][-1].content)

result = graph.invoke(
    {"messages": [
        HumanMessage(content="what's the capital of Mars?"),
    ]}
)

print("\nFinal state:\n", result['messages'][-1].content)


# ---------------------------------------------------------------------
#  Visualise graph
# ---------------------------------------------------------------------

# png_bytes = graph.get_graph(xray=True).draw_mermaid_png(
#     draw_method=MermaidDrawMethod.PYPPETEER
# )
# PILImage.open(BytesIO(png_bytes)).show()