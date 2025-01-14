# Variables
IMAGE_NAME := bioinformatics
IMAGE_TAG := latest
CONTAINER_NAME := bioinformatics
DOCKERFILE := Dockerfile
SOURCE_DIR := src
PYTHON_SOURCES := $(shell find $(SOURCE_DIR) -type f -name '*.py')
PROJECT_FILE = requirements.txt

# Default target
.PHONY: all
all: build

# Build the Docker image (only if Python files or Dockerfile changed)
.PHONY: build
build: .docker-built


.docker-built: $(DOCKERFILE) $(PROJECT_FILE)
	@echo "Building Docker image $(IMAGE_NAME):$(IMAGE_TAG)..."
	docker build --progress auto -t $(IMAGE_NAME):$(IMAGE_TAG) -f $(DOCKERFILE) .
	@touch .docker-built

# Run the Docker container
.PHONY: run
run: build
	@echo "Running container $(CONTAINER_NAME)..."
	docker run \
		--name $(CONTAINER_NAME) \
		--gpus all \
		--rm -it \
		-v ./notebooks:/usr/src/work/notebooks \
		-v ./figures:/usr/src/work/figures \
		-v ./src:/usr/src/work/src \
		-v ./data:/usr/src/work/data \
		-v ./scripts:/usr/src/work/scripts \
		$(IMAGE_NAME):$(IMAGE_TAG)

# Stop the container

.PHONY: setup
setup:
	@echo "Setting up the project"

.PHONY: stop
stop:
	@echo "Stopping container $(CONTAINER_NAME)..."
	-docker stop $(CONTAINER_NAME)

# Remove the Docker image
.PHONY: clean
clean:
	@echo "Removing Docker image $(IMAGE_NAME):$(IMAGE_TAG)..."
	-docker rmi $(IMAGE_NAME):$(IMAGE_TAG)
	@rm -f .docker-built

# Remove all Docker images and containers
.PHONY: prune
prune:
	@echo "Cleaning up Docker images and containers..."
	docker system prune -af

# Push the image to a Docker registry
.PHONY: push
push:
	@echo "Pushing Docker image $(IMAGE_NAME):$(IMAGE_TAG)..."
	docker push $(IMAGE_NAME):$(IMAGE_TAG)

# Pull the image from a Docker registry
.PHONY: pull
pull:
	@echo "Pulling Docker image $(IMAGE_NAME):$(IMAGE_TAG)..."
	docker pull $(IMAGE_NAME):$(IMAGE_TAG)

# Display help
.PHONY: help
help:
	@echo "Usage:"
	@echo "  make build     - Build the Docker image (if necessary)"
	@echo "  make run       - Run the Docker container"
	@echo "  make stop      - Stop the running container"
	@echo "  make clean     - Remove the Docker image"
	@echo "  make prune     - Remove all unused Docker data"
	@echo "  make push      - Push the Docker image to a registry"
	@echo "  make pull      - Pull the Docker image from a registry"
