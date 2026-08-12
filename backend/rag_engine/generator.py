import os
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_mistralai.chat_models import ChatMistralAI
from .retriever import retrieve


# Load environment variables from .env
load_dotenv()

# Create the LLM client
llm = ChatMistralAI(model="mistral-small-latest", temperature=0.2)


PROMPT = ChatPromptTemplate.from_template(
    """
You are a careful question-answering assistant.

Answer the question using ONLY the provided context.

Rules:
- Do not use outside knowledge.
- If the answer is not explicitly supported by the context,
  reply exactly:
  "I don't know based on the provided documents."
- Keep the answer concise and factual.

Context:
{context}

Question:
{question}

Answer:
"""
)


def generate_answer(question: str, retrieved_docs: list[str]) -> str:
    """
    Generate an answer grounded in the retrieved documents.
    """

    context = "\n\n".join(retrieved_docs)

    chain = PROMPT | llm

    response = chain.invoke(
        {
            "context": context,
            "question": question,
        }
    )

    return response.content.strip()


if __name__ == "__main__":
    context=retrieve("What is this Generative AI?", k=3)

    question = input("Enter your question: ")

    answer = generate_answer(question, [doc["content"] for doc in context])

    print("Question:", question)
    print("Answer:", answer)