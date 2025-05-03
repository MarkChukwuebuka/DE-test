# Invoice Processing System

A robust system for processing invoice data with PostgreSQL, FastAPI, and Docker.

## Features

- Import invoice data from CSV files
- Validate and classify line items
- REST API for data access
- Data integrity checks
- Containerized deployment

## Prerequisites

- Docker 20.10+
- Docker Compose 1.29+
- Python 3.9+ (for local development)

## Quick Start

1. Clone the repository:
   ```bash
   git clone https://github.com/MarkChukwuebuka/DE-test.git
   cd invoice-processing
   
2. Make Sure you have docker installed and set up, then start up the system:
   ```bash
   docker-compose up -d --build

3. Load the sample data:
   ```bash
   docker-compose exec web python src/data_loader.py

4. View the API endpoints/documentation at:
   ```bash
   http://localhost:8000/docs

5. Run tests
   ```bash
   docker-compose exec web pytest tests/ -v
