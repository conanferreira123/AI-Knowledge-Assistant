from langchain_core.prompts import ChatPromptTemplate
from langchain_mistralai import ChatMistralAI
from dotenv import load_dotenv
import os

load_dotenv()

# ----------------------------------------------------------------------
# Small, deterministic model for query rewriting.
# Temperature 0 keeps rewrites stable and reproducible.
# ----------------------------------------------------------------------
llm = ChatMistralAI(
    model="mistral-small-latest",
    api_key=os.getenv("MISTRAL_API_KEY"),
    temperature=0.7,
)

PROMPT = ChatPromptTemplate.from_template(
    '''
You are a search query rewriter for a conversational RAG system.

Conversation history:
{history}

Current user query:
{query}

Rewrite the current query into a concise standalone search query.

Rules:
- Use the conversation history to resolve references such as "it", "they", "this", "that", and follow-up requests like "explain in detail".
- Remove conversational filler.
- Preserve the original meaning.
- Expand abbreviations when obvious.
- Return ONLY the rewritten standalone query.
- If the current query is already standalone, return it with minimal changes.

Standalone query:
'''
)


def rewrite_query(query: str, history: str | None = None) -> str:
    """
    Rewrite a conversational query into a standalone retrieval query.

    Parameters
    ----------
    query:
        Current user message.
    history:
        Recent conversation history. Can be None for new chats.

    Returns
    -------
    str
        Standalone retrieval query.
    """

    # ------------------------------------------------------------------
    # Important:
    # New conversations may have no history. Convert None to an empty
    # string so the prompt remains valid and does not contain the text
    # "None".
    # ------------------------------------------------------------------
    history = history or ''

    chain = PROMPT | llm

    response = chain.invoke(
        {
            'query': query,
            'history': history,
        }
    )

    return response.content.strip()


if __name__ == '__main__':
    history = 'User: Explain the transformer architecture.'
    q = 'Explain in detail please'

    print(rewrite_query(q, history))

    print(rewrite_query('What is IPv6?'))