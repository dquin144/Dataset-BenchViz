from fastapi import FastAPI, File, UploadFile
import shutil
import os
import pandas as pd

app = FastAPI()

# Create a directory to store uploaded datasets
UPLOAD_FOLDER = "datasets"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.get("/")
def home():
    return {"message": "Dataset Benchmarking API"}

# Endpoint to upload dataset files
@app.post("/upload/")
async def upload_dataset(file: UploadFile = File(...)):
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    
    # Save the uploaded file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    return {"filename": file.filename, "status": "uploaded"}

# Endpoint to list uploaded datasets
@app.get("/datasets/")
async def list_datasets():
    files = os.listdir(UPLOAD_FOLDER)
    return {"datasets": files}

# Endpoint to get CSV data
@app.get("/dataset/{filename}")
async def get_dataset(filename: str):
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    
    if not os.path.exists(file_path):
        return {"error": "File not found"}
    
    try:
        df = pd.read_csv(file_path)

        df = df.head(100)  # Keep limiting for performance
        
        # Add a row number (like Excel's leftmost index column)
        df.insert(0, "Row #", range(1, len(df) + 1))

        data = df.to_dict(orient="records")
        columns = df.columns.tolist()
        
        return {
            "filename": filename,
            "columns": columns,
            "data": data,
            "total_rows": len(df)
        }
    except Exception as e:
        return {"error": str(e)}