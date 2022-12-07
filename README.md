Enabling Roll-up and Drill-down Operations in News Exploration via Knowledge Graphs
===


Demo Site
----------
https://ncexplorer.knowledge-fusion.science

Demo Youtube Video: https://youtu.be/NUdiUdoH0Gc


News Data
----------
https://knowledge-fusion-public-dataset.s3.ap-southeast-1.amazonaws.com/news.json.zip

Components
----------
* Data pipline to transform documents into multiple associated concepts
* A relevance level ranking algorithm
* Simple Admin Portal to view document and concept

Software Requirements
---------------------
* python3.9
* pipenv
* mongodb

Other requirements
--------------
* NLP services to perform NER and NEL for text documents
* A knowledge graph (KG) with ontology
* A reachability index of the KG


Installations
-------------
* create python virtual environment with the command `make config`
* copy `.env.example` into `.env` and supply your credentials in `.env` file
* to run the application: `python app/application.py`
* open `http://localhost:5100`, key in your credential, you will be redirected into a simple admin dashboard


Data Flow
-----------------
1. raw document insert into `News` collection. set `processing_state=cleaned`
2. the data pipline in `app.news_processor.task_run_pipeline` will analyze `News`
3. once the task is complete. navigate to your dashboard. click on `News Analytics` and click `view`

Release Procedure
-----------------
