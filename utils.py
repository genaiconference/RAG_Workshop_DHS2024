from langchain.chains import ConversationalRetrievalChain
from IPython.display import Markdown
from langchain.memory import ConversationBufferMemory
from typing import Dict, Any
from langchain.prompts import ChatPromptTemplate

class CustomConversationBufferMemory(ConversationBufferMemory):
    def save_context(self, inputs: Dict[str, Any], outputs: Dict[str, str]) -> None:
        return super(CustomConversationBufferMemory, self).save_context(inputs,{'response': outputs['answer']})

# define memory object
memory = CustomConversationBufferMemory(memory_key="chat_history", return_messages=True)

template = """You are an assistant for question-answering tasks. 
Use the following pieces of retrieved context to answer the question. 
Keep the answer straight to the point.
Avoid using generic phrases like "Provide context" or "as per context.
Question: {question} 
Context: {context} 
Answer:
"""
RAG_prompt = ChatPromptTemplate.from_template(template)

def pretty_print_result(query, _llm, retriever):
    """
    Custom function to print clean output
    """
    chain = ConversationalRetrievalChain.from_llm(llm=_llm, 
                                           combine_docs_chain_kwargs={"prompt": RAG_prompt}, 
                                          retriever=retriever, 
                                           memory=memory, 
                                           return_source_documents=True)
    try:
        result = chain({"question": query})
        print("Answer: " + result["answer"])
        print("=============================================================================================================")

    except Exception as e:
        print(e)
        pass
    print("No of documents retrieved" + str(len(result['source_documents'])))
    print(f"\n{'-' * 100}\n".join([f"Document {i+1}:\n\n" + d.page_content +"\n\n" + str(d.metadata) for i, d in enumerate(result['source_documents'])]))
    return


def get_answer(query, _llm, retriever):
    """
    given query, llm, prompt, return answwer and relevant source documents
    
    """
    
    chain = ConversationalRetrievalChain.from_llm(llm=_llm, 
                                           combine_docs_chain_kwargs={"prompt": RAG_prompt}, 
                                          retriever=retriever, 
                                           memory=memory, 
                                           return_source_documents=True)
    try:
        result = chain({"question": query})
    except:
        pass
    
    return result['answer'], result['source_documents']


# Helper function for printing docs
def pretty_print_docs(docs):
    print(
        f"\n{'-' * 100}\n".join(
            [f"Document {i+1}:\n\n" + d.page_content + "\n\n" + str(d.metadata) for i, d in enumerate(docs)]
        )
    )

import chromadb

from langchain.text_splitter import RecursiveCharacterTextSplitter, SentenceTransformersTokenTextSplitter
import numpy as np
from pypdf import PdfReader
from tqdm import tqdm


def _read_pdf(filename):
    reader = PdfReader(filename)
    
    pdf_texts = [p.extract_text().strip() for p in reader.pages]

    # Filter the empty strings
    pdf_texts = [text for text in pdf_texts if text]
    return pdf_texts


def _chunk_texts(texts):
    character_splitter = RecursiveCharacterTextSplitter(
        separators=["\n\n", "\n", ". ", " ", ""],
        chunk_size=1000,
        chunk_overlap=0
    )
    character_split_texts = character_splitter.split_text('\n\n'.join(texts))

    token_splitter = SentenceTransformersTokenTextSplitter(chunk_overlap=0, tokens_per_chunk=256)

    token_split_texts = []
    for text in character_split_texts:
        token_split_texts += token_splitter.split_text(text)

    return token_split_texts


def load_chroma(filename, collection_name, embedding_function):
    texts = _read_pdf(filename)
    chunks = _chunk_texts(texts)

    chroma_cliet = chromadb.Client()
    chroma_collection = chroma_cliet.create_collection(name=collection_name, embedding_function=embedding_function)

    ids = [str(i) for i in range(len(chunks))]

    chroma_collection.add(ids=ids, documents=chunks)

    return chroma_collection

def word_wrap(string, n_chars=72):
    # Wrap a string at the next space after n_chars
    if len(string) < n_chars:
        return string
    else:
        return string[:n_chars].rsplit(' ', 1)[0] + '\n' + word_wrap(string[len(string[:n_chars].rsplit(' ', 1)[0])+1:], n_chars)


   
def project_embeddings(embeddings, umap_transform):
    umap_embeddings = np.empty((len(embeddings),2))
    for i, embedding in enumerate(tqdm(embeddings)): 
        umap_embeddings[i] = umap_transform.transform([embedding])
    return umap_embeddings

from langchain.document_loaders import PyPDFLoader

def load_data(data_path):

  loader1 = PyPDFLoader(file_path=data_path+'/Apple_2022.pdf')
  documents1 = loader1.load()
  loader2 = PyPDFLoader(file_path=data_path+'/Apple_2023.pdf')
  documents2 = loader2.load()



