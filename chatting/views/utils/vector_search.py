import os
import json
import getpass
import oracle_configs
import warnings
import torch

from FlagEmbedding import BGEM3FlagModel   # bge-m3
from transformers import AutoTokenizer, AutoModelForCausalLM

from tqdm import tqdm
import pandas as pd
import numpy as np
import faiss

from chatting.models import chat_table, message_table
from openai import OpenAI
import openai_api_key

warnings.filterwarnings('ignore')

# BGE-M3 모델 로드
model = BGEM3FlagModel('BAAI/bge-m3', use_fp16=True)
def text_embedding_bge(text):
    embedding = model.encode(text, batch_size=12, max_length=8192)['dense_vecs']
    return embedding
client = OpenAI(api_key=openai_api_key.OPENAI_API_KEY)

# summary model : gemma2 2b
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(device)
summary_tokenizer = AutoTokenizer.from_pretrained("google/gemma-2-2b-it")
summary_model = AutoModelForCausalLM.from_pretrained(
    "google/gemma-2-2b-it",
    device_map="auto",
    torch_dtype=torch.bfloat16,
).to(device)

def summarize(text):
    
    # user_prompt = "Summarize the following text in one sentence: " + text
    user_prompt = 'The following text is a conversation with a user. Please summarize it into key points so that you can remember it later.' + text
    messages = [
        {"role": "user", "content": user_prompt}
    ]
    input_ids = summary_tokenizer.apply_chat_template(messages, return_tensors="pt", return_dict=True).to(device)
    print('2')
    outputs = summary_model.generate(**input_ids, max_new_tokens=2048)   # max_new_tokens=256
    print('3')
    output = summary_tokenizer.decode(outputs[0])
    print('4')
    return output

def summarize_conversation(chat_id):
    """주어진 chat_id의 대화 내용을 요약합니다."""
    messages = message_table.query.filter_by(chat_id=chat_id).all()
    conversation_text = ""

    for m in messages:
        message = m.message
        role = "Assistant" if m.is_bot_message else "User"
        conversation_text += f"{role}: {message}\n" 

    system_prompt = f"The following text is a conversation with a user. Please summarize it into key points so that you can remember it later."

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "system", "content": system_prompt},
                  {"role": "user", "content": f"{conversation_text}\n\nSummary:"}],
        temperature=0.7,
        max_tokens=2048,
    )
    return response.choices[0].message.content
# Oracle DB 연결
# connection = oracledb.connect(**oracle_configs.ORACLE_CONFIG)
# print("Successfully connected to Oracle Database")
# cursor = connection.cursor()

# user_id가 정해졌을 때, 해당 user에 해당하는 chat 중 가장 적합한 chat의 chat_id를 찾는다.
# user_id = 1

# user_id, query, top_k를 입력받아, 가장 유사한 chat을 top_k개 찾는다.
def search_similar_chats(user_id, query, top_k=5):
    # 해당 user_id의 채팅 벡터 가져오기
    # cursor.execute('''
    #     SELECT CHAT_ID, CHAT_VECTOR 
    #     FROM CHAT_TABLE 
    #     WHERE USER_ID = :USER_ID AND (CHAT_VECTOR IS NOT NULL)
    # ''', {'USER_ID': user_id})
    results = chat_table.query.filter_by(user_id=user_id).all()
    
    print('search 개수 :', len(results))

    chat_ids = []
    vectors = []
    for result in results:   # chat_id = 1, chat_vector = [Decimal('0.1'), Decimal('0.2'), ...]
        chat_ids.append(result.chat_id)
        if result.chat_vector is None:
            continue
        chat_vector = np.array(list(map(float, result.chat_vector))).astype('float32')
        vectors.append(chat_vector)

    if not vectors:
        print('no chat vectors')
        return []  # 해당 사용자의 채팅이 없는 경우

    # FAISS 인덱스 생성
    vectors = np.array(vectors)
    dimension = vectors.shape[1]   # 벡터의 차원 : 1024
    index = faiss.IndexFlatL2(dimension)
    index.add(vectors)

    # 쿼리 텍스트를 벡터로 변환
    query_vector = text_embedding_bge(query)
    query_vector = np.array(query_vector).reshape(1, -1).astype('float32')
    
    # FAISS를 사용하여 유사한 벡터 검색
    print(query_vector.shape, vectors.shape)
    distances, indices = index.search(query_vector, min(top_k, len(vectors)))   # [[0.84129953]] [[0]]
    
    results = []
    for i, idx in enumerate(indices[0]):
        chat_id = chat_ids[idx]
        distance = distances[0][i]
        
        # message table에서 채팅 정보 가져오기
        # chat_info = message_table.query.filter_by(chat_id=chat_id).all()
        # results.append({
        #     'chat_id': chat_id,
        #     'distance': distance,
        #     'messages': [c.message for c in chat_info]
        # })

        # chat table에서 summary 가져오기
        chat_info = chat_table.query.filter_by(chat_id=chat_id).first()
        results.append({
            'chat_id': chat_id,
            'distance': distance,
            'summary': chat_info.summary
        })
    return results

# chat table의 summary를 embedding 하고 chat_vector와 요약 text를 반환
def chat_vector_embedding(user_id, chat_id):
    # 해당 chat_id에 해당하는 message들을 message_table에서 가져온다.
    # messages = message_table.query.filter_by(chat_id=chat_id).all()
    # messages = map(lambda x: x.message, messages)   # 나중에 템플릿 적용
    # messages = ' '.join(messages)   # 한 문장으로 합치기

    # # message 요약
    # messages = summarize(messages)
    messages = summarize_conversation(chat_id)
    print('end')

    # chat_vector를 계산
    chat_vector = text_embedding_bge(messages)
    print('Embedding Done')
    # chat_vector를 json으로 변환 후, chat_table에 업데이트
    # chat_vector = json.dumps(chat_vector.tolist())
    # chat_table.query.filter_by(chat_id=chat_id).update({'chat_vector': chat_vector})   # 바로 update 해도 됨

    return chat_vector, messages   # 나중에 messages는 요약해서 return

if __name__ == '__main__':
    # test 가장 유사한 3개
    # answers = search_similar_chats(1, '내일 날씨 어떤가?', 3)
    # for i, answer in enumerate(answers):
    #     print(i, answer)
    chat_id = 1
    messages = message_table.query.filter_by(chat_id=chat_id).all()
    messages = map(lambda x: x.message, messages)   # 나중에 템플릿 적용
    print(messages)
    messages = ' '.join(messages)   # 한 문장으로 합치기
    print(messages)