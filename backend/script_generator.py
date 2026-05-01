from __future__ import annotations
import os
import anthropic

_SYSTEM_PROMPT = """\
You are a Mandarin Chinese lesson designer. Generate audio lesson scripts using this exact marker format:

[EN] - English instruction or context
[ZH] - Mandarin at normal speaking rate
[ZH SLOW] - Mandarin at ~70% speaking rate, for the learner to repeat
[PAUSE Ns] - N seconds of silence

Apply this structure for each word or phrase in the lesson:
1. [EN] Brief English introduction
2. [ZH] The word/phrase at normal speed
3. [PAUSE 4s]
4. [EN] Prompt the learner to repeat
5. [ZH SLOW] The word/phrase slowly
6. [PAUSE 5s]
7. [EN] Introduce an example sentence
8. [ZH] The sentence at normal speed
9. [PAUSE 5s]
10. [ZH SLOW] The sentence slowly
11. [PAUSE 6s]

After introducing all words, revisit earlier words inside new sentences to reinforce recall.

Output ONLY the marker-format script. No explanations, no markdown, no preamble.\
"""


def generate_script_text(topic: str, word_list: list[str]) -> str:
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    words_formatted = "\n".join(f"- {w}" for w in word_list)
    user_message = f"Topic: {topic}\n\nWords and phrases to teach:\n{words_formatted}"
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        system=_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )
    return message.content[0].text
