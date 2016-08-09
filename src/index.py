from datetime import datetime
from elasticsearch import Elasticsearch
es = Elasticsearch()

doc = {
    'user_id': '',
    'user_name': '',
    'timestamp': datetime.now()
}

id = 0
file = open('/dataset/data.csv')
lines = file.readlines()
for line in lines:
    shard = line.strip('\n').split(',')
    id += 1
    doc['user_id'] = shard[0]
    doc['user_name'] = shard[1]

    res = es.index(index="user_info", doc_type='basic', id=id, body=doc)
    print(res['created']), id, ' doc(s) indexed.'
