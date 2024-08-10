import pickle
from langchain_chroma import Chroma
from langchain.agents import AgentType
from langchain.chat_models import ChatOpenAI
from langchain_core.stores import InMemoryByteStore
from langchain.retrievers.multi_vector import MultiVectorRetriever
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents import Tool, AgentExecutor, create_openai_tools_agent
from langchain_core.prompts import PromptTemplate
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder, HumanMessagePromptTemplate, SystemMessagePromptTemplate


def dump_pickle_file(retriever, filename: str):
    """
    Serialize and save the given data to a file using Pickle.
    Args:
        data: The data to be pickled.
        filename (str): The name of the file where the pickled data will be saved.
    Returns:
    A pickle file with object saved in it
    """
    with open(filename, 'wb') as handle:
        pickle.dump(retriever, handle, protocol=pickle.HIGHEST_PROTOCOL)


def load_pickle_file(filename: str):
    """
    De-Serialize file using Pickle.
    Args:
        filename (str): The name of the file where the pickled data will be saved.
    Returns:
    Pickle Object
    """
    
    with open(filename, "rb") as input_file:
        pickle_object = pickle.load(input_file)
    return pickle_object



def create_MVR(filename, _embeddings, persist_directory_name, vectorstore_exists=True, k=7):
    docs_path = "/content/drive/MyDrive/AgenticAI_Repo/docs/"
    vector_store_path = "/content/drive/MyDrive/AgenticAI_Repo/vector_store/vector_store/"
    file_docs = load_pickle_file(docs_path + filename)
    docs = file_docs['parent_docs']
    doc_ids = file_docs['doc_ids']
    id_key = 'doc_id'
    
    if vectorstore_exists:
        vectorstore = Chroma(persist_directory=vector_store_path + persist_directory_name, embedding_function=_embeddings)
    else:
        vectorstore = Chroma.from_documents(docs, _embeddings, persist_directory=vector_store_path + persist_directory_name)

    # The storage layer for the parent documents
    store = InMemoryByteStore()

    retriever = MultiVectorRetriever(
        vectorstore=vectorstore,
        byte_store=store,
        id_key=id_key, search_kwargs={"k": k})

    retriever.docstore.mset(list(zip(doc_ids, docs)))
    return retriever


def create_chat_agent(llm: ChatOpenAI, tools: list, system_prompt: str, verbose=False):
    """Helper function for creating agent executor"""
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder(variable_name="conversation_history", optional=True),
        HumanMessagePromptTemplate(prompt=PromptTemplate(input_variables=['input'], template='{input}')),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])
    agent = create_openai_tools_agent(llm, tools, prompt)
    executor = AgentExecutor(agent=agent, tools=tools, verbose=verbose)
    return executor


def create_qa_agent(llm: ChatOpenAI, tools: list, system_prompt: str, verbose=False):
    """Helper function for creating agent executor"""
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        HumanMessagePromptTemplate(prompt=PromptTemplate(input_variables=['input'], template='{input}')),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])
    agent = create_openai_tools_agent(llm, tools, prompt)
    executor = AgentExecutor(agent=agent, tools=tools, verbose=verbose)
    return executor
