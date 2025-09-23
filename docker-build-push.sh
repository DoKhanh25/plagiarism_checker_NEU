#!/bin/bash

# Set variables
DOCKER_HUB_USERNAME="dokhanh25"  # Replace with your Docker Hub username
BACKEND_IMAGE="plagcheck-flask"
FRONTEND_IMAGE="plagcheck-angular"
IMAGE_VERSION="1.0.0"

# Build and push Flask backend
echo "Building Flask backend Docker image..."
docker build -t ${DOCKER_HUB_USERNAME}/${BACKEND_IMAGE}:${IMAGE_VERSION} -f Dockerfile.flask .
docker tag ${DOCKER_HUB_USERNAME}/${BACKEND_IMAGE}:${IMAGE_VERSION} ${DOCKER_HUB_USERNAME}/${BACKEND_IMAGE}:latest

# Build and push Angular frontend
echo "Building Angular frontend Docker image..."
#cd ../../Front-end/PlagCheck
cd ../plagiarism_checker_NEU_FE
docker build -t ${DOCKER_HUB_USERNAME}/${FRONTEND_IMAGE}:${IMAGE_VERSION} -f Dockerfile.angular .
docker tag ${DOCKER_HUB_USERNAME}/${FRONTEND_IMAGE}:${IMAGE_VERSION} ${DOCKER_HUB_USERNAME}/${FRONTEND_IMAGE}:latest

# Login to Docker Hub
echo "Logging in to Docker Hub..."
docker login -u ${DOCKER_HUB_USERNAME}

# Push images to Docker Hub
echo "Pushing images to Docker Hub..."
docker push ${DOCKER_HUB_USERNAME}/${BACKEND_IMAGE}:${IMAGE_VERSION}
docker push ${DOCKER_HUB_USERNAME}/${BACKEND_IMAGE}:latest
docker push ${DOCKER_HUB_USERNAME}/${FRONTEND_IMAGE}:${IMAGE_VERSION}
docker push ${DOCKER_HUB_USERNAME}/${FRONTEND_IMAGE}:latest

echo "Process completed successfully!"
