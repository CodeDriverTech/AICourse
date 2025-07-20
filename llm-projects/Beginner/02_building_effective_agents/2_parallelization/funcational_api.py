"""
通过并行化，LLM 可以同时执行一项任务：

LLM 有时可以同时处理一项任务，并以编程方式聚合其输出。这种工作流程，即并行化，体现在两个关键方面：分段：将任务分解为并行运行的独立子任务。投票：多次运行同一任务以获得不同的输出。
何时使用此工作流程：当拆分后的子任务可以并行化以提高速度，或者需要多个视角或尝试以获得更高置信度的结果时，并行化非常有效。对于涉及多个考量的复杂任务，当每个考量都由单独的 LLM 调用处理时，LLM 通常表现更好，从而能够专注于每个特定方面。
"""
from dotenv import load_dotenv
import os

load_dotenv()
base_url = os.getenv("OPENAI_BASE_URL")
api_key = os.getenv("OPENAI_API_KEY")

from langchain.chat_models import init_chat_model

llm = init_chat_model(
    "openai:gpt-4.1-nano-2025-04-14",
    # configurable_fields="any",
    # config_prefix="foo",
    temperature=1.0,
    base_url=base_url,
    api_key=api_key
)

from langgraph.func import entrypoint, task

@task
def call_llm_1(topic: str):
    """First LLM call to generate initial joke"""

    msg = llm.invoke(f"Write a joke about {topic}")
    return msg.content

@task
def call_llm_2(topic: str):
    """Second LLM call to generate story"""

    msg = llm.invoke(f"Write a story about {topic}")
    return msg.content

@task
def call_llm_3(topic: str):
    """Third LLM call to generate poem"""

    msg = llm.invoke(f"Write a poem about {topic}")
    return msg.content

@task
def aggregator(topic: str, joke: str, story: str, poem: str):
    """Combine the joke and story into a single output"""

    combined = f"Here's a story, joke, and poem about {topic}!\n\n"
    combined += f"STORY:\n{story}\n\n"
    combined += f"JOKE:\n{joke}\n\n"
    combined += f"POEM:\n{poem}"
    return combined

# Build workflow
@entrypoint()
def parallel_workflow(topic: str):
    joke_fut = call_llm_1(topic)
    story_fut = call_llm_2(topic)
    poem_fut = call_llm_3(topic)
    return aggregator(
        topic, joke_fut.result(), story_fut.result(), poem_fut.result()
    ).result()

# Invoke
for step in parallel_workflow.stream("cats", stream_mode="updates"):
    print(step)
    print("\n--- --- ---\n")
# Output:
"""
{'call_llm_3': 'In moonlit glow and morning rays,  \nA whisper soft, a gentle gaze,  \nThe velvet paws, so sleek, so sly,  \nA creature’s grace beneath the sky.  \n  \nEyes like lanterns, emerald, gold,  \nMysteries in stories told,  \nSilent hunters, fierce and sweet,  \nWith every step, a dance complete.  \n  \nWhiskers twitch and tails unfurl,  \nA magic touch, a secret world,  \nCurled in patches, warm and snug,  \nA little universe, eyes so snug.  \n  \nFeline whispers in the night,  \nA purrsong in a lullaby light,  \nCompanions, enigmas, friends so near,  \nCats bring joy, year to year.'}

--- --- ---

{'call_llm_1': 'Why did the cat sit on the computer?  \nBecause it wanted to keep an eye on the mouse!'}

--- --- ---

{'call_llm_2': 'Once upon a time in a quiet little town, there was a curious gray cat named Luna. Luna loved exploring every corner of her neighborhood, from the bustling marketplace to the silent, moonlit alleyways. She was known among the other cats for her adventurous spirit and bright, shining eyes.\n\nOne day, while wandering near the old wizard’s cottage at the edge of town, Luna stumbled upon a shimmering feather lying in the grass. Intrigued, she gently pawed at it, and suddenly, the feather burst into a swirl of glowing light. Before she knew it, Luna found herself in a magical world filled with talking animals, floating islands, and enchanted forests.\n\nIn this new realm, cats were revered as wise guardians of ancient secrets. Luna met a regal feline named Sir Whiskers, who wore a tiny golden crown and carried a scroll filled with stories of bravery and wisdom. Sir Whiskers explained that their land was protected by a powerful crystal that kept balance and harmony.\n\nHowever, the crystal had lost its glow, and darkness was creeping into their world. Luna, with her curious nature and brave heart, volunteered to help. Guided by the wise old owl and the playful foxes, she embarked on a quest to find the missing shard of the crystal, hidden deep inside a mysterious cave guarded by a friendly but mischievous fire spirit.\n\nWith cleverness and courage, Luna outsmarted the fire spirit, retrieving the shard and restoring the crystal’s glow. The magical world shimmered brighter than ever, and Luna was celebrated as a hero. Before returning home, Sir Whiskers gave her a small token—a tiny, glowing pawprint—that would ensure she would always carry the magic within her.\n\nBack in her town, Luna continued her adventures, always curious, always brave, and forever loved by her fellow cats. And sometimes, on clear nights, she gazed at the moon and remembered her extraordinary journey into a world where cats were legends.\n\nAnd so, in the quiet town of her origin, Luna’s story became a favorite tale whispered among the neighborhood cats—a reminder that curiosity, courage, and a kind heart can lead to the most wonderful adventures.'}

--- --- ---

{'aggregator': "Here's a story, joke, and poem about cats!\n\nSTORY:\nOnce upon a time in a quiet little town, there was a curious gray cat named Luna. Luna loved exploring every corner of her neighborhood, from the bustling marketplace to the silent, moonlit alleyways. She was known among the other cats for her adventurous spirit and bright, shining eyes.\n\nOne day, while wandering near the old wizard’s cottage at the edge of town, Luna stumbled upon a shimmering feather lying in the grass. Intrigued, she gently pawed at it, and suddenly, the feather burst into a swirl of glowing light. Before she knew it, Luna found herself in a magical world filled with talking animals, floating islands, and enchanted forests.\n\nIn this new realm, cats were revered as wise guardians of ancient secrets. Luna met a regal feline named Sir Whiskers, who wore a tiny golden crown and carried a scroll filled with stories of bravery and wisdom. Sir Whiskers explained that their land was protected by a powerful crystal that kept balance and harmony.\n\nHowever, the crystal had lost its glow, and darkness was creeping into their world. Luna, with her curious nature and brave heart, volunteered to help. Guided by the wise old owl and the playful foxes, she embarked on a quest to find the missing shard of the crystal, hidden deep inside a mysterious cave guarded by a friendly but mischievous fire spirit.\n\nWith cleverness and courage, Luna outsmarted the fire spirit, retrieving the shard and restoring the crystal’s glow. The magical world shimmered brighter than ever, and Luna was celebrated as a hero. Before returning home, Sir Whiskers gave her a small token—a tiny, glowing pawprint—that would ensure she would always carry the magic within her.\n\nBack in her town, Luna continued her adventures, always curious, always brave, and forever loved by her fellow cats. And sometimes, on clear nights, she gazed at the moon and remembered her extraordinary journey into a world where cats were legends.\n\nAnd so, in the quiet town of her origin, Luna’s story became a favorite tale whispered among the neighborhood cats—a reminder that curiosity, courage, and a kind heart can lead to the most wonderful adventures.\n\nJOKE:\nWhy did the cat sit on the computer?  \nBecause it wanted to keep an eye on the mouse!\n\nPOEM:\nIn moonlit glow and morning rays,  \nA whisper soft, a gentle gaze,  \nThe velvet paws, so sleek, so sly,  \nA creature’s grace beneath the sky.  \n  \nEyes like lanterns, emerald, gold,  \nMysteries in stories told,  \nSilent hunters, fierce and sweet,  \nWith every step, a dance complete.  \n  \nWhiskers twitch and tails unfurl,  \nA magic touch, a secret world,  \nCurled in patches, warm and snug,  \nA little universe, eyes so snug.  \n  \nFeline whispers in the night,  \nA purrsong in a lullaby light,  \nCompanions, enigmas, friends so near,  \nCats bring joy, year to year."}

--- --- ---

{'parallel_workflow': "Here's a story, joke, and poem about cats!\n\nSTORY:\nOnce upon a time in a quiet little town, there was a curious gray cat named Luna. Luna loved exploring every corner of her neighborhood, from the bustling marketplace to the silent, moonlit alleyways. She was known among the other cats for her adventurous spirit and bright, shining eyes.\n\nOne day, while wandering near the old wizard’s cottage at the edge of town, Luna stumbled upon a shimmering feather lying in the grass. Intrigued, she gently pawed at it, and suddenly, the feather burst into a swirl of glowing light. Before she knew it, Luna found herself in a magical world filled with talking animals, floating islands, and enchanted forests.\n\nIn this new realm, cats were revered as wise guardians of ancient secrets. Luna met a regal feline named Sir Whiskers, who wore a tiny golden crown and carried a scroll filled with stories of bravery and wisdom. Sir Whiskers explained that their land was protected by a powerful crystal that kept balance and harmony.\n\nHowever, the crystal had lost its glow, and darkness was creeping into their world. Luna, with her curious nature and brave heart, volunteered to help. Guided by the wise old owl and the playful foxes, she embarked on a quest to find the missing shard of the crystal, hidden deep inside a mysterious cave guarded by a friendly but mischievous fire spirit.\n\nWith cleverness and courage, Luna outsmarted the fire spirit, retrieving the shard and restoring the crystal’s glow. The magical world shimmered brighter than ever, and Luna was celebrated as a hero. Before returning home, Sir Whiskers gave her a small token—a tiny, glowing pawprint—that would ensure she would always carry the magic within her.\n\nBack in her town, Luna continued her adventures, always curious, always brave, and forever loved by her fellow cats. And sometimes, on clear nights, she gazed at the moon and remembered her extraordinary journey into a world where cats were legends.\n\nAnd so, in the quiet town of her origin, Luna’s story became a favorite tale whispered among the neighborhood cats—a reminder that curiosity, courage, and a kind heart can lead to the most wonderful adventures.\n\nJOKE:\nWhy did the cat sit on the computer?  \nBecause it wanted to keep an eye on the mouse!\n\nPOEM:\nIn moonlit glow and morning rays,  \nA whisper soft, a gentle gaze,  \nThe velvet paws, so sleek, so sly,  \nA creature’s grace beneath the sky.  \n  \nEyes like lanterns, emerald, gold,  \nMysteries in stories told,  \nSilent hunters, fierce and sweet,  \nWith every step, a dance complete.  \n  \nWhiskers twitch and tails unfurl,  \nA magic touch, a secret world,  \nCurled in patches, warm and snug,  \nA little universe, eyes so snug.  \n  \nFeline whispers in the night,  \nA purrsong in a lullaby light,  \nCompanions, enigmas, friends so near,  \nCats bring joy, year to year."}

--- --- ---

"""