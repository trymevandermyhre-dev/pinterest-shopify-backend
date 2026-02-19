from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime, timedelta
import os

from openai import OpenAI

# ---------------- APP ----------------

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ---------------- MODELL ----------------

class RunRequest(BaseModel):
    days_between_posts: int  # 1–10
    posts_per_day: int       # 1–10


# ---------------- ENDPOINTS ----------------

@app.get("/")
def root():
    return {"status": "shopify pinterest backend ready"}


@app.post("/run")
def run(data: RunRequest):

    if not (1 <= data.days_between_posts <= 10):
        return {"error": "days_between_posts must be between 1 and 10"}

    if not (1 <= data.posts_per_day <= 10):
        return {"error": "posts_per_day must be between 1 and 10"}

    today = datetime.today()
    pin_plan = []
    pin_number = 1

    for day in range(5):
        base_date = today + timedelta(days=day * data.days_between_posts)

        for _ in range(data.posts_per_day):
            pin_plan.append({
                "pin_number": pin_number,
                "scheduled_date": base_date.strftime("%Y-%m-%d"),
                "status": "planned"
            })
            pin_number += 1

    return {
        "days_between_posts": data.days_between_posts,
        "posts_per_day": data.posts_per_day,
        "total_pins_planned": len(pin_plan),
        "pins": pin_plan
    }


@app.post("/ai-test")
def ai_test():
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "You are a professional Pinterest SEO copywriter."
            },
            {
                "role": "user",
                "content": "Write one Pinterest title and a short description for a hoodie."
            }
        ]
    )

    return {
        "output": response.choices[0].message.content
    }
