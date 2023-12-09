from docx import Document
from io import BytesIO

from starlette.middleware.cors import CORSMiddleware

from auth import getToken
import requests
from json import loads
from fastapi import FastAPI, UploadFile, File


app = FastAPI(title="Получение предложений действий от ИИ")

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def getModels():
    url = "https://gigachat.devices.sberbank.ru/api/v1/models"
    token = getToken()
    headers = {
        "Authorization": f"Bearer {token}"
    }
    response = requests.get(url, headers=headers, verify=False)
    result = loads(response.text)
    return result


def getAnswer(messages: list[dict], temperature: float = 0.87) -> dict:
    """
    "messages": [
            {
                "role": "user",
                "content": "Когда уже ИИ захватит этот мир?"
            },
            {
                "role": "assistant",
                "content": "Пока что это не является неизбежным событием. Несмотря на то, что искусственный интеллект (ИИ) развивается быстрыми темпами и может выполнять сложные задачи все более эффективно, он по-прежнему ограничен в своих возможностях и не может заменить полностью человека во многих областях. Кроме того, существуют этические и правовые вопросы, связанные с использованием ИИ, которые необходимо учитывать при его разработке и внедрении."
            },
            {
                "role": "user",
                "content": "Думаешь, у нас еще есть шанс?"
            }
        ],

        temperature = number <float> [ 0 .. 2 ]
        По умолчанию: 0.87
        Температура выборки в диапазоне от ноля до двух. Чем выше значение, тем более случайным будет ответ модели.
    """

    url = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {getToken()}"
    }

    data = {
        "model": "GigaChat:latest",
        "messages": messages,
        "temperature": temperature
    }

    response = requests.post(url, headers=headers, json=data, verify=False)
    result = loads(response.text)
    return result


@app.post("/sendMessage")
def get_message(messages: list[dict], temperature: float = 0.87):
    """"
        messages - массив сообщений, минимум одно сообщение должно быть.
        temperature - случайность выбора
    """
    return getAnswer(messages, temperature)


@app.post("/uploadfile/")
async def create_upload_file(file: UploadFile = File(...)):
    contents = await file.read()
    document = Document(BytesIO(contents))
    text = ' '.join([paragraph.text for paragraph in document.paragraphs])
    q_response = getAnswer([{"role": "user", "content": "Мне нужно придумать 4 вопроса(1 правильный, а 2 неправильных) и к ним 4 варианта ответа на них по этой лекции: " + ":\n " + text}], 0.87)['choices'][0]['message']['content']

    new_query = "У меня есть вопросы и варианты ответа, напиши в формате 1 - A, 2 - B и так далее ответы на них: \n" + q_response
    print(new_query)
    resp = getAnswer([{"role": "user", "content": new_query}])
    print(q_response + "\n Ответы: \n" + resp['choices'][0]['message']['content'])
    return {"status": True, "response": q_response + "\n Ответы: \n" + resp['choices'][0]['message']['content']}
