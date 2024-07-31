import os
import json
import getpass
import oracledb
import oracle_configs

import torch
from torch import Tensor
import torch.nn as nn
import torch.nn.functional as F

from transformers import AutoModel, AutoTokenizer, AutoConfig, PretrainedConfig, PreTrainedModel
from sentence_transformers import SentenceTransformer, util
from FlagEmbedding import BGEM3FlagModel   # bge-m3

import os
from tqdm import tqdm
import pandas as pd
import numpy as np
from scipy.spatial.distance import cosine
import faiss

## embedding model 1 : llama-2-ko-7b
# tokenizer = AutoTokenizer.from_pretrained("beomi/llama-2-ko-7b")
# model = AutoModel.from_pretrained("beomi/llama-2-ko-7b")
# model = model.to('cpu')

# def text_embedding(text):
#     seq_ids = tokenizer(text, return_tensors='pt')['input_ids']   # {'input_ids': tensor([[]]), 'attention_mask': tensor([[]])}
#     embedding = model(seq_ids)['last_hidden_state'].mean(axis=[0,1]).detach().numpy()   # detach() 결과는 tensor
#     # 'last_hidden_state'와 'past_key_values'(추후 비사용 대상) 2개가 있다.
#     # model(seq_ids)['last_hidden_state'].shape == torch.Size([1, 13, 4096]) => token 하나 당 4096 차원의 벡터이고, 13 token 으로 이루어진 문장
#     return embedding

## embedding model 2 : bge-m3
model = BGEM3FlagModel('BAAI/bge-m3',  
                       use_fp16=True) # Setting use_fp16 to True speeds up computation with a slight performance degradation
def text_embedding_bge(text):
    embedding = model.encode(text, batch_size=12, max_length=8192)['dense_vecs']
    return embedding

# Oracle DB 연결
connection = oracledb.connect(**oracle_configs.ORACLE_CONFIG)

print("Successfully connected to Oracle Database")

cursor = connection.cursor()

d = cursor.execute('SELECT MESSAGE FROM MESSAGE_TABLE ORDER BY CREATED_AT')

texts = ' '.join([t[0] for t in d.fetchall()])
t = text_embedding_bge(texts)

t = json.dumps(t.tolist())
cursor.execute('UPDATE CHAT_TABLE SET CHAT_VECTOR = :CHAT_VECTOR WHERE CHAT_ID = 1', {'CHAT_VECTOR': t})
connection.commit()

p = cursor.execute('SELECT CHAT_VECTOR FROM CHAT_TABLE WHERE CHAT_ID = 1')
vec = p.fetchone()[0]
vec = np.array(list(map(float, vec)))
print(vec)

cursor.close()
connection.close()
