import pandas as pd
import anthropic
import os

# Read API key from config file
with open(os.path.expanduser('~/Documents/.claude_api_key'), 'r') as f:
    api_key = f.read().strip()

client = anthropic.Anthropic(api_key=api_key)
# Example: Reading a CSV file
df = pd.read_csv('table-1.csv')
csv_content = df.to_string()

# Send as plain text in the message
response = client.messages.create(
    model="claude-opus-4-1-20250805",
    max_tokens=4096,
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": f" Here's the CSV data:\n\n{csv_content}\n\n.\n\nYou are csv file cleaner and your job is to extract data from this csv file and make sure header names are consistent. The file attached is a csv file containing data from a survey of universities that was extracted using amazon textract from a pdf. \n\n There are sometimes more than one tables within this csv. Please combine tables that are similar as amazon automatically separates tables across pages even if they are part of the same table. Hints that the table was split across pages include having a similar number of columns, similar column headers, or the rows preceding in some logical order. \n\n Make sure to note the nested nature of the headers. Create headers that are consistent and imbed all the nested information. Never hallucinate headers that are not there.\n\n Often the total number of columns is given in the header, use that as a guide to check your work. For example, if there are 22 columns in the csv, ensure that there are 22 columns in your output. \n\n Never populate cells that are initially missing in the csv data."
                }
            ]
        }
    ]
)

# Get the response text
response_text = response.content[0].text
print(response_text)

# Save the response to a text file
with open('claude_response.txt', 'w', encoding='utf-8') as f:
    f.write(response_text)

print(f"\nResponse saved to 'claude_response.txt'")