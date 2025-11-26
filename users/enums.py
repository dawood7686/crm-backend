from enum import Enum

class AIModelPlatformChoices(Enum):
    OPENAI = "OPENAI"
    OLLAMA = 'OLLAMA'
    GEMINI = 'GEMINI'

    @classmethod
    def choices(cls):
        return [(choice.value, choice.name) for choice in cls]

class AIModelSelection(Enum):
    OPENAI_GPT_4o_MINI= 'gpt-4o-mini'
    OLLAMA_LLAMA3 = 'llama3'
    GEMINI_PRO = 'gemini-pro'

    @classmethod
    def choices(cls):
        return [(choice.value, choice.name) for choice in cls]