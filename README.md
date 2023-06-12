Enabling Roll-up and Drill-down Operations in News Exploration via Knowledge Graphs
===

Demo Video
----------
https://youtu.be/NUdiUdoH0Gc

Demo Site
----------
https://ncexplorer.knowledge-fusion.science



Dataset
----------
* News: https://knowledge-fusion-public-dataset.s3.ap-southeast-1.amazonaws.com/news.json.zip
* News with Linked KG entities and categories: https://knowledge-fusion-public-dataset.s3.ap-southeast-1.amazonaws.com/news_entity.json.zip
* Relevance evaluation task questions: https://knowledge-fusion-public-dataset.s3.ap-southeast-1.amazonaws.com/relevance_survey_question.json
* Relevance evaluation task human and GPT response: https://knowledge-fusion-public-dataset.s3.ap-southeast-1.amazonaws.com/relevance_evaluation_response.json

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
