# from dotenv import load_dotenv, dotenv_values
# from pathlib import Path
# import os

# print("CWD:", os.getcwd())
# # ROOT = Path(__file__).resolve().parents[0]
# # ENV_PATH = ROOT / ".env"
# load_dotenv(ENV_PATH)
# print("GEMINI_API_KEY:", os.getenv("GOOGLE_API_KEY"))
# print("ENV:", "GOOGLE_API_KEY" in os.environ)

# # from dotenv import load_dotenv, dotenv_values
# # from pathlib import Path
# # import os

# # ROOT = Path(__file__).resolve().parents[0]
# # ENV_PATH = ROOT / ".env"

# # print("ROOT:", ROOT)
# # print("ENV PATH:", ENV_PATH)
# # print("ENV PATH EXISTS:", ENV_PATH.exists())
# # print("RAW ENV CONTENT:", dotenv_values(ENV_PATH))

# # load_dotenv(ENV_PATH)

# # print("IN os.environ:", "GOOGLE_API_KEY" in os.environ)
# # print("VALUE:", os.getenv("GOOGLE_API_KEY"))

import google.generativeai as genai

for model in genai.list_models():
    print(
        model.name,
        model.supported_generation_methods
    )



