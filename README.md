# EDITH Project

## Overview
EDITH is a web application designed for monitoring and managing STARK analysis runs. It provides a user-friendly interface for users to interact with the data, visualize statistics, and manage their profiles.

Based on the workspace information, EDITH is a web application designed to monitor and manage STARK analysis runs. STARK appears to be a bioinformatics pipeline for analyzing genomic sequencing data, particularly focused on variant detection and annotation.

## Key Components of EDITH
The EDITH project is structured as a Flask web application with these key features:

User authentication and profile management
Visualization of run statistics using graphs
Management of input, repository, and archive files from STARK runs
Admin functionalities for user management and data population

## Relationship with STARK
EDITH serves as a front-end interface for STARK (Stellar Tools from raw sequencing data Analysis to variant RanKing), which is an environment for analyzing sequencing data that:

Processes raw sequencing data (BCL, FASTQ, BAM, SAM, CRAM formats)
Produces annotated variant files (VCF, TSV)
Generates analysis reports (HTML, PDF)
Follows national and international bioinformatics best practices
Supports various sequencing technologies (capture, amplicon) and detection types (constitutional, somatic mutations)

## Features
- User authentication and profile management
- Visualization of run statistics using graphs
- Management of input, repository, and archive files
- Admin functionalities for user management and data population

## Requirements
To run the EDITH application, you need to have the following installed:
- Python 3.x
- Flask
- Flask-SQLAlchemy
- Flask-Login
- Flask-Bootstrap
- Pygal
- Other dependencies listed in `requirements.txt`

## Setup Instructions

### Using Docker
1. Build the Docker image:
   ```
   docker build -t edith-app .
   ```

2. Run the application using Docker Compose:
   ```
   docker-compose up
   ```

### Local Setup
1. Clone the repository:
   ```
   git clone <repository-url>
   cd EDITH
   ```

2. Install the required Python packages:
   ```
   pip install -r requirements.txt
   ```

3. Run the application:
   ```
   python main.py
   ```

## Usage
- Access the application in your web browser at `http://localhost:5000`.
- Register a new user or log in with existing credentials.
- Navigate through the application to manage runs and view statistics.

## Contributing
Contributions are welcome! Please submit a pull request or open an issue for any enhancements or bug fixes.

## License
This project is licensed under the MIT License. See the LICENSE file for more details.