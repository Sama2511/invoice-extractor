from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from pydantic import BaseModel
from supabase import create_client, Client
import os
from pydantic import BaseModel, ConfigDict
from ocr import extract_TEXT_from_pdf
from extractor import convert_text_to_json_Ai
from typing import Optional


load_dotenv()

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

supabase: Client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

class Company(BaseModel):
    name: str
    tax_number: str
    address: str

@app.get('/companies')
async def getCompanies():
    try:
        result = supabase.table('company').select('*').execute()
    except Exception:
        raise HTTPException(status_code=500, detail="Something went wrong")
    return {'companies': result.data}


@app.post('/add-company/')
async def addCompany(company: Company):
    try:
        data = supabase.table('company').insert({
            "name": company.name,
            'tax_number': company.tax_number,
            'address': company.address
        }).execute()
    except Exception as e:
        if '23505' in str(e):
            raise HTTPException(status_code=400, detail="Company already exists")
        raise HTTPException(status_code=500, detail="Something went wrong")
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
        if not data.data:
            raise HTTPException(status_code=500, detail="Failed to save invoices")
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Not only information were provided")
    except TypeError as e:
        raise HTTPException(status_code=400, detail='Enter the right information')
    except Exception as e:
        if '23505' in str(e):
            raise HTTPException(status_code=400, detail='Invoice already exists')
        raise HTTPException(status_code=500 , detail="Something went wrong")
    

    return data.data




@app.get("/company/{id}")
async def getCompany(id:str):
    try:
        data = supabase.table('company').select("*").eq("id", id).execute()
        if not data.data:
            raise HTTPException(status_code=404, detail='Company not found')
    except HTTPException:
        raise   
    except Exception:
        raise HTTPException(status_code=500 , detail="Something went wrong")     
    return {'company': data.data}

@app.get("/invoice/{id}")
async def getInvoice(id: str):
    try:
        data = supabase.table('invoices').select('*').eq('id', id).execute()
        if not data.data:
            raise HTTPException(status_code=404, detail='Invoice not found')
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Something went wrong")
    return {'invoice': data.data}

@app.get("/invoices/{company_id}")
async def getInvoices(company_id :str):
    try:
        data = supabase.table('invoices').select('*').eq('company_id',company_id).execute()
        if not data.data:
                raise HTTPException(status_code=404, detail='Invoice not found')
    except HTTPException:
        raise 
    except Exception:
        raise HTTPException(status_code=500 , detail="Something went wrong")
 
    return {"invoice": data.data}


@app.delete('/company/{id}')
async def deleteCompany(id:str):
    try:
        data = supabase.table('company').delete().eq("id", id).execute()
        if not data.data:
            raise HTTPException(status_code=404, detail='Company not found')
    except HTTPException:
        raise  
    except Exception:
        raise HTTPException(status_code=500 , detail="Something went wrong")
    return {'company': data.data}


@app.delete('/invoice/{id}')
async def deleteInvoice(id :str):
    try:
        data = supabase.table('invoices').delete().eq('id',id).execute()
        if not data.data:
                raise HTTPException(status_code=404, detail='Invoice not found')
    except HTTPException:
        raise 
    except Exception:
        raise HTTPException(status_code=500 , detail="Something went wrong")
    return {"invoice": data.data}



class CompanyUpdate(BaseModel):
    name: Optional[str] = None
    tax_number: Optional[str] = None
    address: Optional[str] = None

@app.patch("/company/{id}")
async def editCompany(id: str, details: CompanyUpdate):
    try:
        updates = {}
        for k, v in details.model_dump().items():
            if v is not None:
                updates[k] = v
        if not updates:
            raise HTTPException(status_code=400, detail="No fields provided to update")
        data = supabase.table('company').update(updates).eq('id', id).execute()
        if not data.data:
            raise HTTPException(status_code=404, detail="Company not found")
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Something went wrong")
    return data.data

class InvoiceUpdate(BaseModel):
    invoice_number: Optional[str] = None
    date: Optional[str] = None
    amount_ht: Optional[float] = None
    vat: Optional[float] = None
    amount_ttc: Optional[float] = None

@app.patch("/invoice/{id}")
async def editInvoice(id: str, details: InvoiceUpdate):
    try:
        updates = {}
        for k, v in details.model_dump().items():
            if v is not None:
                updates[k] = v
        if not updates:
            raise HTTPException(status_code=400, detail="No fields provided to update")
        data = supabase.table('invoices').update(updates).eq('id', id).execute()
        if not data.data:
            raise HTTPException(status_code=404, detail="Invoice not found")
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Something went wrong")
    return data.data