import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "adaptive_engine")

QUESTIONS = [
    # ── Algebra (difficulties: 0.1 → 0.9) ───────────────────────────────────
    {
        "text": "If x + 5 = 12, what is x?",
        "options": ["A) 5", "B) 6", "C) 7", "D) 8"],
        "correct_answer": "C",
        "difficulty": 0.1,
        "topic": "Algebra",
        "tags": ["linear equations", "beginner"],
    },
    {
        "text": "Solve for x: 3x - 7 = 14",
        "options": ["A) 5", "B) 7", "C) 9", "D) 3"],
        "correct_answer": "B",
        "difficulty": 0.2,
        "topic": "Algebra",
        "tags": ["linear equations"],
    },
    {
        "text": "If f(x) = 2x² - 3x + 1, what is f(3)?",
        "options": ["A) 10", "B) 12", "C) 16", "D) 9"],
        "correct_answer": "A",
        "difficulty": 0.4,
        "topic": "Algebra",
        "tags": ["functions", "quadratics"],
    },
    {
        "text": "What are the roots of x² - 5x + 6 = 0?",
        "options": ["A) 1 and 6", "B) 2 and 3", "C) -2 and -3", "D) 3 and 4"],
        "correct_answer": "B",
        "difficulty": 0.5,
        "topic": "Algebra",
        "tags": ["quadratics", "factoring"],
    },
    {
        "text": "If log₂(x) = 5, what is x?",
        "options": ["A) 10", "B) 25", "C) 32", "D) 64"],
        "correct_answer": "C",
        "difficulty": 0.7,
        "topic": "Algebra",
        "tags": ["logarithms"],
    },
    {
        "text": "The sum of an infinite geometric series is 16 and its first term is 4. What is the common ratio?",
        "options": ["A) 0.5", "B) 0.25", "C) 0.75", "D) 0.6"],
        "correct_answer": "C",
        "difficulty": 0.9,
        "topic": "Algebra",
        "tags": ["series", "geometric"],
    },

    # ── Vocabulary (difficulties: 0.2 → 0.95) ────────────────────────────────
    {
        "text": "BENEVOLENT most nearly means:",
        "options": ["A) Hostile", "B) Charitable", "C) Indifferent", "D) Arrogant"],
        "correct_answer": "B",
        "difficulty": 0.2,
        "topic": "Vocabulary",
        "tags": ["GRE words", "adjectives"],
    },
    {
        "text": "EPHEMERAL most nearly means:",
        "options": ["A) Permanent", "B) Ancient", "C) Short-lived", "D) Invisible"],
        "correct_answer": "C",
        "difficulty": 0.4,
        "topic": "Vocabulary",
        "tags": ["GRE words"],
    },
    {
        "text": "OBSEQUIOUS most nearly means:",
        "options": ["A) Defiant", "B) Excessively compliant", "C) Forgetful", "D) Generous"],
        "correct_answer": "B",
        "difficulty": 0.65,
        "topic": "Vocabulary",
        "tags": ["GRE words", "advanced"],
    },
    {
        "text": "PELLUCID most nearly means:",
        "options": ["A) Cloudy", "B) Translucent and clear", "C) Turbulent", "D) Verbose"],
        "correct_answer": "B",
        "difficulty": 0.85,
        "topic": "Vocabulary",
        "tags": ["GRE words", "advanced"],
    },
    {
        "text": "TENDENTIOUS most nearly means:",
        "options": ["A) Unbiased", "B) Gentle", "C) Promoting a cause", "D) Fragile"],
        "correct_answer": "C",
        "difficulty": 0.95,
        "topic": "Vocabulary",
        "tags": ["GRE words", "advanced"],
    },

    # ── Geometry (difficulties: 0.15 → 0.8) ──────────────────────────────────
    {
        "text": "What is the area of a triangle with base 8 and height 5?",
        "options": ["A) 20", "B) 40", "C) 13", "D) 80"],
        "correct_answer": "A",
        "difficulty": 0.15,
        "topic": "Geometry",
        "tags": ["area", "triangle"],
    },
    {
        "text": "A circle has a radius of 7. What is its circumference? (Use π ≈ 3.14)",
        "options": ["A) 21.98", "B) 43.96", "C) 153.86", "D) 14"],
        "correct_answer": "B",
        "difficulty": 0.3,
        "topic": "Geometry",
        "tags": ["circle", "circumference"],
    },
    {
        "text": "In a right triangle, the two legs are 6 and 8. What is the hypotenuse?",
        "options": ["A) 10", "B) 12", "C) 14", "D) 9"],
        "correct_answer": "A",
        "difficulty": 0.35,
        "topic": "Geometry",
        "tags": ["Pythagorean theorem"],
    },
    {
        "text": "What is the volume of a cylinder with radius 3 and height 10? (Use π ≈ 3.14)",
        "options": ["A) 94.2", "B) 282.6", "C) 188.4", "D) 942"],
        "correct_answer": "B",
        "difficulty": 0.55,
        "topic": "Geometry",
        "tags": ["3D shapes", "volume"],
    },
    {
        "text": "A square is inscribed in a circle of radius r. What is the area of the square in terms of r?",
        "options": ["A) r²", "B) 2r²", "C) 4r²", "D) πr²"],
        "correct_answer": "B",
        "difficulty": 0.8,
        "topic": "Geometry",
        "tags": ["inscribed shapes", "advanced"],
    },

    # ── Data Analysis (difficulties: 0.25 → 0.85) ────────────────────────────
    {
        "text": "The mean of 5 numbers is 12. If four of them are 8, 10, 14, 16, what is the fifth?",
        "options": ["A) 10", "B) 12", "C) 14", "D) 18"],
        "correct_answer": "B",
        "difficulty": 0.25,
        "topic": "Data Analysis",
        "tags": ["mean", "statistics"],
    },
    {
        "text": "In a dataset {3, 7, 7, 9, 11, 13}, what is the median?",
        "options": ["A) 7", "B) 8", "C) 9", "D) 10"],
        "correct_answer": "B",
        "difficulty": 0.45,
        "topic": "Data Analysis",
        "tags": ["median"],
    },
    {
        "text": "A bag has 4 red, 3 blue, and 5 green marbles. What is the probability of picking a blue marble?",
        "options": ["A) 1/4", "B) 1/3", "C) 1/5", "D) 3/12"],
        "correct_answer": "A",
        "difficulty": 0.6,
        "topic": "Data Analysis",
        "tags": ["probability"],
    },
    {
        "text": "The standard deviation of {2, 4, 4, 4, 5, 5, 7, 9} is approximately:",
        "options": ["A) 2", "B) 4", "C) 1.5", "D) 3"],
        "correct_answer": "A",
        "difficulty": 0.85,
        "topic": "Data Analysis",
        "tags": ["standard deviation", "advanced"],
    },
]


async def seed():
    client = AsyncIOMotorClient(MONGO_URI)
    db = client[DB_NAME]

    collection = db["questions"]

    # Drop existing questions to avoid duplicates on re-run
    await collection.drop()
    result = await collection.insert_many(QUESTIONS)
    print(f"✅ Seeded {len(result.inserted_ids)} questions into '{DB_NAME}.questions'")

    # Create index on difficulty for fast adaptive queries
    await collection.create_index([("difficulty", 1)])
    await collection.create_index([("topic", 1)])
    print("✅ Indexes created on difficulty and topic")

    client.close()


if __name__ == "__main__":
    asyncio.run(seed())
