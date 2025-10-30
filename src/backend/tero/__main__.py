import os
import sys

import uvicorn
from uvicorn.config import LOGGING_CONFIG


def _suppress_unnecessary_pydantic_warnings():
    os.environ["PYTHONWARNINGS"] = "ignore::UserWarning:pydantic._internal._generate_schema"


if __name__ == "__main__":
    # This avoids unnecessary warning from transformers library due to missing pytorch and other libraries that are not really necessary.
    os.environ["TRANSFORMERS_VERBOSITY"] = "error"
    _suppress_unnecessary_pydantic_warnings()
    LOGGING_CONFIG["formatters"]["default"]["fmt"] = "%(asctime)s [%(name)s] %(levelprefix)s %(message)s"
    LOGGING_CONFIG["formatters"]["access"]["fmt"] = "%(asctime)s [%(name)s] %(levelprefix)s %(client_addr)s - \"%(request_line)s\" %(status_code)s"
    LOGGING_CONFIG["loggers"]["tero"] = {"handlers": ["default"], "level": "INFO"}
    LOGGING_CONFIG["loggers"]["openai"] = {"handlers": ["default"], "level": "INFO"}
    
    uvicorn.run("tero.api:app", host="0.0.0.0", port=8000, reload=len(sys.argv) > 1)
