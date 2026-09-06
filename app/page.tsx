// Hybrid Dashboard Active
"use client";

import { useState } from "react";
import { 
  Search, Download, Globe, Code, FileText, Mail, Phone, Share2, 
  Activity, Loader2, Image as ImageIcon, Layers, AlertCircle, 
  TrendingUp, DollarSign, MessageSquare, Zap
} from "lucide-react";

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

  const getScoreColor = (score: number) => {
    if (score >= 80) return "text-green-400";
    if (score >= 50) return "text-yellow-400";
    return "text-red-400";
  };

  const exportCSV = () => {
    if (mode === "single" && data) {
      const intel = data.intelligence || {};
      const csvRows = [
        ["Metric", "Value"],
        // Sales Intel
        ["Website Score", intel.website_score || "N/A"],
        ["Opportunity Score", intel.opportunity_score || "N/A"],
        ["Suggested Offer", `"${intel.suggested_offer || "N/A"}"`],
        ["Suggested Price", `"${intel.suggested_price || "N/A"}"`],
        ["Problems Found", `"${(intel.problems_found || []).join(" | ")}"`],
        ["Personalized Pitch", `"${(intel.personalized_pitch || "").replace(/"/g, '""')}"`],
        // Raw Data
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
        ["WordPress", data.tech_stack?.wordpress ? "Yes" : "No"],
        ["Shopify", data.tech_stack?.shopify ? "Yes" : "No"],
        ["Next.js", data.tech_stack?.nextjs ? "Yes" : "No"],
        ["Google Analytics", data.trackers?.google_analytics ? "Yes" : "No"],
        ["Facebook Pixel", data.trackers?.facebook_pixel ? "Yes" : "No"],
        ["HubSpot", data.trackers?.hubspot ? "Yes" : "No"],
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
        [
          "URL", "Status", "Business Name", "Website Score", "Opportunity", 
          "Problems Found", "Suggested Offer", "Suggested Price", "Pitch",
          "Phones", "Emails", "LinkedIn", "WordPress", "Shopify", "Google Analytics", "Facebook Pixel"
        ]
      ];

      bulkData.forEach(item => {
        if (item.status === "Success") {
          const intel = item.intelligence || {};
          csvRows.push([
            `"${item.url}"`,
            `"${item.status}"`,
            `"${(item.title || "").replace(/"/g, '""')}"`,
            intel.website_score || 0,
            `"${intel.opportunity_score || "UNKNOWN"}"`,
            `"${(intel.problems_found || []).join(" | ")}"`,
            `"${intel.suggested_offer || ""}"`,
            `"${intel.suggested_price || ""}"`,
            `"${(intel.personalized_pitch || "").replace(/"/g, '""')}"`,
            `"${(item.phones || []).join(", ")}"`,
            `"${(item.emails || []).join(", ")}"`,
            `"${item.socials?.linkedin || ""}"`,
            item.tech_stack?.wordpress ? "Yes" : "No",
            item.tech_stack?.shopify ? "Yes" : "No",
            item.trackers?.google_analytics ? "Yes" : "No",
            item.trackers?.facebook_pixel ? "Yes" : "No"
          ]);
        } else {
          csvRows.push([`"${item.url}"`, "Failed", "", "", "", "", "", "", "", "", "", "", "", "", "", ""]);
        }
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
              <Zap className="text-blue-500 fill-blue-500/20" /> QuickLead Intel
            </h1>
            <p className="text-neutral-400 mt-1">AshishRaut-Labs | Sales Intelligence Engine</p>
          </div>
          
          <div className="flex bg-neutral-900 border border-neutral-800 p-1 rounded-md">
            <button
              onClick={() => { setMode("single"); setBulkData([]); }}
              className={`px-3 py-1.5 rounded text-xs font-medium transition-colors ${mode === "single" ? "bg-blue-600 text-white" : "text-neutral-400 hover:text-white"}`}
            >
              Single Intel
            </button>
            <button
              onClick={() => { setMode("bulk"); setData(null); }}
              className={`px-3 py-1.5 rounded text-xs font-medium transition-colors ${mode === "bulk" ? "bg-blue-600 text-white" : "text-neutral-400 hover:text-white"}`}
            >
              Bulk Batch Engine
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
                  placeholder="Enter target domain (e.g., target-client.com)" 
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
                Analyze Target
              </button>
            </div>
          ) : (
            <div className="space-y-3">
              <label className="text-xs text-neutral-400 uppercase tracking-wider flex items-center gap-1.5">
                <Layers className="w-4 h-4 text-blue-400" /> Enter URLs (one per line, up to 50 max)
              </label>
              <textarea
                rows={5}
                placeholder={"client1.com\nclient2.com"}
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
                Run Batch Analysis
              </button>
            </div>
          )}
        </form>

        {error && (
          <div className="bg-red-500/10 border border-red-500/50 text-red-400 p-4 rounded-md text-sm">
            {error}
          </div>
        )}

        {/* --- SINGLE SCAN DASHBOARD --- */}
        {mode === "single" && data && (
          <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
            
            <div className="flex justify-between items-center border-b border-neutral-800 pb-4">
              <h2 className="text-xl font-semibold text-neutral-200">Sales Intelligence Report</h2>
              <button 
                onClick={exportCSV}
                className="bg-neutral-800 hover:bg-neutral-700 text-white px-4 py-2 rounded-md flex items-center gap-2 transition-colors text-sm"
              >
                <Download className="w-4 h-4" /> Export Complete CSV
              </button>
            </div>

            {/* SECTION 1: SALES ENGINE */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {/* Overall Score */}
              <div className="bg-neutral-900 border border-neutral-800 rounded-lg p-6 flex flex-col items-center justify-center text-center space-y-2">
                <p className="text-xs text-neutral-500 uppercase tracking-wider">Website Score</p>
                <div className={`text-5xl font-bold ${getScoreColor(data.intelligence?.website_score || 0)}`}>
                  {data.intelligence?.website_score || 0}<span className="text-2xl text-neutral-600">/100</span>
                </div>
                <div className="flex gap-4 mt-2 text-xs text-neutral-400">
                  <span>SEO: {data.intelligence?.seo_score}/35</span>
                  <span>Conv: {data.intelligence?.conversion_score}/40</span>
                </div>
              </div>

              {/* Opportunity & Offer */}
              <div className="bg-neutral-900 border border-neutral-800 rounded-lg p-6 flex flex-col justify-center space-y-4">
                <div>
                  <p className="text-xs text-neutral-500 uppercase tracking-wider mb-1 flex items-center gap-1.5"><TrendingUp className="w-3.5 h-3.5" /> Opportunity Level</p>
                  <span className={`px-2.5 py-1 text-xs font-bold rounded ${data.intelligence?.opportunity_score === 'HIGH' ? 'bg-green-500/20 text-green-400 border border-green-500/30' : data.intelligence?.opportunity_score === 'MEDIUM' ? 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/30' : 'bg-red-500/20 text-red-400 border border-red-500/30'}`}>
                    {data.intelligence?.opportunity_score || "UNKNOWN"}
                  </span>
                </div>
                <div>
                  <p className="text-xs text-neutral-500 uppercase tracking-wider mb-1 flex items-center gap-1.5"><DollarSign className="w-3.5 h-3.5" /> Suggested Pricing</p>
                  <p className="text-sm font-medium text-neutral-200">{data.intelligence?.suggested_price || "N/A"}</p>
                  <p className="text-xs text-blue-400 mt-0.5">{data.intelligence?.suggested_offer || "N/A"}</p>
                </div>
              </div>

              {/* Pitch Generation */}
              <div className="bg-blue-900/10 border border-blue-500/30 rounded-lg p-6 flex flex-col justify-center space-y-2">
                <p className="text-xs text-blue-400 uppercase tracking-wider flex items-center gap-1.5">
                  <MessageSquare className="w-4 h-4" /> Generated Pitch
                </p>
                <p className="text-sm text-neutral-300 italic leading-relaxed">"{data.intelligence?.personalized_pitch}"</p>
              </div>
            </div>

            {/* Problems Found */}
            <div className="bg-red-950/20 border border-red-900/50 rounded-lg p-6">
              <div className="flex items-center gap-2 text-red-400 mb-4">
                <AlertCircle className="w-5 h-5" />
                <h3 className="font-medium">Identified Problems (Sales Angles)</h3>
              </div>
              {data.intelligence?.problems_found && data.intelligence.problems_found.length > 0 ? (
                <ul className="grid grid-cols-1 md:grid-cols-2 gap-2">
                  {data.intelligence.problems_found.map((problem: string, i: number) => (
                    <li key={i} className="text-sm text-neutral-300 flex items-start gap-2">
                      <span className="text-red-500 mt-0.5">•</span> {problem}
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-sm text-green-400">No major critical issues detected.</p>
              )}
            </div>

            {/* SECTION 2: DETAILED RAW AUDIT DATA */}
            <h3 className="text-lg font-semibold text-neutral-400 pt-4 border-t border-neutral-800">Raw Technical Audit</h3>
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
                    <span className="text-sm text-green-400 font-medium">{data.status || "Successful"}</span>
                  </div>
                  <div className="flex justify-between items-center border-b border-neutral-800 pb-2">
                    <span className="text-sm text-neutral-500">Engine</span>
                    <span className="text-sm text-neutral-300">FastAPI Sales Intel</span>
                  </div>
                </div>
              </div>

            </div>
          </div>
        )}

        {/* --- BULK SCAN DASHBOARD --- */}
        {mode === "bulk" && bulkData.length > 0 && (
          <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
            <div className="flex justify-between items-center border-b border-neutral-800 pb-4">
              <h2 className="text-xl font-semibold text-neutral-200">Bulk Intelligence Report</h2>
              <button 
                onClick={exportCSV}
                className="bg-neutral-800 hover:bg-neutral-700 text-white px-4 py-2 rounded-md flex items-center gap-2 transition-colors text-sm"
              >
                <Download className="w-4 h-4" /> Export Complete Bulk CSV
              </button>
            </div>

            <div className="bg-neutral-900 border border-neutral-800 rounded-lg overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="border-b border-neutral-800 bg-neutral-950 text-xs uppercase tracking-wider text-neutral-400">
                      <th className="p-3">Target URL</th>
                      <th className="p-3">Score</th>
                      <th className="p-3">Opportunity</th>
                      <th className="p-3">Problems Found</th>
                      <th className="p-3">Contacts</th>
                      <th className="p-3">Stack & Trackers</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-neutral-800 text-sm">
                    {bulkData.map((item, index) => (
                      <tr key={index} className="hover:bg-neutral-800/50 transition-colors">
                        <td className="p-3 font-medium text-blue-400 truncate max-w-[150px]">{item.url}</td>
                        <td className="p-3">
                          {item.status === 'Success' ? (
                            <span className={`font-bold ${getScoreColor(item.intelligence?.website_score || 0)}`}>
                              {item.intelligence?.website_score || 0}
                            </span>
                          ) : (
                            <span className="text-red-500 text-xs">Failed</span>
                          )}
                        </td>
                        <td className="p-3">
                           {item.status === 'Success' && (
                              <span className={`text-[10px] px-1.5 py-0.5 rounded font-bold ${item.intelligence?.opportunity_score === 'HIGH' ? 'bg-green-500/20 text-green-400' : item.intelligence?.opportunity_score === 'MEDIUM' ? 'bg-yellow-500/20 text-yellow-400' : 'bg-neutral-800 text-neutral-400'}`}>
                                {item.intelligence?.opportunity_score}
                              </span>
                           )}
                        </td>
                        <td className="p-3 text-xs text-neutral-300 max-w-[200px] truncate">
                          {item.intelligence?.problems_found?.length || 0} Issues
                        </td>
                        <td className="p-3">
                           <span className="text-xs text-neutral-400">
                             {item.phones?.length ? '📞 ' + item.phones[0] : (item.emails?.length ? '✉️ ' + item.emails[0] : 'None')}
                           </span>
                        </td>
                        <td className="p-3">
                          <div className="flex gap-1.5 flex-wrap max-w-[150px]">
                            {item.tech_stack?.wordpress && <span className="text-[10px] bg-neutral-950 border border-neutral-800 px-1.5 py-0.5 rounded text-neutral-300">WP</span>}
                            {item.tech_stack?.shopify && <span className="text-[10px] bg-neutral-950 border border-neutral-800 px-1.5 py-0.5 rounded text-neutral-300">Shopify</span>}
                            {item.trackers?.facebook_pixel && <span className="text-[10px] bg-neutral-950 border border-neutral-800 px-1.5 py-0.5 rounded text-yellow-400">FB</span>}
                            {item.trackers?.google_analytics && <span className="text-[10px] bg-neutral-950 border border-neutral-800 px-1.5 py-0.5 rounded text-yellow-400">GA</span>}
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