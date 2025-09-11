import anthropic

client = anthropic.Anthropic(api_key="***REMOVED***")


# Use the file_id with code execution
response = client.beta.messages.create(
    model="claude-opus-4-1-20250805",
    betas=["code-execution-2025-08-25", "files-api-2025-04-14"],
    max_tokens=4096,
    messages=[{
        "role": "user",
        "content": [
            {"type": "text", "text": "You are json file cleaner and your job is to extract data from this json file and make sure header names are consistent. The file attached is a JSON file containing data from a survey of universities that was extracted using amazon textract from a pdf. There are many tables within this json file. Make sure to note the nested nature of the headers. Create headers that are consistent across tables and imbed all the nested information. It is also your job to detect within the document the different tables contained within. Make sure to create different outpput csv's for each of the different tables. Tables of the same type should be appended together, however."},
            {"type": "container_upload", "file_id": "file_011CSy6eM36dcMjN6FrK4vS8.id"}
        ]
    }],
    tools=[{
        "type": "code_execution_20250825",
        "name": "code_execution"
    }]
)