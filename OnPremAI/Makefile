REGISTRY ?= registry.intra.charter.example/ai

build-api:
	docker build -t $(REGISTRY)/rag-api:v0.1.0 ./services/rag_api

push-api:
	docker push $(REGISTRY)/rag-api:v0.1.0

build-connectors:
	docker build -t $(REGISTRY)/connectors:v0.1.0 ./services/connectors

push-connectors:
	docker push $(REGISTRY)/connectors:v0.1.0
