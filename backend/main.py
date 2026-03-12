from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from pydantic import BaseModel
from supabase import create_client, Client
import os
from pydantic import BaseModel, ConfigDict
from ocr import extract_TEXT_from_pdf
from extractor import convert_text_to_json_Ai


load_dotenv()

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

supabase: Client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))


@app.get('/companies')
def read_root():
    result = supabase.table('company').select('*').execute()
    return{'companies':result.data}

class Company(BaseModel):
    name: str
    tax_number: str
    address: str
    
@app.post('/add-company/')
async def addCompany(company :Company ):
    data =  supabase.table('company').insert({
        "name": company.name,
        'tax_number':company.tax_number,
        'address': company.address
    }).execute()
    return data.data


@app.post("/uploadPdf")
async def uploadPDF(file: UploadFile):

    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail='File must be a PDF')
    pdf = await file.read()
    try:
        result = extract_TEXT_from_pdf(pdf)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception :
        raise HTTPException(status_code=500, detail="Something went wrong")
    try:
        invoices = convert_text_to_json_Ai(result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail='Something went wrong')
    return {'text':invoices}


class Invoice(BaseModel):
    invoice_number : str
    date : str
    amount_ht : float
    vat: float
    amount_ttc : float

class FullInvoice(BaseModel):
    company_id: str
    invoices: list[Invoice]
    
@app.post("/confirm-invoices")
async def confirmation(dataInvoice : FullInvoice):
    try:
        company_name = supabase.table('company').select('name').eq('id',dataInvoice.company_id ).execute()
        if not company_name.data: 
            raise HTTPException(status_code=404, detail="Company not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException (status_code=500, detail=f"Something went wrong: {str(e)}")
    records = []
    try:
        if not dataInvoice.invoices:
            raise HTTPException(status_code=400, detail='No Invoices Provided')
        for invoice in  dataInvoice.invoices:
            records.append({
                'company_id': dataInvoice.company_id,
                'supplier_name': company_name.data[0]['name'],
                "invoice_number": invoice.invoice_number,
                "invoice_date": invoice.date, 
                "amount_ht":invoice.amount_ht ,
                "vat": invoice.vat,
                "amount_ttc": invoice.amount_ttc 
            })
        data = supabase.table('invoices').insert(records).execute()
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Not only information were provided")
    except TypeError as e:
        raise HTTPException(status_code=400, detail='Enter the right information')
    except Exception:
        raise HTTPException(status_code=500 , detail='Something went wrong')
    

    return data.data





