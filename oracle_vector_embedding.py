import os
import json
import getpass
import oracledb
import oracle_configs
import warnings

import torch
#from torch import Tensor
import torch.nn as nn
import torch.nn.functional as F

from transformers import AutoModel, AutoTokenizer, AutoConfig, PretrainedConfig, PreTrainedModel
from sentence_transformers import SentenceTransformer, util
from FlagEmbedding import BGEM3FlagModel   # bge-m3

from tqdm import tqdm
import pandas as pd
import numpy as np
from scipy.spatial.distance import cosine
import faiss


warnings.filterwarnings('ignore')

# embedding model 1 : llama-2-ko-7b
# tokenizer = AutoTokenizer.from_pretrained("beomi/llama-2-ko-7b")
# model = AutoModel.from_pretrained("beomi/llama-2-ko-7b")
# model = model.to('cpu')

# def text_embedding(text):
#     seq_ids = tokenizer(text, return_tensors='pt')['input_ids']   # {'input_ids': tensor([[]]), 'attention_mask': tensor([[]])}
#     embedding = model(seq_ids)['last_hidden_state'].mean(axis=[0,1]).detach().numpy()   # detach() 결과는 tensor
#     # 'last_hidden_state'와 'past_key_values'(추후 비사용 대상) 2개가 있다.
#     # model(seq_ids)['last_hidden_state'].shape == torch.Size([1, 13, 4096]) => token 하나 당 4096 차원의 벡터이고, 13 token 으로 이루어진 문장
#     return embedding

# embedding model 2 : bge-m3
model = BGEM3FlagModel('BAAI/bge-m3', use_fp16=True)   # Setting use_fp16 to True speeds up computation with a slight performance degradation
def text_embedding_bge(text):
    embedding = model.encode(text, batch_size=12, max_length=8192)['dense_vecs']
    return embedding

# Oracle DB 연결
connection = oracledb.connect(**oracle_configs.ORACLE_CONFIG)

print("Successfully connected to Oracle Database")
cursor = connection.cursor()

# user id가 정해졌을 때, user_id에 해당하는 chat_id를 가져온다.
user_id = 1

# 그 중, chat_table에서 chat_vector가 Null인 것들을 가져온다.
table = cursor.execute('SELECT CHAT_ID FROM CHAT_TABLE WHERE CHAT_VECTOR IS NULL')
table = table.fetchall()

# 해당 chat_id에 해당하는 message들을 message_table에서 가져온다.
for chat_id in table:
    chat_id = (1,)   # 이 부분은 실험용 -> 지워주세요.
    print('CHAT_ID :', chat_id[0])
    messages = cursor.execute('SELECT MESSAGE FROM MESSAGE_TABLE WHERE CHAT_ID = :CHAT_ID ORDER BY CREATED_AT', {'CHAT_ID': chat_id[0]}).fetchall()
    messages = map(lambda x: x[0], messages)   # 각 원소가 tuple이므로, 첫 번째 원소만 가져온다.
    messages = ' '.join(messages)   # 한 문장으로 합치기
    
    # chat_vector를 계산
    chat_vector = text_embedding_bge(messages)

    # chat_vector를 json으로 변환 후, chat_table에 업데이트
    chat_vector = json.dumps(chat_vector.tolist())
    cursor.execute('UPDATE CHAT_TABLE SET CHAT_VECTOR = :CHAT_VECTOR WHERE CHAT_ID = :CHAT_ID', {'CHAT_VECTOR': chat_vector, 'CHAT_ID': chat_id[0]})
    connection.commit()

# vector 확인
chat_id = 1   # 확인하고 싶은 chat_id 입력
vec = cursor.execute('SELECT CHAT_VECTOR FROM CHAT_TABLE WHERE CHAT_ID = :CHAT_ID', {'CHAT_ID': chat_id})
vec = vec.fetchone()[0]
vec = np.array(list(map(float, vec)))
print('vec')
print(vec)

# 전체 table 확인
chat_id = 1   # 확인하고 싶은 chat_id 입력
chat_info = cursor.execute('SELECT * FROM CHAT_TABLE WHERE CHAT_ID = :CHAT_ID', {'CHAT_ID': chat_id})
chat_info = chat_info.fetchone()
print('chat_info')
print(chat_info)

# 연결 종료
cursor.close()
connection.close()
