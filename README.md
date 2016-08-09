# search_system_example
快速搭建一个搜索引擎，示例程序

有时候你可能有这样的小需求，短时间内快速搭建一个规模不大的搜索引擎，并提供一个简单的界面给同事或者小部分人使用，这篇文章旨在介绍搭建一个简单搜索引擎的步骤，并力求做到：  
1. 搜索引擎和数据分离，搜索引擎不应该依赖于数据存储和web接口
2. 可移植性要好，可以快速从本地机器迁移到服务器或者云端主机

分解任务之后，我们有三部分工作要做：  

搜索引擎——>准备要进行检索的数据——>web查询接口  

下面分别介绍每一步

## 第一步：搭建搜索引擎
---

首先我们要搭建一个纯的搜索引擎，这时候引擎是空跑的、可以移植的、提供了访问接口，但暂时还没有索引数据，我们使用Elasticsearch来搭建，关于Elasticsearch的简介请见：[中文文档](https://www.gitbook.com/book/looly/elasticsearch-the-definitive-guide-cn)  

有两种方式搭建Elasticsearch集群，一种是本地搭建，具体步骤请见上面的文档，一般来说会有一些依赖的环境问题需要你逐步安装。另外一种是基于Docker的安装，直接下载一个Elasticsearch的镜像就可以了，不需要关心安装过程中的依赖问题。我们推荐使用这种方式来搭建，具体如下：
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
