Streamlit dashboard displaying analytics of a DeGiro stock portfolio.

![screenshot_portfolio_dashboard](screenshot_portfolio_dashboard.png)

# Installation

## Setting Up the Application Locally

To run the application on your local machine, follow these steps:

### 1. Verify Python and pip are installed

Ensure that Python 3.10+ and pip are installed. You can check the versions by running the following commands:

```bash
python3 --version
pip --version
```

If they are not installed, you can download Python from the official site: [Download Python](https://www.python.org/downloads/).

### 2. Clone the repository to your local machine

Clone the repository using the following command:

```bash
git clone https://github.com/matteorosato/degiro-portfolio-analyzer.git
```

### 3. Navigate into the project directory

Go into the project directory:

```bash
cd degiro-portfolio-analyzer
```

### 4. Create a virtual environment for the project

To set up a virtual environment, follow the steps for your operating system:
- On Windows:
  ```bash
  py -m venv .venv
  ```
- On macOS and Linux:
  ```bash
  python3 -m venv .venv
  ```

### 5. Activate the virtual environment

Activate the virtual environment using the appropriate command for your system:
- On Windows:
  ```bash
  .venv\Scripts\activate
  ```
- On macOS and Linux:
  ```bash
  source .venv/bin/activate
  ```

### 6. Install the required dependencies

Install the project dependencies by running the following command:
- On Windows:
  ```bash
  py -m pip install -r requirements.txt
  ```
- On macOS and Linux:
  ```bash
  python3 -m pip install -r requirements.txt
  ```

### 7. Configure the `.env` file

Populate the `.env` file with the necessary environment variables. You can refer to the `.env.example` file as a guide.

### 8. Set up the `config.toml` file

Edit the `config.toml` file with your personal settings and preferences.

### 9. Run the application

To run the application, follow these steps:

1. **Navigate to the `backend` directory**:  
   First, change your working directory to the `backend` folder:
   ```bash
   cd backend
   ```

2. **Start the Flask backend**:  
   Run the Flask application by executing the following command:
   ```bash
   python main.py
   ```

3. **Run the Streamlit frontend**:  
   Open a new terminal window (or tab), navigate back to the project root folder, and run the Streamlit app:
   ```bash
   streamlit run app.py
   ```

   This will launch the Streamlit app, which will communicate with the Flask backend to display the user interface.

   If you're using **PyCharm**, you can follow the instructions in this [guide](https://discuss.streamlit.io/t/run-streamlit-from-pycharm/21624) to run Streamlit directly from the IDE.

After completing these steps, the application should be running locally, and you can begin interacting with it.
## Docker
Before you start, make sure Docker is installed on your machine/server. See the [official Docker installation guide](https://docs.docker.com/engine/install/) based on your OS.

## Install app

### Create a new directory for your portfolio analyzer on your machine/server
```
mkdir portfolio-analyzer
cd portfolio-analyzer
```

### Download the docker-compose.yaml from GitHub
```
curl -O https://raw.githubusercontent.com/kbberendsen/portfolio-analyzer/main/docker-compose.yaml
```

### Build and run the Docker container

```
docker compose up --build -d
```

### Updating the container
```
docker compose down
docker compose pull
docker compose up --force-recreate -d --build
```

# Initial run
Go to http://localhost:8501/ to see your stock portfolio dashboard! After running the app, the streamlit port (8501) can be redirected to another domain if desired.

## How to export transactions data from Degiro
To export your transactions in CSV format, follow the official procedure described by Degiro. You can find the instructions on the official
[Degiro Helpdesk page](https://www.degiro.com/uk/helpdesk/tax/tax-treaties/which-reports-are-there-and-where-can-i-find-them).
This page provides step-by-step guidance on how to download your transactions report from your Degiro account.

## Upload initial transactions file
- When opening the dashboard for the first time, upload the downloaded transactions file.
- The uploaded file will be stored in the 'uploads' directory in the portfolio-analyzer directory.
- Reload the page. Loading the dashboard for the first time ([after you've mapped the tickers](#ticker-mapping)) might take a few minutes, depending on the date range of transactions. Subsequent runs will take a few seconds to load.

## Updating transactions file
- After new transactions, download the new transactions file from DeGiro. The old file will be overwritten so make sure to select the full date range of transactions each time to not miss any previous transactions.
- To update the transactions data in the dashboard, upload the new transactions file through the sidebar in the dashboard.
- Reload the page.

## Directory structure
After uploading your transaction csv file to the dashboard for the first time, your app directory should look like this:

```
.
├── .env
├── cronjobs
│   └── logs
├── docker-compose.yaml
└── output
    └── cached data files
└── uploads
    └── Transactions.csv
```

## Ticker Mapping

After uploading your transaction data, the app requires **stock tickers** (e.g., `AAPL` for Apple) to fetch price data from Yahoo Finance. However, DeGiro only provides **ISIN identifiers**, not tickers. Therefore, **you need to manually map each ISIN to a ticker** the first time you encounter a new product.

### How to map tickers

1. Go to the **ticker mapping** page.
2. Use the **Auto-fill tickers** button to automatically search for tickers based on the product name (this can take a few seconds).
3. Carefully review all auto-filled tickers. **Exchange-traded funds (ETFs)** in particular can have multiple versions across exchanges — make sure the ticker matches the **correct exchange and price**.
4. If auto-fill fails or the ticker is incorrect:
   - Simplify the **display name** and retry auto-fill.
   - Or: visit [Yahoo Finance](https://finance.yahoo.com).
   - Search for the product name.
   - Choose the ticker with the correct exchange and price.

### Manual editing

- You can **edit the ticker** and **display name** for each ISIN directly in the app.
- You can also **download the mapping as a JSON file**, edit it manually, and re-upload it if needed.
- The **display name** is used throughout the dashboard (e.g., charts and tables), so feel free to customize it.

> ⚠️ If ticker fields remain empty, the app will not show the product. You must complete ticker mapping before proceeding.

## Currency Conversion
The app supports **currency conversion** for products priced in different currencies. It uses [Yahoo Finance](https://finance.yahoo.com) to fetch exchange rates. The app will automatically convert all prices to Euro.

# Optional: Supabase database
The app can utilize a [Supabase database](https://supabase.com/) to store and retrieve your portfolio performance data in the cloud. The Supabase free tier will suffice. Create a new project and create three tables (this can be done in the 'SQL Editor' in the Supabase online dashboard):

**Daily performance table**
```
CREATE TABLE portfolio_performance_daily (
    product VARCHAR,
    ticker VARCHAR,
    quantity INT,
    start_date DATE,
    end_date DATE,
    avg_cost NUMERIC,
    total_cost NUMERIC,
    transaction_costs NUMERIC,
    current_value NUMERIC,
    current_money_weighted_return NUMERIC,
    realized_return NUMERIC,
    net_return NUMERIC,
    current_performance_percentage NUMERIC,
    net_performance_percentage NUMERIC,
    PRIMARY KEY (ticker, end_date)
);
```

**Monthly performance table**
```
CREATE TABLE portfolio_performance_monthly (
    product VARCHAR,
    ticker VARCHAR,
    quantity INT,
    start_date DATE,
    end_date DATE,
    avg_cost NUMERIC,
    total_cost NUMERIC,
    transaction_costs NUMERIC,
    current_value NUMERIC,
    current_money_weighted_return NUMERIC,
    realized_return NUMERIC,
    net_return NUMERIC,
    current_performance_percentage NUMERIC,
    net_performance_percentage NUMERIC,
    PRIMARY KEY (ticker, end_date)
);
```

**Stock prices table**
```
CREATE TABLE stock_prices (
    ticker TEXT,
    date DATE,
    price NUMERIC,
    fx_rate NUMERIC,
    currency_pair, TEXT
    PRIMARY KEY (ticker, date)
);
```
After creating the tables, make sure to go to the Supabase project (API) settings to retrieve your __Supabase URL and key__. These values need to be filled in into the .env file (see below).

## Create the .env file for Supabase
Create a `.env` file in the same directory as the downloaded docker-compose file. If you want to use a Supabase database ([optional](#optional-supabase-database)), make sure to enter your URL and key values in the .env file and set `USE_SUPABASE` to `"true"`. If not, leave the default values. It's also an option to change the applicable fields in the docker-compose file instead.

```
cat <<EOT > .env
USE_SUPABASE=false
SUPABASE_URL=https://your-supabase-url
SUPABASE_KEY=your-supabase-api-key
EOT
```

# Disclaimer
I am not affiliated with [DEGIRO](https://www.degiro.com/) in any way. This project is an independent, unofficial portfolio analytics tool created to gain better insight and control over my investments. It is not endorsed, supported, or maintained by [DEGIRO](https://www.degiro.com/). Use this tool at your own discretion.

# Credits
This project is inspired by the work of [Kas Berendsen](https://github.com/kbberendsen) and his repository [portfolio-analyzer](https://github.com/kbberendsen/portfolio-analyzer), from which I have forked and further developed this tool.
