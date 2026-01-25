import os
import shutil
import json
from pathlib import Path
from common_parameter import OUTPUT_DIR

class WebViewerGenerator:
    def __init__(self):
        self.src_static = Path("ssd_eng_library/static")
        self.out_base = Path(OUTPUT_DIR) / "summary_html"
        self.out_static = self.out_base / "static"
        
    def setup_directories(self):
        self.out_base.mkdir(parents=True, exist_ok=True)
        self.out_static.mkdir(parents=True, exist_ok=True)
        
    def copy_assets(self):
        """Copy Vue, Tailwind and other assets"""
        assets = ["vue.global.js", "tailwindcss.js"]
        for asset in assets:
            src = self.src_static / asset
            dst = self.out_static / asset
            if src.exists():
                shutil.copy(src, dst)
                print(f"Copied {asset}")
            else:
                # Fallback: Download from CDN if not local?
                # For now assume they exist as per user context
                print(f"Warning: {asset} not found in {self.src_static}")

    def create_index_html(self):
        """Create the main index.html"""
        
        html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SSD Spec Viewer - Summary & Original</title>
    <!-- Vue.js -->
    <script src="static/vue.global.js"></script>
    <script src="static/tailwindcss.js"></script>
    <!-- Marked for Markdown Rendering -->
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <!-- Google Fonts -->
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        body { font-family: 'Inter', sans-serif; }
        .tree-node { margin-left: 1.2rem; border-left: 1px solid #e5e7eb; }
        .tree-content { padding: 4px 8px; cursor: pointer; border-radius: 4px; display: flex; align-items: center; }
        .tree-content:hover { background-color: #f3f4f6; }
        .tree-content.active { background-color: #dbeafe; color: #1e40af; font-weight: 500; }
        .folder-icon { width: 16px; text-align: center; margin-right: 4px; color: #9ca3af; font-size: 0.8rem; }
        .markdown-body { font-size: 0.9rem; line-height: 1.6; color: #374151; }
        .markdown-body h1, .markdown-body h2 { color: #111827; font-weight: 700; margin-top: 1.5em; margin-bottom: 0.5em; }
        .markdown-body h1 { font-size: 1.5em; border-bottom: 1px solid #e5e7eb; padding-bottom: 0.3em; }
        .markdown-body h2 { font-size: 1.25em; }
        .markdown-body p { margin-bottom: 1em; }
        .markdown-body ul { list-style-type: disc; padding-left: 1.5em; margin-bottom: 1em; }
        .markdown-body pre { background: #f3f4f6; padding: 1em; border-radius: 0.5em; overflow-x: auto; }
        .markdown-body code { background: #f3f4f6; padding: 0.2em 0.4em; border-radius: 0.25em; font-family: monospace; font-size: 0.85em; }
    </style>
</head>
<body class="bg-gray-50 h-screen flex flex-col text-sm text-gray-800">

    <div id="app" class="flex h-full overflow-hidden">
        
        <!-- Sidebar -->
        <div class="w-80 bg-white border-r flex flex-col shadow-sm z-10">
            <div class="p-4 border-b bg-gray-50">
                <h1 class="font-bold text-lg text-indigo-700">Spec Library</h1>
                <p class="text-xs text-gray-500 mt-1">Summary & Original Viewer</p>
            </div>
            
            <div class="p-2 border-b">
                <input type="text" v-model="searchQuery" placeholder="Search sections..." 
                    class="w-full px-3 py-1.5 border rounded-md text-sm focus:outline-none focus:ring-1 focus:ring-indigo-500">
            </div>

            <div class="flex-1 overflow-y-auto p-2">
                <tree-item v-for="item in filteredSections" :key="item.id" :item="item" :active-id="currentSectionId" @select="selectSection"></tree-item>
            </div>
        </div>

        <!-- Main Content -->
        <div class="flex-1 flex flex-col overflow-hidden relative">
            <header class="bg-white border-b h-14 flex items-center px-6 justify-between flex-shrink-0">
                <h2 v-if="currentSection" class="text-lg font-semibold truncate">{{ currentSection.id }} {{ currentSection.title }}</h2>
                <div v-if="currentSection" class="text-xs text-indigo-600 bg-indigo-50 px-2 py-1 rounded border border-indigo-100">
                    Depth: {{ currentSection.depth }}
                </div>
            </header>

            <main class="flex-1 overflow-y-auto p-8 bg-white max-w-5xl mx-auto w-full shadow-sm m-4 rounded-lg">
                <div v-if="!currentSection" class="text-center py-20 text-gray-400">
                    Select a section from the left to view summary and original content.
                </div>
                
                <div v-else class="space-y-12">
                    <!-- Summary Section -->
                    <section class="bg-blue-50 p-6 rounded-xl border border-blue-100">
                        <div class="flex items-center mb-4">
                            <span class="bg-blue-600 text-white text-xs font-bold px-2 py-1 rounded mr-2">SUMMARY</span>
                            <h3 class="text-lg font-semibold text-blue-900">AI Generated Summary</h3>
                        </div>
                        <div class="markdown-body" v-html="renderMarkdown(currentSection.summary)"></div>
                    </section>

                    <!-- Original Content Link/Preview -->
                    <section class="pt-8 border-t">
                        <div class="flex items-center mb-4">
                            <span class="bg-gray-600 text-white text-xs font-bold px-2 py-1 rounded mr-2">ORIGINAL</span>
                            <h3 class="text-lg font-semibold text-gray-900">Source Content</h3>
                        </div>
                        
                        <div v-if="currentSection.sub_sections && currentSection.sub_sections.length > 0" class="mb-4 text-xs text-gray-500">
                            Includes content from: {{ currentSection.sub_sections.join(', ') }}
                        </div>

                        <!-- We will load the original markdown dynamically or just show file path for now since step7 didn't embed full ori text in json -->
                        <!-- Update: Let's assume we want to show it. We can fetch the .md file if served via simple http server -->
                        <div class="p-4 border rounded bg-gray-50 text-gray-600">
                             <p class="mb-2">Original File: <strong>{{ currentSection.original_md_file }}</strong></p>
                             <div class="flex gap-2">
                                <a :href="'../section_markdown/' + currentSection.original_md_file" target="_blank" class="text-indigo-600 hover:underline">Open Raw Markdown</a>
                             </div>
                        </div>
                    </section>
                </div>
            </main>
        </div>
    </div>

    <script>
        const TreeItem = {
            name: 'TreeItem',
            props: ['item', 'activeId'],
            emits: ['select'],
            data() { return { isOpen: this.item.depth < 2 } }, // Default open for top levels
            template: `
                <div class="mb-0.5">
                    <div class="tree-content select-none" :class="{ 'active': activeId === item.id }" @click="handleClick">
                        <span @click.stop="toggle" class="folder-icon cursor-pointer w-4 h-4 flex items-center justify-center rounded hover:bg-gray-200 mr-1.5 transition-colors">
                            {{ item.children && item.children.length ? (isOpen ? '▼' : '▶') : '•' }}
                        </span>
                        <div class="truncate">
                            <span class="font-mono text-[10px] text-gray-500 mr-1.5">{{ item.id }}</span>
                            <span>{{ item.title }}</span>
                        </div>
                    </div>
                    <div v-if="isOpen && item.children && item.children.length" class="tree-node">
                        <tree-item v-for="child in item.children" :key="child.id" :item="child" :active-id="activeId" @select="$emit('select', $event)"></tree-item>
                    </div>
                </div>
            `,
            methods: {
                toggle() { if (this.item.children && this.item.children.length) this.isOpen = !this.isOpen; },
                handleClick() { this.$emit('select', this.item); }
            }
        };

        const { createApp } = Vue;

        createApp({
            components: { TreeItem },
            data() {
                return {
                    sections: [],         // Flat list from JSON
                    rootSections: [],     // Tree structure
                    searchQuery: '',
                    currentSection: null,
                    currentSectionId: null
                }
            },
            computed: {
                filteredSections() {
                    // If search logic needed, implement here. For now return tree.
                    if (!this.searchQuery) return this.rootSections;
                    // Simple search filtering is complex in tree. 
                    // Just return root for now or implement flatten search.
                    return this.rootSections; 
                }
            },
            mounted() {
                this.loadData();
            },
            methods: {
                async loadData() {
                    try {
                        const res = await fetch('data/summary.json');
                        const data = await res.json();
                        this.sections = data;
                        this.buildTree(data);
                    } catch (e) {
                        console.error("Failed to load summary.json", e);
                    }
                },
                buildTree(data) {
                    const map = {};
                    data.forEach(s => {
                        s.children = [];
                        map[s.id] = s;
                    });
                    
                    const roots = [];
                    data.forEach(s => {
                        // Find parent ID (e.g. 1.1 -> 1, 1.1.1 -> 1.1)
                        if (s.id.includes('.')) {
                            const parentId = s.id.substring(0, s.id.lastIndexOf('.'));
                            if (map[parentId]) {
                                map[parentId].children.push(s);
                            } else {
                                roots.push(s); // Parent missing or top level logic mismatch
                            }
                        } else {
                            roots.push(s);
                        }
                    });
                    this.rootSections = roots;
                },
                selectSection(item) {
                    this.currentSection = item;
                    this.currentSectionId = item.id;
                },
                renderMarkdown(text) {
                    return marked.parse(text || '');
                }
            }
        }).mount('#app');
    </script>
</body>
</html>
        """
        
        with open(self.out_base / "index.html", 'w', encoding='utf-8') as f:
            f.write(html_content)
        print("Created index.html")

    def process(self):
        self.setup_directories()
        self.copy_assets()
        self.create_index_html()
        print(f"Web Viewer generated at: {self.out_base.absolute()}")

if __name__ == "__main__":
    gen = WebViewerGenerator()
    gen.process()
