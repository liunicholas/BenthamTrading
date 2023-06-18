from bs4 import BeautifulSoup
import requests
import pandas as pd

# url = 'https://us.econoday.com/byweek.asp?cust=us'
# html = requests.get(url).content
# df_list = pd.read_html(html)
# # df = df_list[-1]
# print(df_list)
# # df.to_csv('my data.csv')



# URL of the website with the tables
# url = 'https://us.econoday.com/byweek.asp?cust=us'
url = "https://www.forexfactory.com"
# Send a GET request to the website
response = requests.get(url)

# Check if the request was successful
if response.status_code == 200:
    # Parse the HTML content using BeautifulSoup
    soup = BeautifulSoup(response.content, 'html.parser')

    # Find all the tables on the page
    # tables = soup.find_all('table')

    table = soup.find_all('table', {"class": "calendar__table  "})[0]

    # Process each table
    if table:
        # Extract table headers
        headers = [header.text for header in table.find_all('th')]
        print('Table Headers:', headers)

        # Extract table rows
        rows = table.find_all('tr')

        # Process each row
        for row in rows:
            # Extract table cells
            cells = row.find_all('td')
            values = [cell.text for cell in cells]
            print('Row Values:', values)

        print('-' * 50)
else:
    print('Error: Unable to retrieve data from the website.')
