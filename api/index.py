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
@app.post("/generate-pin")
def generate_pin(keywords: list[str] | None = None):

    # Fallback til keywords.txt hvis ingen sendes
    if not keywords:
        try:
            with open("keywords.txt", "r") as f:
                keywords = [line.strip() for line in f if line.strip()]
        except FileNotFoundError:
            keywords = []

    prompt = f"""
You are an expert Pinterest SEO copywriter.

TASK:
Generate ONE Pinterest pin based on a fashion product image (image will be added later).

STRICT RULES:
- Language: English
- Platform: Pinterest
- Title: concise, SEO-optimized, purchase intent
- Description:
  - 4–7 sentences
  - Use 15–30 keywords TOTAL
  - Keywords must be embedded naturally in sentences
  - No hashtags
  - No emojis
  - No keyword lists
  - Avoid repeating sentence structure
- Focus on buyer intent, outfit use-cases, and trends
- Do NOT over-optimize or stuff keywords

KEYWORDS TO USE (mix, vary, do not repeat exact structure):
{", ".join(keywords)}

RETURN ONLY valid JSON in this exact structure:
{{
  "title": "...",
  "description": ["...", "..."],
  "keywords_used": ["...", "..."]
}}
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You generate Pinterest SEO content only."},
            {"role": "user", "content": prompt}
        ]
    )

    return response.choices[0].message.content
from fastapi import UploadFile, File

@app.post("/generate-pin-from-image")
async def generate_pin_from_image(
    image: UploadFile = File(...),
    keywords: list[str] | None = None
):

    # Fallback keywords
    if not keywords:
        try:
            with open("keywords.txt", "r") as f:
                keywords = [line.strip() for line in f if line.strip()]
        except FileNotFoundError:
            keywords = []

    image_bytes = await image.read()

    prompt = f"""
You are an expert Pinterest SEO copywriter.

TASK:
Analyze the provided product image.
Identify the garment type and style.
Generate ONE Pinterest pin.

STRICT RULES:
- Language: English
- Platform: Pinterest
- Title: SEO-optimized, purchase intent
- Description:
  - 4–7 sentences
  - Use 15–30 keywords TOTAL
  - Keywords must be embedded naturally
  - No hashtags
  - No emojis
  - No keyword lists
  - Avoid repeating sentence structures
- Keep content highly relevant to what is visible in the image

KEYWORDS TO USE (mix and vary):
{", ".join(keywords)}

RETURN ONLY valid JSON in this structure:
{{
  "garment": "...",
  "style": "...",
  "title": "...",
  "description": ["...", "..."],
  "keywords_used": ["...", "..."]
}}
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_bytes.hex()}"
                        }
                    }
                ]
            }
        ]
    )

    return response.choices[0].message.content

class ImageUrlRequest(BaseModel):
    image_url: str
    keywords: list[str] | None = None


@app.post("/generate-pin-from-image-url")
def generate_pin_from_image_url(data: ImageUrlRequest):

    keywords = data.keywords or []

    prompt = f"""
Analyze the product image and generate one Pinterest pin.

Return valid JSON with:
- title
- 4–7 sentence description
- keywords_used
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": data.image_url}}
                ]
            }
        ]
    )

    return response.choices[0].message.content


