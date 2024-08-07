# 일단 사용하지 않음
import json
import warnings

from FlagEmbedding import BGEM3FlagModel   # bge-m3

import numpy as np
from scipy.spatial.distance import cosine
from chatting.models import chat_table, message_table
from chatting import db
# warnings.filterwarnings('ignore')


# embedding model 2 : bge-m3
model = BGEM3FlagModel('BAAI/bge-m3', use_fp16=True)   # Setting use_fp16 to True speeds up computation with a slight performance degradation
def text_embedding_bge(text):
    embedding = model.encode(text, batch_size=12, max_length=8192)['dense_vecs']
    return embedding

def chat_vector_embedding(chat_id):
    # 해당 chat_id에 해당하는 message들을 message_table에서 가져온다.
    messages = message_table.query.filter_by(chat_id=chat_id).all()
    messages = map(lambda x: x.message, messages)   # 나중에 템플릿 적용
    messages = ' '.join(messages)   # 한 문장으로 합치기

    # chat_vector를 계산
    chat_vector = text_embedding_bge(messages)

    # chat_vector를 json으로 변환 후, chat_table에 업데이트
    chat_vector = json.dumps(chat_vector.tolist())
    chat_table.query.filter_by(chat_id=chat_id).update({'chat_vector': chat_vector})

    db.session.commit()
    

if __name__ == '__main__':
    # user id가 정해졌을 때, user_id에 해당하는 chat_id를 가져온다.
    user_id = 1

    # 그 중, chat_table에서 chat_vector가 Null인 것들을 가져온다.
    null_tables = chat_table.query.filter_by(user_id=user_id, chat_vector=None).all()


    # 해당 chat_id에 해당하는 message들을 message_table에서 가져온다.
    for null_table in null_tables:
        messages = message_table.query.filter_by(CHAT_ID=null_table.chat_id).all()
        messages = map(lambda x: x.message, messages)   # 나중에 템플릿 적용
        messages = ' '.join(messages)   # 한 문장으로 합치기
        
        # chat_vector를 계산
        chat_vector = text_embedding_bge(messages)

        # chat_vector를 json으로 변환 후, chat_table에 업데이트
        chat_vector = json.dumps(chat_vector.tolist())
        null_table.chat_vector = chat_vector
    db.session.commit()

    # # vector 확인
    # chat_id = 1   # 확인하고 싶은 chat_id 입력
    # vec = cursor.execute('SELECT CHAT_VECTOR FROM CHAT_TABLE WHERE CHAT_ID = :CHAT_ID', {'CHAT_ID': chat_id})
    # vec = vec.fetchone()[0]
    # vec = np.array(list(map(float, vec)))
    # print('vec')
    # print(vec)

    # # 전체 table 확인
    # chat_id = 1   # 확인하고 싶은 chat_id 입력
    # chat_info = cursor.execute('SELECT * FROM CHAT_TABLE WHERE CHAT_ID = :CHAT_ID', {'CHAT_ID': chat_id})
    # chat_info = chat_info.fetchone()
    # print('chat_info')
    # print(chat_info)

    # # 연결 종료
    # cursor.close()
    # connection.close()
