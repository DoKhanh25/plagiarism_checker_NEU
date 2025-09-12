# PlagCheck Docker Images

This repository contains Docker images for the PlagCheck application, a plagiarism detection system built with Flask (backend) and Angular (frontend).

## Components

- **Flask Backend**: RESTful API service that processes plagiarism detection requests
- **Angular Frontend**: User interface for the plagiarism detection system
- **MySQL**: Database for storing application data
- **Solr**: Search engine for text processing and similarity detection

## Usage

### Pull the images

```bash
# Pull Flask backend
docker pull dokhanh25/plagcheck-flask:latest

# Pull Angular frontend
docker pull dokhanh25/plagcheck-angular:latest
```

### Run with Docker Compose

The recommended way to run this application is using Docker Compose:

```bash
docker-compose up -d
```

This will start all components of the PlagCheck application.

### Environment Variables

#### Flask Backend
- `MYSQL_HOST`: MySQL server hostname
- `MYSQL_USER`: MySQL username
- `MYSQL_PASSWORD`: MySQL password
- `MYSQL_DB`: MySQL database name
- `SOLR_HOST`: Hostname for Solr
- `SOLR_PORT`: Port for Solr
- `SOLR_CORE`: Solr core name

## Version History

- 1.0.0: Initial release
