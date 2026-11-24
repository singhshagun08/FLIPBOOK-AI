
from app import create_app
from app.services.rag_service import get_rag_service

app = create_app()

with app.app_context():

    print("\nFLIPBOOK-AI RAG TEST")
    print("=" * 45)

    try:
        rag = get_rag_service()

        result = rag.generate_answer(
            question="What are outliers and how can they be detected?",
            user_id=1,
            document_ids=[1],
            top_k=5
        )

        print("\nAI ANSWER:")
        print(result["answer"])

        print("\nMODEL:", result["model"])
        print("GROUNDED:", result["grounded"])
        print("RETRIEVED PASSAGES:", result["retrieved_count"])

        print("\nSOURCES:")
        for source in result["sources"]:
            print(source)

        print("\nRAG TEST COMPLETED!")

    except Exception as error:
        print("\nRAG TEST FAILED!")
        print(type(error).__name__, str(error))
