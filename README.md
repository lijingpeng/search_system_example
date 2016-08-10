# search_system_example
快速搭建一个搜索引擎，示例程序，地址：[https://github.com/lijingpeng/search_system_example](https://github.com/lijingpeng/search_system_example)

有时候你可能有这样的小需求，短时间内快速搭建一个规模不大的搜索引擎，并提供一个简单的界面给同事或者小部分人使用，这篇文章旨在介绍搭建一个简单搜索引擎的步骤，并力求做到：

1. 搜索引擎和数据分离，搜索引擎不应该依赖于数据存储和web接口  
2. 可移植性要好，可以快速从本地机器迁移到服务器或者云端主机

分解任务之后，我们有三部分工作要做：  

搜索引擎——>准备要进行检索的数据——>web查询接口  

下面分别介绍每一步

## 第一步：搭建搜索引擎

首先我们要搭建一个纯的搜索引擎，这时候引擎是空跑的、可以移植的、提供了访问接口，但暂时还没有索引数据，我们使用Elasticsearch来搭建，关于Elasticsearch的简介请见：[中文文档](https://www.gitbook.com/book/looly/elasticsearch-the-definitive-guide-cn)  

有两种方式搭建Elasticsearch引擎，一种是本地搭建，具体步骤请见上面的文档，一般来说会有一些依赖的环境问题需要你逐步安装。另外一种是基于Docker的安装，直接下载一个Elasticsearch的镜像就可以了，不需要关心安装过程中的依赖问题。我们推荐使用这种方式来搭建，具体如下：
```bash
# 1. 下载镜像
docker pull dockerfile/elasticsearch
# 2. 测试镜像是否能正常运行
docker run -d -p 9200:9200 -p 9300:9300 dockerfile/elasticsearch
```
通过访问http://localhost:9200/ 来查看容器是否访问成功，成功后会显示如下信息：
```json
{
    "name": "Night Thrasher",
    "cluster_name": "elasticsearch",
    "version": {
        "number": "2.1.1",
        "build_hash": "40e2c53a6b6c2972b3d13846e450e66f4375bd71",
        "build_timestamp": "2015-12-15T13:05:55Z",
        "build_snapshot": false,
        "lucene_version": "5.3.1"
    },
    "tagline": "You Know, for Search"
}
```

还记得我们的目标之一是可提供一个索引和查询的接口么，http://localhost:9200/ 这个URL就是Elasticsearch提供给我们的索引和查询接口，如果你部署到了其他的接口和服务器，只需要做相应的修改就可以了。最简单的情况你可以使用curl url来存储和检索数据，如果你想使用python，请参见[python接口封装](https://www.elastic.co/guide/en/elasticsearch/client/python-api/current/index.html)。

我们的另一个目标是存储和引擎分离，因为Docker容器适合运行无状态的应用，而我们的索引数据显然是需要持久化存储的，我们需要用Docker Volume来存储索引数据，具体来说在启动容器的时候：
```bash
# 映射本地主机目录data到容器中的/usr/share/elasticsearch目录中
# 容器中的elasticsearch启动的时候会将索引数据存储到该目录下，这样我们就实现了索引和容器引擎分离存储的目标
docker run -v ~/data:/usr/share/elasticsearch/data -p 9200:9200 -p 9300:9300 -d docker/elasticsearch
```
截止到目前，我们的引擎已经搭建好了，该引擎将数据存储到我们指定的位置，实现了存储分离；提供了一个URL访问接口，不依赖具体的机器环境。下面一步就是准备待索引的数据，将数据索引起来以供检索。

## 第二步 索引数据

### 测试  
在索引数据前我们先通过一个小例子测试下python接口，例子来自于[这里](https://elasticsearch-py.readthedocs.io/en/master/)

```python
from datetime import datetime
from elasticsearch import Elasticsearch
es = Elasticsearch() # 默认连接本地9200端口

doc = {
    'author': 'kimchy',
    'text': 'Elasticsearch: cool. bonsai cool.',
    'timestamp': datetime.now(),
}
# 索引数据
res = es.index(index="test-index", doc_type='tweet', id=1, body=doc)
```


```python
res = es.get(index="test-index", doc_type='tweet', id=1)
print(res['_source'])
```

    {u'text': u'Elasticsearch: cool. bonsai cool.', u'author': u'kimchy', u'timestamp': u'2016-08-09T21:15:05.956257'}

```python
es.indices.refresh(index="test-index")

res = es.search(index="test-index", body={"query": {"match_all": {}}})
print("Got %d Hits:" % res['hits']['total'])
for hit in res['hits']['hits']:
    print("%(timestamp)s %(author)s: %(text)s" % hit["_source"])
```

    Got 1 Hits:
    2016-08-09T21:15:05.956257 kimchy: Elasticsearch: cool. bonsai cool.

### 索引数据
假设数据是用户的信息数据，包括user_id和user_name, 存储在csv文件中，以逗号分隔，如下所示：
```
123,小米
234,李明
345,李念
```
接下来我们索引这些数据，指定index名字为user_info, doc_type为basic, 代表用户的基本信息。代码(src/index.py)如下：


```python
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
```
输出：  
```
    True 1  doc(s) indexed.  
    True 2  doc(s) indexed.  
    True 3  doc(s) indexed.  
```


```python
res = es.get(index="user_info", doc_type='basic', id=1)
print(res['_source'])
```
输出：  

    {u'user_id': u'123', u'user_name': u'\u5c0f\u7c73', u'timestamp': u'2016-08-09T21:30:17.860371'}

```python
# 检索
res = es.search(index="user_info", body={"query": {"match_all": {}}})
print("Got %d Hits:" % res['hits']['total'])
for hit in res['hits']['hits']:
    print("%(timestamp)s %(user_id)s: %(user_name)s" % hit["_source"])
```
输出：  
```
Got 3 Hits:
2016-08-09T21:30:17.860371 234: 李明
2016-08-09T21:30:17.860371 123: 小米
2016-08-09T21:30:17.860371 345: 李念
```
到目前为止，我们的数据检索系统完成了，真的是非常的简单，elasticsearch Schema Free的特性在这里得到了很好的体现，无论你的数据是在本地文件还是在DB， 你只需要重写数据解析和索引模块就可以了。

## 第三步 提供一个web接口
试试把这个地址复制到浏览器地址栏中执行：
```
http://localhost:9200/user_info/basic/_search?q=user_id:345
```
没错，这个就是检索user_id = 345的用户基本信息，在浏览器中返回：
```json
{
    "took": 6,
    "timed_out": false,
    "_shards": {
        "total": 5,
        "successful": 5,
        "failed": 0
    },
    "hits": {
        "total": 1,
        "max_score": 0.30685282,
        "hits": [
            {
                "_index": "user_info",
                "_type": "basic",
                "_id": "3",
                "_score": 0.30685282,
                "_source": {
                    "user_name": "李念",
                    "user_id": "345",
                    "timestamp": "2016-08-09T21:30:17.860371"
                }
            }
        ]
    }
}
```

接下来就可以编写web服务了，你可以使用任何你熟悉的web框架搭建一个友好的web访问界面，比如Spring MVC、或者是Flask。为了保持我们的接口足够简单，这里我们使用纯HTML+jQuery来搭建，不依赖任何web框架。不过我们先要解决ajax跨域访问的问题，万能的开源社区已经给我们提供了解决方案，我们需要在web工程里使用[elasticsearch.js](https://github.com/lijingpeng/search_system_example/tree/master/elasticsearch.js)
