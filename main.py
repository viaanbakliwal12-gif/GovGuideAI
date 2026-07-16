from dotenv import load_dotenv

load_dotenv()
import os

from app.server import create_app


app = create_app()


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", "5000")),
        debug=False,
    )
