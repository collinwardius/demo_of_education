import anthropic

client = anthropic.Anthropic(api_key="***REMOVED***")
client.beta.files.upload(
    file=("1916_18_table.json", open("/Users/cjwardius/Downloads/bi_survey1916_1918 (1)/analyzeDocResponse.json", "rb"), "application/json"),
)