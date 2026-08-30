"use client";

import { useState } from "react";
import { Search, Download, Globe, Code, FileText, Mail, Activity, Loader2 } from "lucide-react";

export default function QuickLeadDashboard() {
  const [url, setUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [data, setData] = useState<any>(null);

  const handleScan = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!url) return;

    setLoading(true);
    setError("");
    setData(null);

    try {
      // Updated to point to your live Render backend
      const response = await fetch(`https://quicklead-intel.onrender.com/api/scan?url=${encodeURIComponent(url)}`);
      if (!response.ok) throw new Error("Failed to scan the target URL.");
      
      const result = await response.json();
      setData(result);
    } catch (err: any) {
      setError(err.message || "An unexpected error occurred.");
    } finally {
      setLoading(false);
    }
  };

  const exportCSV = () => {
    if (!data) return;
    
    const csvRows = [
      ["Metric", "Value"],
      ["Title", `"${data.title}"`],
      ["Meta Description", `"${data.meta_description}"`],
      ["Emails", `"${data.emails.join(", ")}"`],
      ["WordPress", data.tech_stack.wordpress ? "Yes" : "No"],
      ["Shopify", data.tech_stack.shopify ? "Yes" : "No"],
      ["Next.js", data.tech_stack.nextjs ? "Yes" : "No"],
      ["Google Analytics", data.tech_stack.google_analytics ? "Yes" : "No"],
    ];

    const csvContent = "data:text/csv;charset=utf-8," + csvRows.map(e => e.join(",")).join("\n");
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `quicklead_intel_${new URL(url.startsWith('http') ? url : `https://${url}`).hostname}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="min-h-screen bg-neutral-950 text-neutral-100 p-8 font-sans">
      <div className="max-w-6xl mx-auto space-y-8">
        
        {/* Header & Search */}
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 border-b border-neutral-800 pb-6">
          <div>
            <h1 className="text-3xl font-bold flex items-center gap-2">
              <Activity className="text-blue-500" /> QuickLead Intel
            </h1>
            <p className="text-neutral-400 mt-1">AshishRaut-Labs | Competitor & Lead Analysis</p>
          </div>
          
          <form onSubmit={handleScan} className="flex w-full md:w-auto gap-2">
            <div className="relative flex-1 md:w-80">
              <Globe className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-neutral-500" />
              <input 
                type="text" 
                placeholder="Enter domain (e.g., example.com)" 
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                className="w-full bg-neutral-900 border border-neutral-800 rounded-md py-2 pl-10 pr-4 focus:outline-none focus:border-blue-500 transition-colors"
              />
            </div>
            <button 
              type="submit" 
              disabled={loading}
              className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md flex items-center gap-2 transition-colors disabled:opacity-50"
            >
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
              Scan
            </button>
          </form>
        </div>

        {error && (
          <div className="bg-red-500/10 border border-red-500/50 text-red-400 p-4 rounded-md">
            {error}
          </div>
        )}

        {/* Dashboard Grid */}
        {data && (
          <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
            <div className="flex justify-between items-center">
              <h2 className="text-xl font-semibold text-neutral-200">Intelligence Report</h2>
              <button 
                onClick={exportCSV}
                className="bg-neutral-800 hover:bg-neutral-700 text-white px-4 py-2 rounded-md flex items-center gap-2 transition-colors text-sm"
              >
                <Download className="w-4 h-4" /> Export CSV
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              
              {/* SEO Metadata */}
              <div className="bg-neutral-900 border border-neutral-800 rounded-lg p-6 space-y-4">
                <div className="flex items-center gap-2 text-neutral-400 mb-2">
                  <FileText className="w-5 h-5 text-green-400" />
                  <h3 className="font-medium text-neutral-200">SEO Metadata</h3>
                </div>
                <div>
                  <p className="text-xs text-neutral-500 uppercase tracking-wider mb-1">Page Title</p>
                  <p className="text-sm font-medium">{data.title || "No title found"}</p>
                </div>
                <div>
                  <p className="text-xs text-neutral-500 uppercase tracking-wider mb-1">Meta Description</p>
                  <p className="text-sm text-neutral-300 line-clamp-3">{data.meta_description || "No meta description found"}</p>
                </div>
              </div>

              {/* Extracted Contacts */}
              <div className="bg-neutral-900 border border-neutral-800 rounded-lg p-6">
                <div className="flex items-center gap-2 text-neutral-400 mb-4">
                  <Mail className="w-5 h-5 text-purple-400" />
                  <h3 className="font-medium text-neutral-200">Extracted Contacts</h3>
                </div>
                {data.emails && data.emails.length > 0 ? (
                  <ul className="space-y-2">
                    {data.emails.map((email: string, i: number) => (
                      <li key={i} className="text-sm bg-neutral-950 border border-neutral-800 px-3 py-2 rounded flex items-center gap-2">
                        <Mail className="w-3 h-3 text-neutral-500" /> {email}
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-sm text-neutral-500 italic">No email addresses detected on the homepage.</p>
                )}
              </div>

              {/* Detected Tech Stack */}
              <div className="bg-neutral-900 border border-neutral-800 rounded-lg p-6">
                <div className="flex items-center gap-2 text-neutral-400 mb-4">
                  <Code className="w-5 h-5 text-orange-400" />
                  <h3 className="font-medium text-neutral-200">Detected Tech Stack</h3>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  {Object.entries(data.tech_stack).map(([tech, isPresent]: any) => (
                    <div key={tech} className="flex items-center justify-between bg-neutral-950 border border-neutral-800 px-3 py-2 rounded">
                      <span className="text-sm capitalize text-neutral-300">{tech.replace('_', ' ')}</span>
                      <span className={`w-2 h-2 rounded-full ${isPresent ? 'bg-green-500' : 'bg-neutral-700'}`}></span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Site Performance */}
              <div className="bg-neutral-900 border border-neutral-800 rounded-lg p-6">
                <div className="flex items-center gap-2 text-neutral-400 mb-4">
                  <Activity className="w-5 h-5 text-blue-400" />
                  <h3 className="font-medium text-neutral-200">Status & Performance</h3>
                </div>
                <div className="flex flex-col justify-center h-full space-y-4 -mt-4">
                  <div className="flex justify-between items-center border-b border-neutral-800 pb-2">
                    <span className="text-sm text-neutral-500">Scan Status</span>
                    <span className="text-sm text-green-400 font-medium">Successful</span>
                  </div>
                  <div className="flex justify-between items-center border-b border-neutral-800 pb-2">
                    <span className="text-sm text-neutral-500">Engine</span>
                    <span className="text-sm text-neutral-300">FastAPI Scraper</span>
                  </div>
                </div>
              </div>

            </div>
          </div>
        )}
      </div>
    </div>
  );
}