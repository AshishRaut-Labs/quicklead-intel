"use client";

import { useState } from "react";
import { Search, Download, Globe, Code, FileText, Mail, Phone, Share2, Activity, Loader2, Image as ImageIcon, Layers } from "lucide-react";

export default function QuickLeadDashboard() {
  const [url, setUrl] = useState("");
  const [bulkUrls, setBulkUrls] = useState("");
  const [mode, setMode] = useState<"single" | "bulk">("single");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [data, setData] = useState<any>(null);
  const [bulkData, setBulkData] = useState<any[]>([]);

  const handleScan = async (e: React.FormEvent) => {
    e.preventDefault();
    if (mode === "single") {
      if (!url.trim()) return;
      setLoading(true);
      setError("");
      setData(null);

      try {
        const response = await fetch(`https://quicklead-intel.onrender.com/api/scan?url=${encodeURIComponent(url.trim())}`);
        if (!response.ok) throw new Error("Failed to scan the target URL.");
        
        const result = await response.json();
        setData(result);
      } catch (err: any) {
        setError(err.message || "An unexpected error occurred.");
      } finally {
        setLoading(false);
      }
    } else {
      if (!bulkUrls.trim()) return;
      setLoading(true);
      setError("");
      setBulkData([]);

      const urlList = bulkUrls.split("\n").map(u => u.trim()).filter(Boolean);
      if (urlList.length === 0) {
        setError("Please enter at least one valid URL.");
        setLoading(false);
        return;
      }

      try {
        const response = await fetch(`https://quicklead-intel.onrender.com/api/bulk-scan`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(urlList),
        });
        if (!response.ok) throw new Error("Failed to execute bulk scan.");

        const result = await response.json();
        setBulkData(result.results || []);
      } catch (err: any) {
        setError(err.message || "An unexpected error occurred during bulk scan.");
      } finally {
        setLoading(false);
      }
    }
  };

  const exportCSV = () => {
    if (mode === "single" && data) {
      const csvRows = [
        ["Metric", "Value"],
        ["Title", `"${(data.title || "").replace(/"/g, '""')}"`],
        ["Meta Description", `"${(data.meta_description || "").replace(/"/g, '""')}"`],
        ["H1 Tags", `"${(data.h1_tags || []).join(" | ").replace(/"/g, '""')}"`],
        ["OG Image", `"${data.og_image || "None"}"`],
        ["Emails", `"${(data.emails || []).join(", ")}"`],
        ["Phones", `"${(data.phones || []).join(", ")}"`],
        ["LinkedIn", `"${data.socials?.linkedin || "None"}"`],
        ["Twitter/X", `"${data.socials?.twitter || "None"}"`],
        ["Instagram", `"${data.socials?.instagram || "None"}"`],
        ["Facebook", `"${data.socials?.facebook || "None"}"`],
        ["Facebook Pixel", data.trackers?.facebook_pixel ? "Yes" : "No"],
        ["Google Tag Manager", data.trackers?.google_tag_manager ? "Yes" : "No"],
        ["TikTok Pixel", data.trackers?.tiktok_pixel ? "Yes" : "No"],
        ["HubSpot", data.trackers?.hubspot ? "Yes" : "No"],
        ["Klaviyo", data.trackers?.klaviyo ? "Yes" : "No"],
        ["WordPress", data.tech_stack?.wordpress ? "Yes" : "No"],
        ["Shopify", data.tech_stack?.shopify ? "Yes" : "No"],
        ["Next.js", data.tech_stack?.nextjs ? "Yes" : "No"],
        ["Google Analytics", data.tech_stack?.google_analytics ? "Yes" : "No"],
      ];

      const csvContent = "data:text/csv;charset=utf-8," + csvRows.map(e => e.join(",")).join("\n");
      const encodedUri = encodeURI(csvContent);
      const link = document.createElement("a");
      link.setAttribute("href", encodedUri);
      const domainName = url.replace(/^(?:https?:\/\/)?(?:www\.)?/i, "").split("/")[0] || "scan";
      link.setAttribute("download", `quicklead_intel_${domainName}.csv`);
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    } else if (mode === "bulk" && bulkData.length > 0) {
      const csvRows = [
        ["URL", "Status", "Title", "Meta Description", "Phones", "WordPress", "Shopify", "Next.js", "Google Analytics", "Facebook Pixel", "HubSpot"]
      ];

      bulkData.forEach(item => {
        csvRows.push([
          `"${item.url}"`,
          `"${item.status}"`,
          `"${(item.title || "").replace(/"/g, '""')}"`,
          `"${(item.meta_description || "").replace(/"/g, '""')}"`,
          `"${(item.phones || []).join(", ")}"`,
          item.tech_stack?.wordpress ? "Yes" : "No",
          item.tech_stack?.shopify ? "Yes" : "No",
          item.tech_stack?.nextjs ? "Yes" : "No",
          item.tech_stack?.google_analytics ? "Yes" : "No",
          item.trackers?.facebook_pixel ? "Yes" : "No",
          item.trackers?.hubspot ? "Yes" : "No",
        ]);
      });

      const csvContent = "data:text/csv;charset=utf-8," + csvRows.map(e => e.join(",")).join("\n");
      const encodedUri = encodeURI(csvContent);
      const link = document.createElement("a");
      link.setAttribute("href", encodedUri);
      link.setAttribute("download", `quicklead_intel_bulk_report.csv`);
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }
  };

  return (
    <div className="min-h-screen bg-neutral-950 text-neutral-100 p-8 font-sans">
      <div className="max-w-6xl mx-auto space-y-8">
        
        {/* Header & Mode Selector */}
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 border-b border-neutral-800 pb-6">
          <div>
            <h1 className="text-3xl font-bold flex items-center gap-2">
              <Activity className="text-blue-500" /> QuickLead Intel
            </h1>
            <p className="text-neutral-400 mt-1">AshishRaut-Labs | Competitor & Lead Analysis</p>
          </div>
          
          <div className="flex bg-neutral-900 border border-neutral-800 p-1 rounded-md">
            <button
              onClick={() => { setMode("single"); setBulkData([]); }}
              className={`px-3 py-1.5 rounded text-xs font-medium transition-colors ${mode === "single" ? "bg-blue-600 text-white" : "text-neutral-400 hover:text-white"}`}
            >
              Single Scan
            </button>
            <button
              onClick={() => { setMode("bulk"); setData(null); }}
              className={`px-3 py-1.5 rounded text-xs font-medium transition-colors ${mode === "bulk" ? "bg-blue-600 text-white" : "text-neutral-400 hover:text-white"}`}
            >
              Bulk Scan Engine
            </button>
          </div>
        </div>

        {/* Input Form */}
        <form onSubmit={handleScan} className="bg-neutral-900 border border-neutral-800 p-6 rounded-lg space-y-4">
          {mode === "single" ? (
            <div className="flex flex-col md:flex-row gap-2">
              <div className="relative flex-1">
                <Globe className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-neutral-500" />
                <input 
                  type="text" 
                  placeholder="Enter domain (e.g., example.com)" 
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  className="w-full bg-neutral-950 border border-neutral-800 rounded-md py-2.5 pl-10 pr-4 focus:outline-none focus:border-blue-500 transition-colors text-sm"
                />
              </div>
              <button 
                type="submit" 
                disabled={loading}
                className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2.5 rounded-md flex items-center justify-center gap-2 transition-colors disabled:opacity-50 text-sm font-medium"
              >
                {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
                Scan Target
              </button>
            </div>
          ) : (
            <div className="space-y-3">
              <label className="text-xs text-neutral-400 uppercase tracking-wider flex items-center gap-1.5">
                <Layers className="w-4 h-4 text-blue-400" /> Enter URLs (one per line, up to 50 max)
              </label>
              <textarea
                rows={5}
                placeholder={"example.com\nhubspot.com\nshopify.com"}
                value={bulkUrls}
                onChange={(e) => setBulkUrls(e.target.value)}
                className="w-full bg-neutral-950 border border-neutral-800 rounded-md p-3 focus:outline-none focus:border-blue-500 transition-colors text-sm font-mono"
              />
              <button 
                type="submit" 
                disabled={loading}
                className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2.5 rounded-md flex items-center justify-center gap-2 transition-colors disabled:opacity-50 text-sm font-medium w-full md:w-auto"
              >
                {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
                Run Bulk Batch Scan
              </button>
            </div>
          )}
        </form>

        {error && (
          <div className="bg-red-500/10 border border-red-500/50 text-red-400 p-4 rounded-md text-sm">
            {error}
          </div>
        )}

        {/* Single Scan Results Grid */}
        {mode === "single" && data && (
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
              
              {/* SEO Metadata & Structural Health */}
              <div className="bg-neutral-900 border border-neutral-800 rounded-lg p-6 space-y-4">
                <div className="flex items-center gap-2 text-neutral-400 mb-2">
                  <FileText className="w-5 h-5 text-green-400" />
                  <h3 className="font-medium text-neutral-200">SEO & Structural Health</h3>
                </div>
                <div>
                  <p className="text-xs text-neutral-500 uppercase tracking-wider mb-1">Page Title</p>
                  <p className="text-sm font-medium">{data.title || "No title found"}</p>
                </div>
                <div>
                  <p className="text-xs text-neutral-500 uppercase tracking-wider mb-1">Meta Description</p>
                  <p className="text-sm text-neutral-300 line-clamp-3">{data.meta_description || "No meta description found"}</p>
                </div>
                <div>
                  <p className="text-xs text-neutral-500 uppercase tracking-wider mb-1">H1 Headings</p>
                  {data.h1_tags && data.h1_tags.length > 0 ? (
                    <ul className="space-y-1">
                      {data.h1_tags.map((h1: string, i: number) => (
                        <li key={i} className="text-xs bg-neutral-950 border border-neutral-800 px-2 py-1 rounded text-neutral-300">
                          {h1}
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p className="text-xs text-neutral-500 italic">No H1 tags detected</p>
                  )}
                </div>
                <div>
                  <p className="text-xs text-neutral-500 uppercase tracking-wider mb-1">OpenGraph Image</p>
                  {data.og_image ? (
                    <div className="flex items-center gap-2 bg-neutral-950 border border-neutral-800 p-2 rounded">
                      <ImageIcon className="w-4 h-4 text-green-400 shrink-0" />
                      <a href={data.og_image} target="_blank" rel="noopener noreferrer" className="text-xs text-blue-400 truncate hover:underline">
                        {data.og_image}
                      </a>
                    </div>
                  ) : (
                    <p className="text-xs text-neutral-500 italic">No OG image detected</p>
                  )}
                </div>
              </div>

              {/* Extracted Contacts & Socials */}
              <div className="bg-neutral-900 border border-neutral-800 rounded-lg p-6 space-y-4">
                <div className="flex items-center gap-2 text-neutral-400 mb-2">
                  <Mail className="w-5 h-5 text-purple-400" />
                  <h3 className="font-medium text-neutral-200">Extracted Contacts & Socials</h3>
                </div>

                <div>
                  <p className="text-xs text-neutral-500 uppercase tracking-wider mb-1">Emails</p>
                  {data.emails && data.emails.length > 0 ? (
                    <ul className="space-y-1">
                      {data.emails.map((email: string, i: number) => (
                        <li key={i} className="text-xs bg-neutral-950 border border-neutral-800 px-2 py-1 rounded flex items-center gap-2 text-neutral-300">
                          <Mail className="w-3 h-3 text-purple-400" /> {email}
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p className="text-xs text-neutral-500 italic">No emails detected</p>
                  )}
                </div>

                <div>
                  <p className="text-xs text-neutral-500 uppercase tracking-wider mb-1">Phone Numbers</p>
                  {data.phones && data.phones.length > 0 ? (
                    <ul className="space-y-1">
                      {data.phones.map((phone: string, i: number) => (
                        <li key={i} className="text-xs bg-neutral-950 border border-neutral-800 px-2 py-1 rounded flex items-center gap-2 text-neutral-300">
                          <Phone className="w-3 h-3 text-blue-400" /> {phone}
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p className="text-xs text-neutral-500 italic">No phone numbers detected</p>
                  )}
                </div>

                <div>
                  <p className="text-xs text-neutral-500 uppercase tracking-wider mb-1">Social Profiles</p>
                  <div className="flex flex-wrap gap-2">
                    {data.socials && Object.entries(data.socials).map(([platform, link]: any) => (
                      link ? (
                        <a 
                          key={platform} 
                          href={link} 
                          target="_blank" 
                          rel="noopener noreferrer" 
                          className="text-xs bg-neutral-950 border border-neutral-800 hover:border-neutral-600 px-2.5 py-1 rounded capitalize text-blue-400 transition-colors flex items-center gap-1.5"
                        >
                          <Share2 className="w-3 h-3 text-neutral-400" /> {platform}
                        </a>
                      ) : null
                    ))}
                    {(!data.socials || Object.values(data.socials).every(val => !val)) && (
                      <p className="text-xs text-neutral-500 italic">No social links detected</p>
                    )}
                  </div>
                </div>
              </div>

              {/* Detected Tech Stack */}
              <div className="bg-neutral-900 border border-neutral-800 rounded-lg p-6">
                <div className="flex items-center gap-2 text-neutral-400 mb-4">
                  <Code className="w-5 h-5 text-orange-400" />
                  <h3 className="font-medium text-neutral-200">Detected Tech Stack</h3>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  {data.tech_stack && Object.entries(data.tech_stack).map(([tech, isPresent]: any) => (
                    <div key={tech} className="flex items-center justify-between bg-neutral-950 border border-neutral-800 px-3 py-2 rounded">
                      <span className="text-sm capitalize text-neutral-300">{tech.replace(/_/g, ' ')}</span>
                      <span className={`w-2 h-2 rounded-full ${isPresent ? 'bg-green-500 shadow-sm shadow-green-500/50' : 'bg-neutral-700'}`}></span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Ad Pixels & Trackers */}
              <div className="bg-neutral-900 border border-neutral-800 rounded-lg p-6">
                <div className="flex items-center gap-2 text-neutral-400 mb-4">
                  <Globe className="w-5 h-5 text-yellow-400" />
                  <h3 className="font-medium text-neutral-200">Ad Pixels & Trackers</h3>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  {data.trackers && Object.entries(data.trackers).map(([tracker, isPresent]: any) => (
                    <div key={tracker} className="flex items-center justify-between bg-neutral-950 border border-neutral-800 px-3 py-2 rounded">
                      <span className="text-sm capitalize text-neutral-300">{tracker.replace(/_/g, ' ')}</span>
                      <span className={`w-2 h-2 rounded-full ${isPresent ? 'bg-green-500 shadow-sm shadow-green-500/50' : 'bg-neutral-700'}`}></span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Site Performance */}
              <div className="bg-neutral-900 border border-neutral-800 rounded-lg p-6 md:col-span-2">
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

        {/* Bulk Scan Results Table */}
        {mode === "bulk" && bulkData.length > 0 && (
          <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
            <div className="flex justify-between items-center">
              <h2 className="text-xl font-semibold text-neutral-200">Bulk Batch Intelligence Report</h2>
              <button 
                onClick={exportCSV}
                className="bg-neutral-800 hover:bg-neutral-700 text-white px-4 py-2 rounded-md flex items-center gap-2 transition-colors text-sm"
              >
                <Download className="w-4 h-4" /> Export Bulk CSV
              </button>
            </div>

            <div className="bg-neutral-900 border border-neutral-800 rounded-lg overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="border-b border-neutral-800 bg-neutral-950 text-xs uppercase tracking-wider text-neutral-400">
                      <th className="p-3">Target URL</th>
                      <th className="p-3">Status</th>
                      <th className="p-3">Title</th>
                      <th className="p-3">Tech Stack</th>
                      <th className="p-3">Trackers</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-neutral-800 text-sm">
                    {bulkData.map((item, index) => (
                      <tr key={index} className="hover:bg-neutral-800/50 transition-colors">
                        <td className="p-3 font-medium text-blue-400 truncate max-w-xs">{item.url}</td>
                        <td className="p-3">
                          <span className={`px-2 py-0.5 text-xs rounded font-medium ${item.status === 'Success' ? 'bg-green-500/10 text-green-400' : 'bg-red-500/10 text-red-400'}`}>
                            {item.status}
                          </span>
                        </td>
                        <td className="p-3 text-neutral-300 truncate max-w-xs">{item.title || "N/A"}</td>
                        <td className="p-3">
                          <div className="flex gap-1.5 flex-wrap">
                            {item.tech_stack && Object.entries(item.tech_stack).map(([k, v]) => v ? (
                              <span key={k} className="text-[10px] bg-neutral-950 border border-neutral-800 px-1.5 py-0.5 rounded capitalize text-neutral-300">
                                {k.replace(/_/g, ' ')}
                              </span>
                            ) : null)}
                          </div>
                        </td>
                        <td className="p-3">
                          <div className="flex gap-1.5 flex-wrap">
                            {item.trackers && Object.entries(item.trackers).map(([k, v]) => v ? (
                              <span key={k} className="text-[10px] bg-neutral-950 border border-neutral-800 px-1.5 py-0.5 rounded capitalize text-yellow-400">
                                {k.replace(/_/g, ' ')}
                              </span>
                            ) : null)}
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

      </div>
    </div>
  );
}