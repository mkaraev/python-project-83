dev:
	poetry run flask --app page_analyzer:app --debug run

PORT ?= 8000
start:
	poetry run gunicorn -w 5 -b 0.0.0.0:$(PORT) page_analyzer:app

start-db:
	docker run --name page-analyzer-db -e POSTGRES_PASSWORD=mysecretpassword -p 54320:5432 -d postgres