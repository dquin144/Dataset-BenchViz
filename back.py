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
        # Read the full dataset first to get accurate statistics
        full_df = pd.read_csv(file_path)
        
        # Calculate statistics from the full dataset
        total_rows = len(full_df)
        total_cols = len(full_df.columns)
        missing_values = full_df.isna().sum().sum()
        
        # Get column types
        column_types = {col: str(full_df[col].dtype) for col in full_df.columns}
        
         # Calculate summary statistics for numeric columns
        summary_stats = {}
        numeric_columns = list(full_df.select_dtypes(include=['number']).columns)
        
        for col in numeric_columns:
            summary_stats[col] = {
                'mean': float(full_df[col].mean()),
                'std': float(full_df[col].std()),
                'min': float(full_df[col].min()),
                'max': float(full_df[col].max())
            }
        
        # Now limit to 100 rows for display
        df = full_df.head(100)
        
        # Add a row number (like Excel's leftmost index column)
        df.insert(0, "Row #", range(1, len(df) + 1))

        # Replace NaN with None for proper JSON serialization
        df_json = df.replace({pd.NA: None}).replace({float('nan'): None})

        data = df_json.to_dict(orient="records")
        columns = df.columns.tolist()
        
        return {
            "filename": filename,
            "columns": columns,
            "data": data,
            "total_rows": total_rows,
            "total_cols": total_cols,
            "missing_values": int(missing_values),
            "column_types": column_types,
            "summary_stats": summary_stats,
            "numeric_columns": numeric_columns
        }
    except Exception as e:
        return {"error": str(e)}