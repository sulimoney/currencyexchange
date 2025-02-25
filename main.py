import os
import pandas as pd
import subprocess
from flask import Flask, send_file, request
import plotly.express as px

app = Flask(__name__)

# Set directory where CSV files are stored
data_dir = "exchange_rates"

# ✅ Run scrapper.py before starting Flask
if not os.path.exists(data_dir) or not os.listdir(data_dir):
    print("🔄 No CSV files found. Running scrapper.py to fetch data...")
    subprocess.run(["python", "scrapper.py"], check=True)
else:
    print("✅ Exchange rates already exist.")

@app.route("/")
def home():
    try:
        # Get list of CSV files, sorted by date
        csv_files = sorted(
            [f for f in os.listdir(data_dir) if f.startswith("exchange_rates_") and f.endswith(".csv")],
            reverse=True  # Newest first
        )

        if not csv_files:
            return "<h1>No exchange rate data found.</h1>"

        # Get the requested date from URL parameters
        requested_date = request.args.get("date")

        # Find the index of the requested date or use the latest file
        if requested_date and f"exchange_rates_{requested_date}.csv" in csv_files:
            current_index = csv_files.index(f"exchange_rates_{requested_date}.csv")
        else:
            current_index = 0  # Default to latest file

        latest_file = os.path.join(data_dir, csv_files[current_index])
        date_str = latest_file.split("_")[-1].replace(".csv", "")

        # Load the CSV
        df = pd.read_csv(latest_file, header=0)
        df.columns = ["Currency", "Buying Price", "Selling Price", "Other"]

        # Retrieve conversion input before constructing conversion_form
        amount = request.args.get("amount")
        currency = request.args.get("currency")
        rate_type = request.args.get("rate_type")
        conversion_result = ""
        if amount and currency and rate_type:
            amount_float = float(amount)
            rate = df.loc[df["Currency"] == currency, rate_type].values[0]
            conversion_result = f'<div class="alert alert-success mt-3"><h4 class="mb-0">{amount} {currency} = {amount_float * rate:.2f} SDG</h4></div>'

        # Currency conversion tool (form only)
        conversion_form = f"""
        <div class="card mb-4">
            <div class="card-header bg-primary text-white">
                <h5 class="mb-0">💱 Convert Currency</h5>
            </div>
            <div class="card-body">
                <form action="/" method="get" class="row g-3">
                    <div class="col-md-4">
                        <label for="amount" class="form-label">Amount</label>
                        <input type="number" class="form-control" id="amount" name="amount" step="0.01" required>
                    </div>
                    <div class="col-md-4">
                        <label for="currency" class="form-label">Currency</label>
                        <select name="currency" id="currency" class="form-select">
                            {''.join([f'<option value="{cur}">{cur}</option>' for cur in df["Currency"]])}
                        </select>
                    </div>
                    <div class="col-md-4">
                        <label for="rate_type" class="form-label">Rate Type</label>
                        <select name="rate_type" id="rate_type" class="form-select">
                            <option value="Buying Price">Buying</option>
                            <option value="Selling Price">Selling</option>
                        </select>
                    </div>
                    <div class="col-12 mt-3">
                        <button type="submit" class="btn btn-primary">Convert</button>
                        <input type="hidden" name="date" value="{date_str}">
                    </div>
                </form>
                {conversion_result}
            </div>
        </div>
        """

        # Get previous and next file links
        prev_link = ""
        next_link = ""

        if current_index < len(csv_files) - 1:
            prev_date = csv_files[current_index + 1].split("_")[-1].replace(".csv", "")
            prev_link = f'<a href="/?date={prev_date}" class="btn btn-primary me-2">⬅️ Previous</a>'

        if current_index > 0:
            next_date = csv_files[current_index - 1].split("_")[-1].replace(".csv", "")
            next_link = f'<a href="/?date={next_date}" class="btn btn-success me-2">Next ➡️</a>'

        # HTML content with Bootstrap styling
        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <meta http-equiv="refresh" content="600">
            <title>Sudan Black Market Exchange Rates</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        </head>
        <body>
            <div class="container my-4">
                <h1 class="mb-3">Sudan Black Market Exchange Rates</h1>
                <h5 class="text-muted mb-4">Date: {date_str}</h5>
                
                <div class="mb-4">
                    {prev_link}
                    {next_link}
                    <a href="/trend" class="btn btn-warning">📊 View Trends</a>
                    <a href="/download" class="btn btn-secondary ms-2">📥 Download CSV</a>
                </div>
                
                {conversion_form}
                
                <div class="table-responsive">
                    <table class="table table-striped table-hover">
                        <thead class="table-dark">
                            <tr>
                                <th>Currency</th>
                                <th>Buying Price</th>
                                <th>Selling Price</th>
                                <th>Other</th>
                            </tr>
                        </thead>
                        <tbody>
                            {"".join([f"<tr><td>{row['Currency']}</td><td>{row['Buying Price']}</td><td>{row['Selling Price']}</td><td>{row['Other']}</td></tr>" for _, row in df.iterrows()])}
                        </tbody>
                    </table>
                </div>
            </div>
            <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
        </body>
        </html>
        """

        return html_content

    except Exception as e:
        return f'<div class="container"><div class="alert alert-danger">Internal Server Error: {str(e)}</div></div>'

@app.route("/download")
def download():
    try:
        csv_files = sorted(
            [f for f in os.listdir(data_dir) if f.startswith("exchange_rates_") and f.endswith(".csv")],
            reverse=True
        )

        if not csv_files:
            return "<h1>No file available for download.</h1>"

        latest_file = os.path.join(data_dir, csv_files[0])
        return send_file(latest_file, as_attachment=True)

    except Exception as e:
        return f"<h1>Internal Server Error:</h1><p>{str(e)}</p>"

@app.route("/trend")
def trend():
    try:
        # Read all CSV files and combine into one DataFrame
        csv_files = sorted(
            [f for f in os.listdir(data_dir) if f.startswith("exchange_rates_") and f.endswith(".csv")]
        )

        if not csv_files:
            return "<h1>No exchange rate data available.</h1>"

        # Combine all exchange rate data
        all_data = []
        for file in csv_files:
            date = file.split("_")[-1].replace(".csv", "")
            df = pd.read_csv(os.path.join(data_dir, file), header=0)
            df.columns = ["Currency", "Buying Price", "Selling Price", "Other"]
            df["Date"] = date
            all_data.append(df)

        df_all = pd.concat(all_data)

        # Create interactive graph
        fig = px.line(df_all, x="Date", y="Buying Price", color="Currency", title="Exchange Rate Trends")
        graph_html = fig.to_html(full_html=False)

        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <title>Exchange Rate Trends</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        </head>
        <body>
            <div class="container my-4">
                <h1 class="mb-4">Exchange Rate Trends</h1>
                <div class="mb-4">
                    <a href="/" class="btn btn-primary">⬅️ Back to Rates</a>
                </div>
                <div class="card">
                    <div class="card-body">
                        {graph_html}
                    </div>
                </div>
            </div>
            <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
        </body>
        </html>
        """

        return html_content

    except Exception as e:
        return f'<div class="container"><div class="alert alert-danger">Internal Server Error: {str(e)}</div></div>'

if __name__ == "__main__":
    from waitress import serve  # Use Waitress for production
    serve(app, host="0.0.0.0", port=8080)
