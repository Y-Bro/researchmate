from common.errors import ConfigError
from rag.llm_client import LLMClient
from common.config import load_settings


def main():
    print("Hello, World!")

    try:
        settings = load_settings()
        llm_client = LLMClient(settings)

        response = llm_client.generate("Top 5 best songs similar to sign of the times by harry styles")

        print(response)

    except Exception as e:
        pass

if __name__ == "__main__":
    main()