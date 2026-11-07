\# MongoDB Distributed Architecture



\## Description



This academic project focuses on the implementation of distributed database

architecture using MongoDB.



It covers two main concepts:



\- \*\*Replication:\*\* Maintaining multiple copies of data across MongoDB nodes

&#x20; to improve availability and fault tolerance.

\- \*\*Sharding:\*\* Distributing data across multiple shards to support horizontal

&#x20; scalability.



\## Project Architecture



The project is divided into two parts:



\### 1. MongoDB Replication



Implementation of a MongoDB Replica Set composed of three nodes:



\- mongo1

\- mongo2

\- mongo3



The Replica Set uses:

\- One Primary node

\- Two Secondary nodes



A Python Flask application is also included to interact with the database

and manage command data.



\### 2. MongoDB Sharding



Implementation of a sharded MongoDB cluster composed of:



\- One Config Server

\- Two Shards

\- One Mongos Router



The collection `ecommerce.commandes` is sharded using the key:



```javascript

{ order\_id: 1 }

