
from openai import OpenAI
import json

client = OpenAI()

def convert_text_to_json_Ai(result):
    try:
        response = client.responses.create(
            model="gpt-4.1-mini",
            input=f'You are an invoice data extractor. Extract the following fields from each invoice in the text below and return a JSON array where each item represents one invoice: [  "invoice_number": "", "date": "", "amount_ht": "", "vat": "", "amount_ttc": ""  ] Return ONLY the JSON array, no extra text. Invoice text: {result}')
        text = response.output[0].content[0].text
        invoices = json.loads(text)
        return invoices
    except json.JSONDecodeError:
        raise ValueError("Invalid JSON returned")
    except Exception as e:
        raise ValueError(f'Extraction failed: {e}')
    

