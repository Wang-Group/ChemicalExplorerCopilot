from llmlab.constant import open_ai_api_key
import openai
import json

openai.api_key = open_ai_api_key


def get_completion(to_send, NL, model, CHAT_HISTORY, message_only=False):
    messages = [
        {
            "role": "system",
            "content": f"ULE stands for 'Unified Language of Experimentation'. You are an expert in robotic chemistry and in translating natural language into ULE. Your task is to generate ULE and correct any incorrect ULE, and ensure you only use items listed in the ULE description file: \n {to_send}",
        },
        {
            "role": "user",
            "content": f"""Convert "{NL}" to proper ULE, a robot-executable JSON file""",
        },
    ]
    # no update for the chat hisotry 
    if message_only:
        return messages
    # update the chat history 
    for message in messages:
        CHAT_HISTORY.append(message)

    response = openai.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0,
        top_p=1,
        response_format={"type": "json_object"},
    )
    CHAT_HISTORY.append(
        {"role": "assistant", "content": response.choices[0].message.content}
    )

    return response.choices[0].message.content


def iter_completion(iterative_to_send, NL, model, CHAT_HISTORY, message_only=False):
    messages = [
        {
            "role": "system",
            "content": f"ULE stands for 'Unified Language of Experimentation'. You are an expert in robotic chemistry and in translating natural language into ULE. Your task is to generate ULE and correct any incorrect ULE, and ensure you only use items listed in the ULE description file: \n {iterative_to_send}",
        },
        {
            "role": "user",
            "content": f"""Convert "{NL}" to proper ULE, a robot-executable JSON file""",
        },
    ]
    if message_only:
        return messages
    for message in messages:
        CHAT_HISTORY.append(message)

    response = openai.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0,
        top_p=1,
        response_format={"type": "json_object"},
    )
    CHAT_HISTORY.append(
        {"role": "assistant", "content": response.choices[0].message.content}
    )

    return response.choices[0].message.content


def find_corresponding_text(matching_to_send, model):
    response = openai.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": "You are a natural language processing expert.",
            },
            {"role": "user", "content": matching_to_send},
        ],
        temperature=0,
        top_p=1,
    )
    return response.choices[0].message.content
