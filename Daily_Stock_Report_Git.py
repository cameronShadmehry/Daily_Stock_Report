# Necessary Libraries
import yfinance as yf, pandas as pd, shutil, os, time, glob, smtplib, ssl
from get_all_tickers import get_tickers as gt

# List of the stocks we are interested in analyzing. At the time of writing this, it narrows the list of stocks down to 44.
# If you have a list of your own you would like to use just create a new list instead of using this, for example: tickers = ["FB", "AMZN", ...] 
tickers = gt.get_tickers_filtered(mktcap_min=150000, mktcap_max=10000000)

# Check that the amount of tickers isn't more than 2000
print("The amount of stocks chosen to observe: " + str(len(tickers)))

# These two lines remove the Stocks folder and then recreate it in order to remove old stocks.
shutil.rmtree("<Your Path>\\Daily_Stock_Report\\Stocks\\")
os.mkdir("<Your Path>\\Daily_Stock_Report\\Stocks\\")

# Holds the amount of API calls we executed
Amount_of_API_Calls = 0

# This while loop is reponsible for storing the historical data for each ticker in our list. Note that yahoo finance sometimes incurs json.decode errors and because of this we are sleeping for 2
# seconds after each iteration, also if a call fails we are going to try to execute it again.
# Also, do not make more than 2,000 calls per hour or 48,000 calls per day or Yahoo Finance may block your IP. The clause "(Amount_of_API_Calls < 1800)" below will stop the loop from making
# too many calls to the yfinance API.
# Prepare for this loop to take some time. It is pausing for 2 seconds after importing each stock.

# Used to make sure we don't waste too many API calls on one Stock ticker that could be having issues
Stock_Failure = 0
Stocks_Not_Imported = 0

# Used to iterate through our list of tickers
i=0
while (i < len(tickers)) and (Amount_of_API_Calls < 1800):
    try:
        stock = tickers[i]  # Gets the current stock ticker
        temp = yf.Ticker(str(stock))
        Hist_data = temp.history(period="max")  # Tells yfinance what kind of data we want about this stock (In this example, all of the historical data)
        Hist_data.to_csv("<Your Path>\\Daily_Stock_Report\\Stocks\\"+stock+".csv")  # Saves the historical data in csv format for further processing later
        time.sleep(2)  # Pauses the loop for two seconds so we don't cause issues with Yahoo Finance's backend operations
        Amount_of_API_Calls += 1 
        Stock_Failure = 0
        i += 1  # Iteration to the next ticker
    except ValueError:
        print("Yahoo Finance Backend Error, Attempting to Fix")  # An error occured on Yahoo Finance's backend. We will attempt to retreive the data again
        if Stock_Failure > 5:  # Move on to the next ticker if the current ticker fails more than 5 times
            i+=1
            Stocks_Not_Imported += 1
        Amount_of_API_Calls += 1
        Stock_Failure += 1
print("The amount of stocks we successfully imported: " + str(i - Stocks_Not_Imported))

# OBV Analysis, feel free to replace this section with your own analysis -------------------------------------------------------------------------
list_files = (glob.glob("<Your Path>\\Daily_Stock_Report\\Stocks\\*.csv")) # Creates a list of all csv filenames in the stocks folder
new_data = [] #  This will be a 2D array to hold our stock name and OBV score
interval = 0  # Used for iteration
while interval < len(list_files):
    Data = pd.read_csv(list_files[interval]).tail(10)  # Gets the last 10 days of trading for the current stock in iteration
    pos_move = []  # List of days that the stock price increased
    neg_move = []  # List of days that the stock price increased
    OBV_Value = 0  # Sets the initial OBV_Value to zero
    count = 0
    while (count < 10):  # 10 because we are looking at the last 10 trading days
        if Data.iloc[count,1] < Data.iloc[count,4]:  # True if the stock increased in price
            pos_move.append(count)  # Add the day to the pos_move list
        elif Data.iloc[count,1] > Data.iloc[count,4]:  # True if the stock decreased in price
            neg_move.append(count)  # Add the day to the neg_move list
        count += 1
    count2 = 0
    for i in pos_move:  # Adds the volumes of positive days to OBV_Value, divide by opening price to normalize across all stocks
        OBV_Value = round(OBV_Value + (Data.iloc[i,5]/Data.iloc[i,1]))
    for i in neg_move:  # Subtracts the volumes of negative days from OBV_Value, divide by opening price to normalize across all stocks
        OBV_Value = round(OBV_Value - (Data.iloc[i,5]/Data.iloc[i,1]))
    Stock_Name = ((os.path.basename(list_files[interval])).split(".csv")[0])  # Get the name of the current stock we are analyzing
    new_data.append([Stock_Name, OBV_Value])  # Add the stock name and OBV value to the new_data list
    interval += 1
df = pd.DataFrame(new_data, columns = ['Stock', 'OBV_Value'])  # Creates a new dataframe from the new_data list
df["Stocks_Ranked"] = df["OBV_Value"].rank(ascending = False)  # Rank the stocks by their OBV_Values
df.sort_values("OBV_Value", inplace = True, ascending = False)  # Sort the ranked stocks
df.to_csv("<Your Path>\\Daily_Stock_Report\\OBV_Ranked.csv", index = False)  # Save the dataframe to a csv without the index column
# OBV_Ranked.csv now contains the ranked stocks that we want recalculate daily and receive in a digestable format.

# Code to email yourself your anaysis -----------------------------------------------------------------------------------
Analysis = pd.read_csv("<Your Path>\\Daily_Stock_Report\\OBV_Ranked.csv")  # Read in the ranked stocks

top10 = Analysis.head(10)  # I want to see the 10 stocks in my analysis with the highest OBV values
bottom10 = Analysis.tail(10)  # I also want to see the 10 stocks in my analysis with the lowest OBV values

# This is where we write the body of our email. Add the top 10 and bottom 10 dataframes to include the results of your analysis
Body_of_Email = """\
Subject: Daily Stock Report

Your highest ranked OBV stocks of the day:

""" + top10.to_string(index=False) + """\


Your lowest ranked OBV stocks of the day:

""" + bottom10.to_string(index=False) + """\


Sincerely,
Your Computer"""

context = ssl.create_default_context()
Email_Port = 465  # If you are not using a gmail account, you will need to look up the port for your specific email host
with smtplib.SMTP_SSL("smtp.gmail.com", Email_Port, context=context) as server:
    server.login("<Your email>", "<Your email password>")  #  This statement is of the form: server.login(<Your email>, "Your email password")
    server.sendmail("<Your email>", "<Email receiving message>", Body_of_Email)  # This statement is of the form: server.sendmail(<Your email>, <Email receiving message>, Body_of_Email)