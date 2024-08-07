import os
import json
import getpass
import oracledb
import oracle_configs
import warnings

import torch
from torch import Tensor
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

# BGE-M3 모델 로드
model = BGEM3FlagModel('BAAI/bge-m3', use_fp16=True)
def text_embedding_bge(text):
    embedding = model.encode(text, batch_size=12, max_length=8192)['dense_vecs']
    return embedding

# Oracle DB 연결
connection = oracledb.connect(**oracle_configs.ORACLE_CONFIG)
print("Successfully connected to Oracle Database")
cursor = connection.cursor()

# user_id가 정해졌을 때, 해당 user에 해당하는 chat 중 가장 적합한 chat의 chat_id를 찾는다.
user_id = 1

# user_id, query, top_k를 입력받아, 가장 유사한 chat을 top_k개 찾는다.
def search_similar_chats(user_id, query, top_k=5):
    # 해당 user_id의 채팅 벡터 가져오기
    cursor.execute('''
        SELECT CHAT_ID, CHAT_VECTOR 
        FROM CHAT_TABLE 
        WHERE USER_ID = :USER_ID AND (CHAT_VECTOR IS NOT NULL)
    ''', {'USER_ID': user_id})
    
    results = cursor.fetchall()
    print('search 개수 :', len(results))

    chat_ids = []
    vectors = []
    for chat_id, chat_vector in results:   # chat_id = 1, chat_vector = [Decimal('0.1'), Decimal('0.2'), ...]
        chat_ids.append(chat_id)
        chat_vector = np.array(list(map(float, chat_vector))).astype('float32')
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
    distances, indices = index.search(query_vector, min(top_k, len(vectors)))   # [[0.84129953]] [[0]]
    
    results = []
    for i, idx in enumerate(indices[0]):
        chat_id = chat_ids[idx]
        distance = distances[0][i]
        
        # 채팅 정보 가져오기
        cursor.execute('SELECT MESSAGE FROM MESSAGE_TABLE WHERE CHAT_ID = :CHAT_ID', {'CHAT_ID': chat_id})
        chat_info = cursor.fetchall()
        
        results.append({
            'chat_id': chat_id,
            'distance': distance,
            'messages': chat_info
        })
    
    return results

answers = search_similar_chats(1, '내일 날씨 어떤가?', 3)
for i, answer in enumerate(answers):
    print(i, answer)