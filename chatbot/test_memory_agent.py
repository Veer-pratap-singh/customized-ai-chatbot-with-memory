from chatbot.agents.memory_agent import MemoryAgent

agent = MemoryAgent()

documents = agent.extract_memories(
    """
    My name is Veer Pratap.
    My favorite language is Python.
    I am a Computer Engineering student.
    """
)

for doc in documents:

    print(doc)