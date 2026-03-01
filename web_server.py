import os
import shutil
import subprocess
import glob
from pathlib import Path
from fastapi import FastAPI, File, UploadFile, Form, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# FastAPI App Setting
app = FastAPI(title="SSD Engineering Library")

# Enable CORS for frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Constants & Paths
BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "source_doc" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Mount statics (for UI dashboard)
# Ensure the folder exists to avoid startup errors
(BASE_DIR / "web_server" / "static").mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "web_server" / "static")), name="static")

# Define existing library directory (Hardcoded as requested, but can be overridden)
EXISTING_LIBRARY_DIR = Path(os.environ.get("DOC_LIBRARY_PATH", "/home/wscho/Documents/SSD_DOC2"))
EXISTING_LIBRARY_DIR.mkdir(parents=True, exist_ok=True)

# Mount SSD docs to serve existing output HTML
app.mount("/SSD_DOC2", StaticFiles(directory=str(EXISTING_LIBRARY_DIR)), name="SSD_DOC2")

# In-memory status tracking for pipeline jobs
job_status = {}  # { "job_id": { "status": "running|done|error", "message": "...", "output_dir": "..." } }

# ---------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------

def run_pipeline_task(job_id: str, pdf_path: str, output_dir: str, custom_prompt: str, merge_depth: int):
    """Background task to run the step1 ~ step8 pipeline."""
    job_status[job_id] = {"status": "running", "message": "Starting pipeline...", "step": "Init"}
    
    # Define steps dynamically to mirror run_batch_pipeline.py
    steps = [
        "step1_layout_analyzer.py",
        "step2_section_extractor.py",
        "step3_image_generator.py",
        "step4_llm_parser.py",
        "step5_markdown_converter.py",
        "step6_db_migration.py",
        "step7_summary_generator.py",
        "step8_web_viewer_generator.py"
    ]
    
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    env["PDF_PATH"] = pdf_path
    env["OUTPUT_DIR"] = output_dir
    # Inject user prompt! (Will be read correctly by modified step7/llm scripts if implemented)
    env["USER_CUSTOM_PROMPT"] = custom_prompt
    env["MERGE_DEPTH_THRESHOLD"] = str(merge_depth)
    
    try:
        for idx, step in enumerate(steps, 1):
            job_status[job_id]["message"] = f"Running {step}..."
            job_status[job_id]["step"] = f"{idx}/{len(steps)}: {step}"
            print(f"[JOB {job_id}] Executing: {step}")
            
            # Execute the python script synchronously in a subprocess
            subprocess.run(
                ["python", step], 
                env=env, 
                cwd=str(BASE_DIR),
                check=True
            )
            
        job_status[job_id]["status"] = "done"
        job_status[job_id]["message"] = "Pipeline completed successfully!"
        # Return the path to the dynamically generated index.html
        job_status[job_id]["url"] = f"/SSD_DOC2/{Path(output_dir).name}/summary_html/index.html"
        
    except subprocess.CalledProcessError as e:
        print(f"[JOB {job_id}] Pipeline Failed at step: {e}")
        job_status[job_id]["status"] = "error"
        job_status[job_id]["message"] = f"Error during execution."

# ---------------------------------------------------------
# API Endpoints
# ---------------------------------------------------------

@app.post("/api/upload")
async def upload_pdf(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    prompt: str = Form(""),
    merge_depth: int = Form(4),
):
    """Handles PDF file upload and triggers background pipeline."""
    if not file.filename.endswith('.pdf'):
        return JSONResponse(status_code=400, content={"error": "Only PDF files are allowed."})
    
    # 1. Save uploaded file securely
    file_path = UPLOAD_DIR / file.filename
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # 2. Define Output Directory in the EXISTING_LIBRARY_DIR
    # Folder name: Clean filename + simple timestamp 
    import time
    clean_name = file.filename.replace('.pdf', '').replace(' ', '_')
    folder_name = f"o_upload_{clean_name}_{int(time.time())}"
    output_dir = EXISTING_LIBRARY_DIR / folder_name
    
    # 3. Create job ID
    job_id = folder_name
    
    # 4. Add to background tasks to prevent blocking
    background_tasks.add_task(
        run_pipeline_task, 
        job_id=job_id, 
        pdf_path=str(file_path), 
        output_dir=str(output_dir), 
        custom_prompt=prompt,
        merge_depth=merge_depth
    )
    
    return {"status": "success", "job_id": job_id, "message": "Upload successful, pipeline started."}


@app.get("/api/status/{job_id}")
async def get_status(job_id: str):
    """Check the status of a specific background job."""
    if job_id not in job_status:
        return JSONResponse(status_code=404, content={"error": "Job not found"})
    return job_status[job_id]


@app.get("/api/library")
async def list_library():
    """Scans the EXISTING_LIBRARY_DIR directory and returns available documents."""
    libraries = []
    
    if EXISTING_LIBRARY_DIR.exists():
        # Look for summary.json inside each subfolder's summary_html/data directory
        # OR just list folders that have a summary_html/index.html
        folders = [f for f in EXISTING_LIBRARY_DIR.iterdir() if f.is_dir()]
        
        # Sort folders by modification time (newest first)
        folders.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        for folder in folders:
            index_path = folder / "summary_html" / "index.html"
            summary_json = folder / "summary_html" / "data" / "summary.json"
            
            if index_path.exists():
                doc_title = folder.name
                
                # Attempt to read exact document title from summary.json
                if summary_json.exists():
                    try:
                        with open(summary_json, "r") as f:
                            data = json.load(f)
                            if "title" in data:
                                doc_title = data["title"]
                    except:
                        pass
                
                libraries.append({
                    "id": folder.name,
                    "title": doc_title.replace("o_", "").replace("_", " ").title(),
                    "folder_name": folder.name,
                    "url": f"/SSD_DOC2/{folder.name}/summary_html/index.html"
                })
                
    return {"documents": libraries}


@app.get("/", response_class=HTMLResponse)
async def serve_dashboard():
    """Serves the main frontend dashboard (HTML)."""
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>SSD Engineering Library Dashboard</title>
        <script src="https://unpkg.com/vue@3"></script>
        <script src="https://cdn.tailwindcss.com"></script>
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        <style>
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f3f4f6; }
            .drop-zone { border: 2px dashed #9ca3af; transition: all 0.3s ease; }
            .drop-zone.dragover { border-color: #3b82f6; background-color: #eff6ff; }
            .glass-panel { background: rgba(255, 255, 255, 0.95); backdrop-filter: blur(10px); }
        </style>
    </head>
    <body class="text-gray-800">
        <div id="app" class="min-h-screen flex flex-col">
            <!-- Navbar -->
            <nav class="bg-indigo-700 text-white shadow-md p-4 flex justify-between items-center">
                <div class="flex items-center space-x-3">
                    <i class="fas fa-microchip text-2xl"></i>
                    <h1 class="text-xl font-bold tracking-wider">SSD Engineering Library</h1>
                </div>
                <div class="text-indigo-200 text-sm">Automated Spec Parsing AI</div>
            </nav>

            <!-- Main Content -->
            <main class="flex-1 max-w-7xl w-full mx-auto p-6 flex flex-col lg:flex-row gap-8">
                
                <!-- Left: Upload Section -->
                <div class="lg:w-1/3 flex flex-col gap-6">
                    <div class="glass-panel rounded-xl shadow-lg p-6 border border-gray-100">
                        <h2 class="text-lg font-bold mb-4 text-indigo-900 border-b pb-2"><i class="fas fa-cloud-upload-alt mr-2"></i>Upload New Spec</h2>
                        
                        <!-- Drag & Drop Zone -->
                        <div 
                            class="drop-zone relative bg-gray-50 rounded-lg p-8 text-center cursor-pointer mb-5"
                            :class="{ 'dragover': isDragging }"
                            @dragover.prevent="isDragging = true"
                            @dragleave.prevent="isDragging = false"
                            @drop.prevent="handleDrop"
                            @click="$refs.fileInput.click()">
                            
                            <input type="file" ref="fileInput" class="hidden" accept=".pdf" @change="handleFileSelect">
                            
                            <div v-if="!selectedFile">
                                <i class="fas fa-file-pdf text-4xl text-gray-400 mb-3"></i>
                                <p class="text-sm text-gray-600 font-medium">Drag & drop your PDF spec here</p>
                                <p class="text-xs text-gray-400 mt-1">or click to browse from computer</p>
                            </div>
                            
                            <div v-else class="text-indigo-600">
                                <i class="fas fa-file-check text-4xl mb-2"></i>
                                <p class="font-bold truncate px-4">{{ selectedFile.name }}</p>
                                <p class="text-xs text-gray-500 mt-1">({{ (selectedFile.size / 1024 / 1024).toFixed(2) }} MB)</p>
                            </div>
                        </div>

                        <!-- Prompt Input -->
                        <div class="mb-5">
                            <label class="block text-sm font-semibold text-gray-700 mb-2">Custom Analysis Prompt (Optional)</label>
                            <textarea 
                                v-model="promptText" 
                                rows="3" 
                                class="w-full border border-gray-300 rounded-md p-3 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 transition shadow-inner"
                                placeholder="E.g., Extract all power requirements in detail. Focus heavily on state transition timings..."></textarea>
                            <p class="text-[11px] text-gray-400 mt-1"><i class="fas fa-info-circle"></i> This prompt will be injected into the LLM during generation step.</p>
                        </div>

                        <!-- Merge Depth Input -->
                        <div class="mb-5">
                            <label class="block text-sm font-semibold text-gray-700 mb-2">Summary Merge Depth Threshold <span class="text-xs text-gray-500 font-normal ml-2">(Default: 4)</span></label>
                            <input type="number" 
                                v-model.number="mergeDepth" 
                                min="1" max="10" 
                                class="w-full border border-gray-300 rounded-md p-3 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 transition shadow-inner"
                            >
                            <p class="text-[11px] text-gray-400 mt-1"><i class="fas fa-info-circle"></i> E.g., Depth 4 will merge sub-sections like 1.1.1.1 into 1.1 automatically.</p>
                        </div>

                        <!-- Upload Button -->
                        <button 
                            @click="uploadDocument" 
                            :disabled="!selectedFile || isProcessing"
                            class="w-full py-3 rounded-lg font-bold text-white transition shadow-md disabled:opacity-50 disabled:cursor-not-allowed"
                            :class="isProcessing ? 'bg-indigo-400' : 'bg-indigo-600 hover:bg-indigo-700 active:transform active:scale-95'">
                            <span v-if="!isProcessing"><i class="fas fa-cogs mr-2"></i>Start General Parsing Pipeline</span>
                            <span v-else><i class="fas fa-spinner fa-spin mr-2"></i>Initializing...</span>
                        </button>
                    </div>

                    <!-- Status Tracker Box -->
                    <div v-if="currentJobId" class="glass-panel rounded-xl shadow-md p-5 border-l-4" :class="statusBorderColor">
                        <div class="flex justify-between items-center mb-2">
                            <h3 class="font-bold text-gray-800 text-sm">Pipeline Status</h3>
                            <span class="text-xs font-semibold px-2 py-1 rounded-full" :class="statusBadgeClass">{{ jobStatus }}</span>
                        </div>
                        <p class="text-xs text-gray-500 mb-1 font-mono truncate" :title="currentJobId">Job: {{ currentJobId }}</p>
                        <p class="text-sm font-medium text-indigo-700 mt-2"><i class="fas fa-terminal mr-2"></i>{{ jobMessage }}</p>
                        <div v-if="jobStep" class="w-full bg-gray-200 rounded-full h-1.5 mt-3">
                            <div class="bg-indigo-600 h-1.5 rounded-full" :style="{ width: progressPercentage + '%' }"></div>
                        </div>
                        <div v-if="jobResultUrl" class="mt-4">
                            <a :href="jobResultUrl" target="_blank" class="block w-full text-center bg-green-500 hover:bg-green-600 text-white font-bold py-2 rounded text-sm transition">
                                <i class="fas fa-external-link-alt mr-1"></i> Open Processed Document
                            </a>
                        </div>
                    </div>
                </div>

                <!-- Right: Library Grid -->
                <div class="lg:w-2/3 flex flex-col">
                    <div class="flex justify-between items-baseline mb-4 border-b pb-2">
                        <h2 class="text-2xl font-bold text-gray-800"><i class="fas fa-book-open text-indigo-500 mr-2"></i>Existing Documents</h2>
                        <button @click="fetchLibrary" class="text-sm text-indigo-600 hover:text-indigo-800"><i class="fas fa-sync-alt mr-1"></i>Refresh</button>
                    </div>
                    
                    <div v-if="isLoadingLibrary" class="flex justify-center py-20">
                        <i class="fas fa-spinner fa-spin text-4xl text-indigo-300"></i>
                    </div>
                    
                    <div v-else-if="libraryDocs.length === 0" class="text-center py-20 text-gray-400 bg-white rounded-xl shadow-sm border border-dashed border-gray-300">
                        <i class="fas fa-folder-open text-5xl mb-3 text-gray-300"></i>
                        <p>Document library is empty.</p>
                        <p class="text-sm">Upload a PDF to get started.</p>
                    </div>
                    
                    <div v-else class="grid grid-cols-1 md:grid-cols-2 gap-5 overflow-y-auto pb-10">
                        <div v-for="doc in libraryDocs" :key="doc.id" 
                            class="bg-white rounded-xl shadow border border-gray-100 p-5 hover:shadow-lg transition group relative overflow-hidden flex flex-col justify-between">
                            
                            <div class="absolute top-0 left-0 w-1 h-full bg-indigo-500"></div>
                            
                            <div>
                                <div class="flex justify-between items-start mb-2">
                                    <h3 class="font-bold text-gray-900 group-hover:text-indigo-700 transition line-clamp-2 leading-snug">{{ doc.title }}</h3>
                                    <span class="bg-blue-50 text-blue-700 text-[10px] font-bold px-2 py-0.5 rounded ml-2 whitespace-nowrap"><i class="fas fa-check-circle mr-1"></i>Parsed</span>
                                </div>
                                <p class="text-xs text-gray-400 font-mono mb-4 truncate text-ellipsis overflow-hidden">/SSD_DOC2/{{ doc.folder_name }}</p>
                            </div>
                            
                            <div class="mt-auto">
                                <a :href="doc.url" target="_blank" class="inline-block px-4 py-2 bg-indigo-50 hover:bg-indigo-100 text-indigo-700 text-sm font-semibold rounded transition w-full text-center border border-indigo-100">
                                    View Web Dashboard <i class="fas fa-arrow-right ml-1"></i>
                                </a>
                            </div>
                        </div>
                    </div>
                </div>
            </main>
        </div>

        <script>
            const { createApp } = Vue

            createApp({
                data() {
                    return {
                        isDragging: false,
                        selectedFile: null,
                        promptText: '',
                        mergeDepth: 4,
                        isProcessing: false,
                        
                        // Status Tracking
                        currentJobId: null,
                        jobStatus: '',
                        jobMessage: '',
                        jobStep: '',
                        jobResultUrl: null,
                        statusInterval: null,
                        
                        // Library
                        libraryDocs: [],
                        isLoadingLibrary: false
                    }
                },
                computed: {
                    statusBorderColor() {
                        if (this.jobStatus === 'done') return 'border-green-500';
                        if (this.jobStatus === 'error') return 'border-red-500';
                        return 'border-indigo-500';
                    },
                    statusBadgeClass() {
                        if (this.jobStatus === 'done') return 'bg-green-100 text-green-800';
                        if (this.jobStatus === 'error') return 'bg-red-100 text-red-800';
                        return 'bg-yellow-100 text-yellow-800 animate-pulse';
                    },
                    progressPercentage() {
                        if (this.jobStatus === 'done') return 100;
                        if (!this.jobStep) return 5;
                        
                        // Parse step info e.g., "1/8: step1_layout_analyzer.py"
                        const match = this.jobStep.match(/(\d+)\/(\d+)/);
                        if (match) {
                            const cur = parseInt(match[1]);
                            const total = parseInt(match[2]);
                            return Math.floor((cur / total) * 100);
                        }
                        return 10;
                    }
                },
                mounted() {
                    this.fetchLibrary();
                },
                beforeUnmount() {
                    if (this.statusInterval) clearInterval(this.statusInterval);
                },
                methods: {
                    handleDragOver(e) {
                        e.preventDefault();
                        this.isDragging = true;
                    },
                    handleDragLeave(e) {
                        e.preventDefault();
                        this.isDragging = false;
                    },
                    handleDrop(e) {
                        e.preventDefault();
                        this.isDragging = false;
                        if (e.dataTransfer.files.length > 0) {
                            this.setFile(e.dataTransfer.files[0]);
                        }
                    },
                    handleFileSelect(e) {
                        if (e.target.files.length > 0) {
                            this.setFile(e.target.files[0]);
                        }
                    },
                    setFile(file) {
                        if (file.type !== 'application/pdf' && !file.name.toLowerCase().endsWith('.pdf')) {
                            alert("Only PDF files are supported.");
                            return;
                        }
                        this.selectedFile = file;
                    },
                    async uploadDocument() {
                        if (!this.selectedFile) return;
                        
                        this.isProcessing = true;
                        this.currentJobId = null;
                        this.jobResultUrl = null;
                        this.jobStatus = 'uploading';
                        this.jobMessage = "Uploading PDF securely...";
                        this.jobStep = '';
                        
                        const formData = new FormData();
                        formData.append('file', this.selectedFile);
                        formData.append('prompt', this.promptText);
                        formData.append('merge_depth', this.mergeDepth);
                        
                        try {
                            const response = await fetch('/api/upload', {
                                method: 'POST',
                                body: formData
                            });
                            
                            const data = await response.json();
                            
                            if (response.ok) {
                                this.currentJobId = data.job_id;
                                this.jobStatus = 'running';
                                this.jobMessage = "Upload Complete. Pipeline initiated in background.";
                                
                                // Start Polling Status
                                this.pollStatus();
                            } else {
                                this.jobStatus = 'error';
                                this.jobMessage = data.error || "Upload failed.";
                                this.isProcessing = false;
                            }
                        } catch (err) {
                            console.error(err);
                            this.jobStatus = 'error';
                            this.jobMessage = "Network error occurred.";
                            this.isProcessing = false;
                        }
                    },
                    pollStatus() {
                        if (this.statusInterval) clearInterval(this.statusInterval);
                        
                        this.statusInterval = setInterval(async () => {
                            try {
                                const res = await fetch('/api/status/' + this.currentJobId);
                                if (res.ok) {
                                    const data = await res.json();
                                    this.jobStatus = data.status;
                                    this.jobMessage = data.message;
                                    this.jobStep = data.step || '';
                                    
                                    if (data.status === 'done') {
                                        this.jobResultUrl = data.url;
                                        this.isProcessing = false;
                                        clearInterval(this.statusInterval);
                                        // Refresh library list
                                        setTimeout(() => this.fetchLibrary(), 1000);
                                    } else if (data.status === 'error') {
                                        this.isProcessing = false;
                                        clearInterval(this.statusInterval);
                                    }
                                }
                            } catch (e) {
                                console.error("Error fetching status", e);
                            }
                        }, 2000); // Poll every 2 seconds
                    },
                    async fetchLibrary() {
                        this.isLoadingLibrary = true;
                        try {
                            const res = await fetch('/api/library');
                            if (res.ok) {
                                const data = await res.json();
                                this.libraryDocs = data.documents;
                            }
                        } catch (e) {
                            console.error("Failed to fetch library", e);
                        } finally {
                            this.isLoadingLibrary = false;
                        }
                    }
                }
            }).mount('#app')
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

if __name__ == "__main__":
    import uvicorn
    os.environ["DOC_LIBRARY_PATH"] = '/home/wscho/Documents/SSD_DOC2' #기존에 매뉴얼로 생성된 결과가 있는 위치
    # Execute with: python web_server.py
    print(f"Server starting on http://0.0.0.0:8000")
    print(f"Mounting target existing library to: {EXISTING_LIBRARY_DIR}")
    uvicorn.run(app, host="0.0.0.0", port=8000)
