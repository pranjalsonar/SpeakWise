import random

from app.enums.practice_session import SessionMode
from app.schemas.topic import TopicResponse


RANDOM_TOPICS = [
    {
        "title": "Should AI replace teachers?",
        "category": "Technology",
        "difficulty": "Medium",
    },
    {
        "title": "The impact of social media on society",
        "category": "Social Issues",
        "difficulty": "Easy",
    },
    {
        "title": "Is remote work the future?",
        "category": "Business",
        "difficulty": "Easy",
    },
    {
        "title": "Climate change and individual responsibility",
        "category": "Environment",
        "difficulty": "Medium",
    },
    {
        "title": "The future of electric vehicles",
        "category": "Technology",
        "difficulty": "Medium",
    },
    {
        "title": "Should college education be free?",
        "category": "Education",
        "difficulty": "Hard",
    },
    {
        "title": "Can technology improve mental health?",
        "category": "Healthcare",
        "difficulty": "Hard",
    },
    {
        "title": "The importance of financial literacy",
        "category": "Finance",
        "difficulty": "Medium",
    },
    {
        "title": "Space exploration: Worth the investment?",
        "category": "Science",
        "difficulty": "Hard",
    },
    {
        "title": "Should governments regulate artificial intelligence?",
        "category": "Technology",
        "difficulty": "Hard",
    },
]

DAILY_TOPICS = [
    {
        "title": "Describe a challenge you overcame.",
        "category": "Personal Experience",
        "difficulty": "Easy",
    },
    {
        "title": "Talk about your biggest achievement.",
        "category": "Personal Experience",
        "difficulty": "Easy",
    },
    {
        "title": "Explain your dream career.",
        "category": "Career",
        "difficulty": "Medium",
    },
    {
        "title": "Describe a memorable journey.",
        "category": "Travel",
        "difficulty": "Easy",
    },
    {
        "title": "Speak about your favorite book.",
        "category": "Literature",
        "difficulty": "Medium",
    },
]



class TopicService:

    @staticmethod
    def get_topic(
        mode: SessionMode,
        custom_topic: str | None = None,
    ) -> TopicResponse:

        if mode == SessionMode.CUSTOM:

            if not custom_topic:
                raise ValueError("Custom topic is required.")

            return TopicResponse(
                title=custom_topic,
                category="Custom",
                difficulty="User Defined",
            )

        if mode == SessionMode.RANDOM:
            topic = random.choice(RANDOM_TOPICS)
            return TopicResponse(**topic)

        if mode == SessionMode.DAILY:
            topic = random.choice(DAILY_TOPICS)
            return TopicResponse(**topic)

        raise ValueError("Invalid session mode.")