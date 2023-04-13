## AeroDisk Test Task

AeroDisk is a file storage service that allows users to store and manage their files in the cloud.

### Installation

To install AeroDisk, follow these steps:

1. Clone the repository from GitHub:
    ```bash
    git clone https://github.com/romaokorosso/aerodisk_test_task.git
    ```
2. Create `.env` file:
    ```bash
    cp .env.example .env
    ```
If you prefer docker (! may not work correctly)
3. Run Docker containers:
    ```bash
    docker-compose up -d
    ```
4. Visit `http://localhost:{APP_PORT}` in your browser.

For non-docker usage
3. Run database
```bash
docker-compose up -d db
```
4. Install poetry and dependencies 

   i.first
   ```shell
   pip install poetry
   ```
   ii. second
   ```bash
   poetry install
   ```
5. Wait while db is up, then
```bash
sh entrypoint.sh
```
6. Up uvicorn
```bash
uvicorn main:app --reload --port 8000 --host 0.0.0.0
```
### Built With

* [Python](https://www.python.org/)
* [Poetry](https://python-poetry.org/)
* [FastAPI](https://fastapi.tiangolo.com/)
* [Jinja2](https://jinja.palletsprojects.com/en/)
* [Docker](https://www.docker.com/)
* [PostgreSQL](https://www.postgresql.org/)

### License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

### Contact

Created by [@RomaOkorosso](https://github.com/RomaOkorosso)