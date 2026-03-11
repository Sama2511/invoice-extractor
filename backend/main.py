from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from pydantic import BaseModel
from supabase import create_client, Client
import os
from pydantic import BaseModel, ConfigDict
from ocr import extract_TEXT_from_pdf

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
    except Exception as e:
        raise HTTPException(status_code=500, detail="Something went wrong")

    return {'text':result}




