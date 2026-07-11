from database import get_messages

def prepare_messages():
    saved_messages = get_messages()
    print(saved_messages)
    converted_list = []
    system_prompt = {"role": "system", "content": "You are a helpful, professional assistant. Rely on the conversation history if you need to, when it's relevant."}
    converted_list.append(system_prompt)
    for msg in saved_messages:
        role=msg[1]
        content=msg[2]
        converted_dict={"role": role, "content": content}
        converted_list.append(converted_dict)
    return converted_list   