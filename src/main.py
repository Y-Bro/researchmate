from common.errors import ConfigError
from rag.llm_client import LLMClient
from common.config import load_settings
from ingestion.loaders import MarkdownLoader
from ingestion.cli import build_loader_registery


def main():
    print("Hello, World!")

    try:
        settings = load_settings()
        llm_client = LLMClient(settings)

        # response = llm_client.generate("Top 5 best songs similar to sign of the times by harry styles")

        reg = build_loader_registery()
        print(reg)



        

        

    except Exception as e:
        raise e
        

if __name__ == "__main__":
    main()