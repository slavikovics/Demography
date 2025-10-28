# Belarusian demography
![Frontend]('./images/frontend.png')
## Acomplished tasks:
- Parsing SDMX-JSON datastructures from belstat. 
- Fetching data and saving to database.
- Forecasting future values using library Prophet.
- Creating FastAPI API for the web-frontend to receive data.
- Creating Frontend to display demographic data and forecasts.

## How to launch:
- Clone repository
```bash
git clone https://github.com/slavikovics/Demography
cd Demography
```
### Without docker:
- Go to data folder
```bash
cd data
```
- Create virtualenv
```bash
virtualenv .venv
```
If you don't have virtualenv installed:
```bash
pip3 install virtualenv
```
- Intall dependencies from requirements.txt

Go to your virtual environment:
```bash
source ./.venv/bin/activate
```
Insatll dependencies:
```bash
pip3 install -r requirements.txt
```
- Launch prepare.py as module.
This will download data from belstat API, create database and create all predictions. Creating forecasts may take a lot of time, if you don't need
predictions data, you can just terminate forecasting at any time.
```bash
python3 -m prepare
```
- After forecasting API will be automatically launched. If you have already loaded data, you can launch run.py as module, which will just start an API.
```bash
python3 -m run
```
- Go to Frontend folder, there:
```bash
npm install
```
- To launch Frontend:
```bash
npm start
```

### Using docker and docker-compose:
```bash
sudo docker compose build
sudo docker compose up
```