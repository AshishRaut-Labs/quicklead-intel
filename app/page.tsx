"use client";

import { useMemo, useState } from "react";

import {
  Search,
  Download,
  Globe,
  Code,
  FileText,
  Mail,
  Phone,
  Share2,
  Activity,
  Loader2,
  Image as ImageIcon,
  Layers,
  AlertCircle,
  TrendingUp,
  DollarSign,
  MessageSquare,
  Zap,
  Eye,
  ExternalLink,
  Copy,
  X,
  Sparkles,
  ArrowUpRight,
  Target,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  RefreshCw,
} from "lucide-react";

const API_BASE = "https://quicklead-intel.onrender.com";

type Mode = "single" | "bulk";

type LeadData = {
  url?: string;
  title?: string;
  meta_description?: string;
  h1_tags?: string[];
  og_image?: string | null;
  emails?: string[];
  phones?: string[];
  socials?: Record<string, string | null>;
  tech_stack?: Record<string, boolean>;
  trackers?: Record<string, boolean>;
  conversion_signals?: {
    has_form?: boolean;
    has_whatsapp?: boolean;
    has_cta?: boolean;
  };
  technical_signals?: {
    has_viewport?: boolean;
    has_favicon?: boolean;
    has_canonical?: boolean;
  };
  status?: string;
  error?: string;
  intelligence?: {
    website_score?: number;
    seo_score?: number;
    conversion_score?: number;
    opportunity_score?: number;
    opportunity_level?: "HOT" | "HIGH" | "MEDIUM" | "LOW" | string;
    opportunity_reasons?: string[];
    problems_found?: string[];
    suggested_offer?: string;
    suggested_price?: string;
    personalized_pitch?: string;
    project_value?: {
      min?: number;
      max?: number;
    };
  };
};

type BulkLead = LeadData;

export default function QuickLeadDashboard() {
  const [url, setUrl] = useState("");
  const [bulkUrls, setBulkUrls] = useState("");
  const [mode, setMode] = useState<Mode>("single");

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const [data, setData] = useState<LeadData | null>(null);
  const [bulkData, setBulkData] = useState<BulkLead[]>([]);

  const [websitePreview, setWebsitePreview] = useState<string | null>(null);
  const [generatingWebsite, setGeneratingWebsite] = useState(false);

  const [selectedLead, setSelectedLead] = useState<BulkLead | null>(null);

  const [showTechnical, setShowTechnical] = useState(false);
  const [showPitch, setShowPitch] = useState(true);

  const [copySuccess, setCopySuccess] = useState(false);

  const normalizeUrl = (value: string) => {
    const trimmed = value.trim();

    if (!trimmed) return "";

    if (/^https?:\/\//i.test(trimmed)) {
      return trimmed;
    }

    return `https://${trimmed}`;
  };

  const getDomainName = (value: string) => {
    try {
      const normalized = normalizeUrl(value);
      const parsed = new URL(normalized);
      return parsed.hostname.replace(/^www\./i, "");
    } catch {
      return value
        .replace(/^https?:\/\//i, "")
        .replace(/^www\./i, "")
        .split("/")[0];
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 80) return "text-green-400";
    if (score >= 60) return "text-blue-400";
    if (score >= 40) return "text-yellow-400";
    return "text-red-400";
  };

  const getOpportunityClasses = (level?: string) => {
    switch (level) {
      case "HOT":
        return "bg-red-500/15 text-red-400 border-red-500/30";
      case "HIGH":
        return "bg-green-500/15 text-green-400 border-green-500/30";
      case "MEDIUM":
        return "bg-yellow-500/15 text-yellow-400 border-yellow-500/30";
      default:
        return "bg-neutral-800 text-neutral-400 border-neutral-700";
    }
  };

  const getOpportunityRing = (level?: string) => {
    switch (level) {
      case "HOT":
        return "border-red-500/50";
      case "HIGH":
        return "border-green-500/40";
      case "MEDIUM":
        return "border-yellow-500/30";
      default:
        return "border-neutral-800";
    }
  };

  const sortedBulkData = useMemo(() => {
    return [...bulkData].sort((a, b) => {
      const aScore = a.intelligence?.opportunity_score ?? -1;
      const bScore = b.intelligence?.opportunity_score ?? -1;
      return bScore - aScore;
    });
  }, [bulkData]);

  const successfulBulkLeads = useMemo(() => {
    return bulkData.filter((item) => item.status === "Success");
  }, [bulkData]);

  const hotLeads = useMemo(() => {
    return successfulBulkLeads.filter(
      (item) => item.intelligence?.opportunity_level === "HOT"
    );
  }, [successfulBulkLeads]);

  const totalPotential = useMemo(() => {
    return successfulBulkLeads.reduce((sum, item) => {
      const min = item.intelligence?.project_value?.min ?? 0;
      return sum + min;
    }, 0);
  }, [successfulBulkLeads]);

  const handleScan = async (e: React.FormEvent) => {
    e.preventDefault();

    setError("");

    if (mode === "single") {
      if (!url.trim()) {
        setError("Please enter a website URL.");
        return;
      }

      setLoading(true);
      setData(null);
      setWebsitePreview(null);

      try {
        const target = normalizeUrl(url);

        const response = await fetch(
          `${API_BASE}/api/scan?url=${encodeURIComponent(target)}`
        );

        if (!response.ok) {
          let message = "Failed to scan the target URL.";

          try {
            const errorPayload = await response.json();
            message =
              errorPayload?.detail ||
              errorPayload?.message ||
              message;
          } catch {
            // Ignore JSON parsing failure.
          }

          throw new Error(message);
        }

        const result: LeadData = await response.json();
        setData(result);
      } catch (err: any) {
        setError(
          err?.message ||
            "An unexpected error occurred while scanning the website."
        );
      } finally {
        setLoading(false);
      }

      return;
    }

    if (!bulkUrls.trim()) {
      setError("Please enter at least one URL.");
      return;
    }

    const urlList = bulkUrls
      .split("\n")
      .map((item) => item.trim())
      .filter(Boolean)
      .slice(0, 50);

    if (urlList.length === 0) {
      setError("Please enter at least one valid URL.");
      return;
    }

    setLoading(true);
    setBulkData([]);
    setSelectedLead(null);

    try {
      const normalizedUrls = urlList.map(normalizeUrl);

      const response = await fetch(`${API_BASE}/api/bulk-scan`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(normalizedUrls),
      });

      if (!response.ok) {
        let message = "Failed to execute bulk scan.";

        try {
          const errorPayload = await response.json();
          message =
            errorPayload?.detail ||
            errorPayload?.message ||
            message;
        } catch {
          // Ignore JSON parsing failure.
        }

        throw new Error(message);
      }

      const result = await response.json();
      setBulkData(result.results || []);
    } catch (err: any) {
      setError(
        err?.message ||
          "An unexpected error occurred during bulk scan."
      );
    } finally {
      setLoading(false);
    }
  };

  const generateWebsiteForLead = async (lead: LeadData | null) => {
    if (!lead) return;

    setGeneratingWebsite(true);
    setError("");

    try {
      const response = await fetch(
        `${API_BASE}/api/generate-website`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(lead),
        }
      );

      if (!response.ok) {
        let message = "Failed to generate website preview.";

        try {
          const errorPayload = await response.json();
          message =
            errorPayload?.detail ||
            errorPayload?.message ||
            message;
        } catch {
          // Ignore parsing error.
        }

        throw new Error(message);
      }

      const result = await response.json();

      if (!result?.html) {
        throw new Error(
          "The website generator returned no preview."
        );
      }

      setWebsitePreview(result.html);
    } catch (err: any) {
      setError(
        err?.message ||
          "Failed to generate the website preview."
      );
    } finally {
      setGeneratingWebsite(false);
    }
  };

  const copyOutreach = async (lead: LeadData | null) => {
    const pitch =
      lead?.intelligence?.personalized_pitch || "";

    if (!pitch) {
      setError("No outreach message is available for this lead.");
      return;
    }

    try {
      await navigator.clipboard.writeText(pitch);
      setCopySuccess(true);

      window.setTimeout(() => {
        setCopySuccess(false);
      }, 1800);
    } catch {
      setError("Could not copy the outreach message.");
    }
  };

  const printAudit = () => {
    window.print();
  };

  const exportRowsAsCsv = (
    rows: (string | number | boolean)[][]
  ) => {
    const csvContent =
      "data:text/csv;charset=utf-8," +
      rows
        .map((row) =>
          row
            .map((cell) => {
              const value = String(cell ?? "");
              return `"${value.replace(/"/g, '""')}"`;
            })
            .join(",")
        )
        .join("\n");

    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");

    link.setAttribute("href", encodedUri);
    link.setAttribute(
      "download",
      "quicklead_intel_report.csv"
    );

    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const exportCSV = () => {
    if (mode === "single" && data) {
      const intel = data.intelligence || {};

      const rows: (string | number | boolean)[][] = [
        ["Metric", "Value"],

        ["URL", data.url || ""],
        ["Business Name", data.title || ""],

        ["Website Health Score", intel.website_score ?? ""],
        ["SEO Score", intel.seo_score ?? ""],
        ["Conversion Score", intel.conversion_score ?? ""],

        ["Sales Opportunity Score", intel.opportunity_score ?? ""],
        ["Opportunity Level", intel.opportunity_level ?? ""],

        [
          "Opportunity Reasons",
          (intel.opportunity_reasons || []).join(" | "),
        ],

        ["Recommended Offer", intel.suggested_offer || ""],
        ["Suggested Price", intel.suggested_price || ""],

        [
          "Project Min",
          intel.project_value?.min ?? "",
        ],

        [
          "Project Max",
          intel.project_value?.max ?? "",
        ],

        [
          "Problems Found",
          (intel.problems_found || []).join(" | "),
        ],

        [
          "Personalized Pitch",
          intel.personalized_pitch || "",
        ],

        ["Title", data.title || ""],
        ["Meta Description", data.meta_description || ""],

        [
          "H1 Tags",
          (data.h1_tags || []).join(" | "),
        ],

        ["OG Image", data.og_image || ""],

        [
          "Emails",
          (data.emails || []).join(", "),
        ],

        [
          "Phones",
          (data.phones || []).join(", "),
        ],

        [
          "LinkedIn",
          data.socials?.linkedin || "",
        ],

        [
          "Twitter/X",
          data.socials?.twitter || "",
        ],

        [
          "Instagram",
          data.socials?.instagram || "",
        ],

        [
          "Facebook",
          data.socials?.facebook || "",
        ],

        [
          "WordPress",
          data.tech_stack?.wordpress ? "Yes" : "No",
        ],

        [
          "Shopify",
          data.tech_stack?.shopify ? "Yes" : "No",
        ],

        [
          "Next.js",
          data.tech_stack?.nextjs ? "Yes" : "No",
        ],

        [
          "Google Analytics",
          data.trackers?.google_analytics
            ? "Yes"
            : "No",
        ],

        [
          "Facebook Pixel",
          data.trackers?.facebook_pixel
            ? "Yes"
            : "No",
        ],

        [
          "HubSpot",
          data.trackers?.hubspot
            ? "Yes"
            : "No",
        ],
      ];

      exportRowsAsCsv(rows);
      return;
    }

    if (mode === "bulk" && bulkData.length > 0) {
      const rows: (string | number | boolean)[][] = [
        [
          "Rank",
          "URL",
          "Business Name",
          "Website Health",
          "Sales Opportunity",
          "Opportunity Level",
          "Recommended Offer",
          "Suggested Price",
          "Project Min",
          "Project Max",
          "Problems",
          "Phone",
          "Email",
          "LinkedIn",
          "Instagram",
          "Facebook",
        ],
      ];

      sortedBulkData.forEach((item, index) => {
        if (item.status === "Success") {
          const intel = item.intelligence || {};

          rows.push([
            index + 1,
            item.url || "",
            item.title || "",
            intel.website_score ?? "",
            intel.opportunity_score ?? "",
            intel.opportunity_level ?? "",
            intel.suggested_offer ?? "",
            intel.suggested_price ?? "",
            intel.project_value?.min ?? "",
            intel.project_value?.max ?? "",
            (intel.opportunity_reasons || []).join(
              " | "
            ),
            item.phones?.[0] || "",
            item.emails?.[0] || "",
            item.socials?.linkedin || "",
            item.socials?.instagram || "",
            item.socials?.facebook || "",
          ]);
        } else {
          rows.push([
            index + 1,
            item.url || "",
            "",
            "",
            "",
            "FAILED",
            "",
            "",
            "",
            "",
            item.error || "Scan failed",
            "",
            "",
            "",
            "",
            "",
          ]);
        }
      });

      exportRowsAsCsv(rows);
    }
  };

  const renderOpportunityBadge = (
    lead: LeadData
  ) => {
    const level =
      lead.intelligence?.opportunity_level ||
      "UNKNOWN";

    return (
      <span
        className={`inline-flex items-center gap-1.5 border px-2.5 py-1 rounded-full text-[11px] font-bold ${getOpportunityClasses(
          level
        )}`}
      >
        {level === "HOT" && (
          <Target className="w-3.5 h-3.5" />
        )}

        {level}
      </span>
    );
  };

  const renderScoreCard = (
    label: string,
    score: number,
    icon: React.ReactNode,
    accentClass = "text-blue-400"
  ) => {
    return (
      <div className="bg-neutral-900 border border-neutral-800 rounded-xl p-5">
        <div className="flex items-center justify-between">
          <p className="text-xs text-neutral-500 uppercase tracking-wider">
            {label}
          </p>

          <div className={accentClass}>
            {icon}
          </div>
        </div>

        <div
          className={`text-4xl font-bold mt-3 ${getScoreColor(
            score
          )}`}
        >
          {score}
          <span className="text-lg text-neutral-600">
            /100
          </span>
        </div>
      </div>
    );
  };

  const renderLeadDetails = (
    lead: LeadData,
    isModal = false
  ) => {
    const intel = lead.intelligence || {};

    return (
      <div
        className={
          isModal
            ? "space-y-5"
            : "space-y-6"
        }
      >
        {/* Lead header */}
        <div
          className={`bg-neutral-900 border ${getOpportunityRing(
            intel.opportunity_level
          )} rounded-xl p-6`}
        >
          <div className="flex flex-col xl:flex-row justify-between gap-6">
            <div className="flex-1">
              <div className="flex flex-wrap items-center gap-3">
                <h2 className="text-2xl md:text-3xl font-bold">
                  {lead.title || "Unknown Business"}
                </h2>

                {renderOpportunityBadge(lead)}
              </div>

              <div className="flex items-center gap-2 mt-2 text-sm text-neutral-500">
                <Globe className="w-4 h-4" />

                <span className="truncate">
                  {lead.url || "Unknown URL"}
                </span>
              </div>

              <p className="text-sm text-neutral-400 mt-4 max-w-3xl leading-relaxed">
                {intel.opportunity_reasons?.[0] ||
                  "The system found potential opportunities to improve the site's ability to generate enquiries."}
              </p>

              <div className="flex flex-wrap gap-2 mt-5">
                <button
                  onClick={() =>
                    generateWebsiteForLead(lead)
                  }
                  disabled={generatingWebsite}
                  className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white px-4 py-2.5 rounded-lg flex items-center gap-2 text-sm font-medium transition-colors"
                >
                  {generatingWebsite ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <Sparkles className="w-4 h-4" />
                  )}

                  {generatingWebsite
                    ? "Generating Preview..."
                    : "Generate New Website"}
                </button>

                <button
                  onClick={() =>
                    copyOutreach(lead)
                  }
                  className="bg-neutral-800 hover:bg-neutral-700 text-white px-4 py-2.5 rounded-lg flex items-center gap-2 text-sm transition-colors"
                >
                  {copySuccess ? (
                    <CheckCircle2 className="w-4 h-4 text-green-400" />
                  ) : (
                    <Copy className="w-4 h-4" />
                  )}

                  {copySuccess
                    ? "Copied"
                    : "Copy Outreach"}
                </button>

                <button
                  onClick={printAudit}
                  className="bg-neutral-800 hover:bg-neutral-700 text-white px-4 py-2.5 rounded-lg flex items-center gap-2 text-sm transition-colors"
                >
                  <FileText className="w-4 h-4" />
                  Audit PDF
                </button>

                {lead.url && (
                  <a
                    href={lead.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="bg-neutral-800 hover:bg-neutral-700 text-white px-4 py-2.5 rounded-lg flex items-center gap-2 text-sm transition-colors"
                  >
                    <ExternalLink className="w-4 h-4" />
                    Open Website
                  </a>
                )}
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3 min-w-[290px]">
              {renderScoreCard(
                "Website Health",
                intel.website_score || 0,
                <Activity className="w-4 h-4" />,
                "text-green-400"
              )}

              {renderScoreCard(
                "Sales Opportunity",
                intel.opportunity_score || 0,
                <TrendingUp className="w-4 h-4" />,
                "text-blue-400"
              )}
            </div>
          </div>
        </div>

        {/* Commercial cards */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <div className="bg-neutral-900 border border-neutral-800 rounded-xl p-5">
            <div className="flex items-center gap-2 text-neutral-500 mb-3">
              <Target className="w-4 h-4 text-blue-400" />
              <p className="text-xs uppercase tracking-wider">
                Recommended Service
              </p>
            </div>

            <p className="text-lg font-semibold text-neutral-100">
              {intel.suggested_offer ||
                "No offer generated"}
            </p>
          </div>

          <div className="bg-neutral-900 border border-neutral-800 rounded-xl p-5">
            <div className="flex items-center gap-2 text-neutral-500 mb-3">
              <DollarSign className="w-4 h-4 text-green-400" />
              <p className="text-xs uppercase tracking-wider">
                Estimated Project Value
              </p>
            </div>

            <p className="text-2xl font-bold text-green-400">
              {intel.suggested_price || "N/A"}
            </p>

            {intel.project_value?.min !==
              undefined &&
              intel.project_value?.max !==
                undefined && (
                <p className="text-xs text-neutral-500 mt-1">
                  Minimum target: $
                  {intel.project_value.min.toLocaleString()}
                </p>
              )}
          </div>

          <div className="bg-blue-900/10 border border-blue-500/30 rounded-xl p-5">
            <div className="flex items-center gap-2 text-blue-400 mb-3">
              <ArrowUpRight className="w-4 h-4" />
              <p className="text-xs uppercase tracking-wider">
                Best Sales Angle
              </p>
            </div>

            <p className="text-sm text-neutral-300 leading-relaxed">
              {intel.opportunity_reasons?.[0] ||
                "No specific sales angle detected."}
            </p>
          </div>
        </div>

        {/* Opportunity reasons */}
        <div className="bg-neutral-900 border border-neutral-800 rounded-xl p-6">
          <div className="flex items-center justify-between gap-4 mb-5">
            <div className="flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-blue-400" />

              <div>
                <h3 className="font-semibold">
                  Sales Opportunities
                </h3>

                <p className="text-xs text-neutral-500 mt-0.5">
                  These are the reasons this lead may be commercially interesting.
                </p>
              </div>
            </div>

            <div className="text-sm font-bold text-blue-400">
              {intel.opportunity_score || 0}/100
            </div>
          </div>

          {intel.opportunity_reasons &&
          intel.opportunity_reasons.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {intel.opportunity_reasons.map(
                (reason, index) => (
                  <div
                    key={`${reason}-${index}`}
                    className="bg-neutral-950 border border-neutral-800 rounded-lg p-4 flex items-start gap-3"
                  >
                    <div className="w-6 h-6 rounded-full bg-blue-500/10 border border-blue-500/20 flex items-center justify-center shrink-0">
                      <span className="text-xs text-blue-400 font-bold">
                        {index + 1}
                      </span>
                    </div>

                    <p className="text-sm text-neutral-300 leading-relaxed">
                      {reason}
                    </p>
                  </div>
                )
              )}
            </div>
          ) : (
            <p className="text-sm text-neutral-500">
              No major commercial opportunity signals detected.
            </p>
          )}
        </div>

        {/* Outreach */}
        <div className="bg-blue-900/10 border border-blue-500/30 rounded-xl overflow-hidden">
          <button
            onClick={() =>
              setShowPitch((value) => !value)
            }
            className="w-full px-6 py-4 flex items-center justify-between hover:bg-blue-500/5 transition-colors"
          >
            <div className="flex items-center gap-2">
              <MessageSquare className="w-5 h-5 text-blue-400" />

              <div className="text-left">
                <h3 className="font-semibold text-neutral-100">
                  Generated Outreach
                </h3>

                <p className="text-xs text-neutral-500">
                  Ready-to-send first contact message
                </p>
              </div>
            </div>

            {showPitch ? (
              <ChevronUp className="w-4 h-4 text-neutral-500" />
            ) : (
              <ChevronDown className="w-4 h-4 text-neutral-500" />
            )}
          </button>

          {showPitch && (
            <div className="px-6 pb-6">
              <div className="bg-neutral-950 border border-neutral-800 rounded-lg p-4">
                <p className="text-sm text-neutral-300 leading-relaxed">
                  {intel.personalized_pitch ||
                    "No outreach message generated."}
                </p>

                <div className="flex justify-end mt-4">
                  <button
                    onClick={() =>
                      copyOutreach(lead)
                    }
                    className="text-xs bg-neutral-800 hover:bg-neutral-700 text-white px-3 py-2 rounded-md flex items-center gap-2"
                  >
                    <Copy className="w-3.5 h-3.5" />
                    Copy Message
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Problems */}
        <div className="bg-red-950/15 border border-red-900/40 rounded-xl p-6">
          <div className="flex items-center gap-2 text-red-400 mb-4">
            <AlertCircle className="w-5 h-5" />

            <div>
              <h3 className="font-semibold">
                Problems Found
              </h3>

              <p className="text-xs text-red-400/60 mt-0.5">
                Evidence supporting the sales opportunity.
              </p>
            </div>
          </div>

          {intel.problems_found &&
          intel.problems_found.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
              {intel.problems_found.map(
                (problem, index) => (
                  <div
                    key={`${problem}-${index}`}
                    className="text-sm text-neutral-300 bg-neutral-950/60 border border-red-900/30 rounded-lg p-3"
                  >
                    <span className="text-red-400 mr-2">
                      •
                    </span>

                    {problem}
                  </div>
                )
              )}
            </div>
          ) : (
            <p className="text-sm text-green-400">
              No major critical problems were detected.
            </p>
          )}
        </div>

        {/* Technical Details */}
        <div className="bg-neutral-900 border border-neutral-800 rounded-xl overflow-hidden">
          <button
            onClick={() =>
              setShowTechnical((value) => !value)
            }
            className="w-full px-6 py-4 flex items-center justify-between hover:bg-neutral-800/50 transition-colors"
          >
            <div className="flex items-center gap-2">
              <Code className="w-5 h-5 text-neutral-400" />

              <div className="text-left">
                <h3 className="font-semibold text-neutral-200">
                  Technical Details
                </h3>

                <p className="text-xs text-neutral-500">
                  Raw website audit data
                </p>
              </div>
            </div>

            {showTechnical ? (
              <ChevronUp className="w-4 h-4 text-neutral-500" />
            ) : (
              <ChevronDown className="w-4 h-4 text-neutral-500" />
            )}
          </button>

          {showTechnical && (
            <div className="p-6 pt-2 space-y-5">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* SEO */}
                <div className="bg-neutral-950 border border-neutral-800 rounded-lg p-5 space-y-4">
                  <div className="flex items-center gap-2 text-neutral-400">
                    <FileText className="w-5 h-5 text-green-400" />
                    <h3 className="font-medium text-neutral-200">
                      SEO & Structure
                    </h3>
                  </div>

                  <div>
                    <p className="text-xs text-neutral-500 uppercase tracking-wider mb-1">
                      Page Title
                    </p>

                    <p className="text-sm">
                      {lead.title ||
                        "No title detected"}
                    </p>
                  </div>

                  <div>
                    <p className="text-xs text-neutral-500 uppercase tracking-wider mb-1">
                      Meta Description
                    </p>

                    <p className="text-sm text-neutral-300 leading-relaxed">
                      {lead.meta_description ||
                        "No meta description detected"}
                    </p>
                  </div>

                  <div>
                    <p className="text-xs text-neutral-500 uppercase tracking-wider mb-1">
                      H1 Headings
                    </p>

                    {lead.h1_tags &&
                    lead.h1_tags.length > 0 ? (
                      <div className="space-y-1">
                        {lead.h1_tags.map(
                          (h1, index) => (
                            <div
                              key={`${h1}-${index}`}
                              className="text-xs bg-neutral-900 border border-neutral-800 px-2.5 py-2 rounded text-neutral-300"
                            >
                              {h1}
                            </div>
                          )
                        )}
                      </div>
                    ) : (
                      <p className="text-xs text-neutral-500 italic">
                        No H1 detected
                      </p>
                    )}
                  </div>

                  <div>
                    <p className="text-xs text-neutral-500 uppercase tracking-wider mb-1">
                      OpenGraph Image
                    </p>

                    {lead.og_image ? (
                      <div className="flex items-center gap-2">
                        <ImageIcon className="w-4 h-4 text-green-400 shrink-0" />

                        <a
                          href={lead.og_image}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-xs text-blue-400 hover:underline truncate"
                        >
                          {lead.og_image}
                        </a>
                      </div>
                    ) : (
                      <p className="text-xs text-neutral-500 italic">
                        No OG image detected
                      </p>
                    )}
                  </div>
                </div>

                {/* Contacts */}
                <div className="bg-neutral-950 border border-neutral-800 rounded-lg p-5 space-y-4">
                  <div className="flex items-center gap-2 text-neutral-400">
                    <Mail className="w-5 h-5 text-purple-400" />
                    <h3 className="font-medium text-neutral-200">
                      Contacts & Socials
                    </h3>
                  </div>

                  <div>
                    <p className="text-xs text-neutral-500 uppercase tracking-wider mb-2">
                      Emails
                    </p>

                    {lead.emails &&
                    lead.emails.length > 0 ? (
                      <div className="space-y-1">
                        {lead.emails.map(
                          (email, index) => (
                            <div
                              key={`${email}-${index}`}
                              className="text-xs bg-neutral-900 border border-neutral-800 px-3 py-2 rounded flex items-center gap-2"
                            >
                              <Mail className="w-3 h-3 text-purple-400" />
                              {email}
                            </div>
                          )
                        )}
                      </div>
                    ) : (
                      <p className="text-xs text-neutral-500 italic">
                        No emails detected
                      </p>
                    )}
                  </div>

                  <div>
                    <p className="text-xs text-neutral-500 uppercase tracking-wider mb-2">
                      Phone Numbers
                    </p>

                    {lead.phones &&
                    lead.phones.length > 0 ? (
                      <div className="space-y-1">
                        {lead.phones.map(
                          (phone, index) => (
                            <div
                              key={`${phone}-${index}`}
                              className="text-xs bg-neutral-900 border border-neutral-800 px-3 py-2 rounded flex items-center gap-2"
                            >
                              <Phone className="w-3 h-3 text-blue-400" />
                              {phone}
                            </div>
                          )
                        )}
                      </div>
                    ) : (
                      <p className="text-xs text-neutral-500 italic">
                        No phone numbers detected
                      </p>
                    )}
                  </div>

                  <div>
                    <p className="text-xs text-neutral-500 uppercase tracking-wider mb-2">
                      Social Profiles
                    </p>

                    <div className="flex flex-wrap gap-2">
                      {lead.socials &&
                        Object.entries(
                          lead.socials
                        ).map(
                          ([platform, link]) =>
                            link ? (
                              <a
                                key={platform}
                                href={link}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-xs bg-neutral-900 border border-neutral-800 hover:border-neutral-600 px-2.5 py-1.5 rounded capitalize text-blue-400 transition-colors flex items-center gap-1.5"
                              >
                                <Share2 className="w-3 h-3 text-neutral-400" />
                                {platform}
                              </a>
                            ) : null
                        )}
                    </div>
                  </div>
                </div>

                {/* Tech stack */}
                <div className="bg-neutral-950 border border-neutral-800 rounded-lg p-5">
                  <div className="flex items-center gap-2 text-neutral-400 mb-4">
                    <Code className="w-5 h-5 text-orange-400" />
                    <h3 className="font-medium text-neutral-200">
                      Tech Stack
                    </h3>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                    {lead.tech_stack &&
                      Object.entries(
                        lead.tech_stack
                      ).map(
                        ([tech, present]) => (
                          <div
                            key={tech}
                            className="flex items-center justify-between bg-neutral-900 border border-neutral-800 px-3 py-2 rounded"
                          >
                            <span className="text-sm capitalize text-neutral-300">
                              {tech.replace(
                                /_/g,
                                " "
                              )}
                            </span>

                            <span
                              className={`w-2.5 h-2.5 rounded-full ${
                                present
                                  ? "bg-green-500 shadow-sm shadow-green-500/50"
                                  : "bg-neutral-700"
                              }`}
                            />
                          </div>
                        )
                      )}
                  </div>
                </div>

                {/* Trackers */}
                <div className="bg-neutral-950 border border-neutral-800 rounded-lg p-5">
                  <div className="flex items-center gap-2 text-neutral-400 mb-4">
                    <Globe className="w-5 h-5 text-yellow-400" />
                    <h3 className="font-medium text-neutral-200">
                      Marketing & Trackers
                    </h3>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                    {lead.trackers &&
                      Object.entries(
                        lead.trackers
                      ).map(
                        ([tracker, present]) => (
                          <div
                            key={tracker}
                            className="flex items-center justify-between bg-neutral-900 border border-neutral-800 px-3 py-2 rounded"
                          >
                            <span className="text-sm capitalize text-neutral-300">
                              {tracker.replace(
                                /_/g,
                                " "
                              )}
                            </span>

                            <span
                              className={`w-2.5 h-2.5 rounded-full ${
                                present
                                  ? "bg-green-500 shadow-sm shadow-green-500/50"
                                  : "bg-neutral-700"
                              }`}
                            />
                          </div>
                        )
                      )}
                  </div>
                </div>

                {/* Performance */}
                <div className="bg-neutral-950 border border-neutral-800 rounded-lg p-5 md:col-span-2">
                  <div className="flex items-center gap-2 text-neutral-400 mb-4">
                    <Activity className="w-5 h-5 text-blue-400" />
                    <h3 className="font-medium text-neutral-200">
                      Status & Technical Signals
                    </h3>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                    <div className="bg-neutral-900 border border-neutral-800 rounded-lg p-4">
                      <p className="text-xs text-neutral-500 uppercase tracking-wider">
                        Scan Status
                      </p>

                      <p className="text-sm font-medium text-green-400 mt-1">
                        {lead.status ||
                          "Successful"}
                      </p>
                    </div>

                    <div className="bg-neutral-900 border border-neutral-800 rounded-lg p-4">
                      <p className="text-xs text-neutral-500 uppercase tracking-wider">
                        Viewport
                      </p>

                      <p className="text-sm font-medium mt-1">
                        {lead.technical_signals
                          ?.has_viewport
                          ? "Detected"
                          : "Missing"}
                      </p>
                    </div>

                    <div className="bg-neutral-900 border border-neutral-800 rounded-lg p-4">
                      <p className="text-xs text-neutral-500 uppercase tracking-wider">
                        Canonical
                      </p>

                      <p className="text-sm font-medium mt-1">
                        {lead.technical_signals
                          ?.has_canonical
                          ? "Detected"
                          : "Missing"}
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-neutral-950 text-neutral-100 p-4 md:p-8 font-sans">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex flex-col xl:flex-row justify-between items-start xl:items-center gap-5 border-b border-neutral-800 pb-6">
          <div>
            <div className="flex items-center gap-2">
              <Zap className="text-blue-500 fill-blue-500/20" />

              <h1 className="text-3xl font-bold">
                QuickLead Intel
              </h1>
            </div>

            <p className="text-neutral-400 mt-1">
              AshishRaut-Labs | Lead Intelligence → Website Sales
            </p>
          </div>

          <div className="flex bg-neutral-900 border border-neutral-800 p-1 rounded-lg">
            <button
              onClick={() => {
                setMode("single");
                setBulkData([]);
                setSelectedLead(null);
              }}
              className={`px-4 py-2 rounded-md text-xs font-medium transition-colors ${
                mode === "single"
                  ? "bg-blue-600 text-white"
                  : "text-neutral-400 hover:text-white"
              }`}
            >
              Single Lead
            </button>

            <button
              onClick={() => {
                setMode("bulk");
                setData(null);
              }}
              className={`px-4 py-2 rounded-md text-xs font-medium transition-colors ${
                mode === "bulk"
                  ? "bg-blue-600 text-white"
                  : "text-neutral-400 hover:text-white"
              }`}
            >
              Bulk Prospecting
            </button>
          </div>
        </div>

        {/* Scanner */}
        <form
          onSubmit={handleScan}
          className="bg-neutral-900 border border-neutral-800 rounded-xl p-5"
        >
          {mode === "single" ? (
            <div className="flex flex-col md:flex-row gap-2">
              <div className="relative flex-1">
                <Globe className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-neutral-500" />

                <input
                  type="text"
                  placeholder="Enter target domain (e.g. target-client.com)"
                  value={url}
                  onChange={(e) =>
                    setUrl(e.target.value)
                  }
                  className="w-full bg-neutral-950 border border-neutral-800 rounded-lg py-3 pl-10 pr-4 focus:outline-none focus:border-blue-500 transition-colors text-sm"
                />
              </div>

              <button
                type="submit"
                disabled={loading}
                className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white px-6 py-3 rounded-lg flex items-center justify-center gap-2 transition-colors text-sm font-semibold"
              >
                {loading ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Search className="w-4 h-4" />
                )}

                {loading
                  ? "Analyzing..."
                  : "Find Sales Opportunity"}
              </button>
            </div>
          ) : (
            <div className="space-y-3">
              <label className="text-xs text-neutral-400 uppercase tracking-wider flex items-center gap-1.5">
                <Layers className="w-4 h-4 text-blue-400" />
                Enter URLs — up to 50
              </label>

              <textarea
                rows={6}
                placeholder={"client1.com\nclient2.com\nclient3.com"}
                value={bulkUrls}
                onChange={(e) =>
                  setBulkUrls(e.target.value)
                }
                className="w-full bg-neutral-950 border border-neutral-800 rounded-lg p-3 focus:outline-none focus:border-blue-500 transition-colors text-sm font-mono"
              />

              <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
                <p className="text-xs text-neutral-500">
                  QuickLead will rank the results by commercial opportunity.
                </p>

                <button
                  type="submit"
                  disabled={loading}
                  className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white px-6 py-3 rounded-lg flex items-center justify-center gap-2 transition-colors text-sm font-semibold"
                >
                  {loading ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <Search className="w-4 h-4" />
                  )}

                  {loading
                    ? "Running..."
                    : "Rank My Leads"}
                </button>
              </div>
            </div>
          )}
        </form>

        {/* Error */}
        {error && (
          <div className="bg-red-500/10 border border-red-500/40 text-red-400 p-4 rounded-lg text-sm flex items-start gap-2">
            <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* ================================================= */}
        {/* SINGLE LEAD */}
        {/* ================================================= */}

        {mode === "single" && data && (
          <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
            <div className="flex flex-col md:flex-row justify-between md:items-center gap-3 border-b border-neutral-800 pb-4">
              <div>
                <h2 className="text-xl font-semibold">
                  Sales Opportunity Report
                </h2>

                <p className="text-xs text-neutral-500 mt-1">
                  Technical data supports the commercial recommendation.
                </p>
              </div>

              <button
                onClick={exportCSV}
                className="bg-neutral-800 hover:bg-neutral-700 text-white px-4 py-2 rounded-lg flex items-center gap-2 transition-colors text-sm"
              >
                <Download className="w-4 h-4" />
                Export Lead
              </button>
            </div>

            {renderLeadDetails(data)}
          </div>
        )}

        {/* ================================================= */}
        {/* BULK LEADS */}
        {/* ================================================= */}

        {mode === "bulk" &&
          bulkData.length > 0 && (
            <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
              {/* Bulk summary */}
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
                <div className="bg-neutral-900 border border-neutral-800 rounded-xl p-5">
                  <p className="text-xs text-neutral-500 uppercase tracking-wider">
                    Leads Scanned
                  </p>

                  <p className="text-3xl font-bold mt-2">
                    {bulkData.length}
                  </p>
                </div>

                <div className="bg-red-500/5 border border-red-500/20 rounded-xl p-5">
                  <p className="text-xs text-red-400 uppercase tracking-wider">
                    Hot Leads
                  </p>

                  <p className="text-3xl font-bold text-red-400 mt-2">
                    {hotLeads.length}
                  </p>
                </div>

                <div className="bg-blue-500/5 border border-blue-500/20 rounded-xl p-5">
                  <p className="text-xs text-blue-400 uppercase tracking-wider">
                    Successful Scans
                  </p>

                  <p className="text-3xl font-bold text-blue-400 mt-2">
                    {successfulBulkLeads.length}
                  </p>
                </div>

                <div className="bg-green-500/5 border border-green-500/20 rounded-xl p-5">
                  <p className="text-xs text-green-400 uppercase tracking-wider">
                    Minimum Pipeline
                  </p>

                  <p className="text-2xl font-bold text-green-400 mt-2">
                    ${totalPotential.toLocaleString()}
                  </p>
                </div>
              </div>

              <div className="flex flex-col md:flex-row justify-between md:items-center gap-3 border-b border-neutral-800 pb-4">
                <div>
                  <h2 className="text-xl font-semibold">
                    Ranked Prospecting Queue
                  </h2>

                  <p className="text-xs text-neutral-500 mt-1">
                    Highest sales opportunity appears first.
                  </p>
                </div>

                <button
                  onClick={exportCSV}
                  className="bg-neutral-800 hover:bg-neutral-700 text-white px-4 py-2 rounded-lg flex items-center gap-2 transition-colors text-sm"
                >
                  <Download className="w-4 h-4" />
                  Export Leads
                </button>
              </div>

              <div className="bg-neutral-900 border border-neutral-800 rounded-xl overflow-hidden">
                <div className="overflow-x-auto">
                  <table className="w-full text-left border-collapse">
                    <thead>
                      <tr className="border-b border-neutral-800 bg-neutral-950 text-[11px] uppercase tracking-wider text-neutral-500">
                        <th className="p-3">
                          Rank
                        </th>

                        <th className="p-3">
                          Business
                        </th>

                        <th className="p-3">
                          Health
                        </th>

                        <th className="p-3">
                          Opportunity
                        </th>

                        <th className="p-3">
                          Offer
                        </th>

                        <th className="p-3">
                          Value
                        </th>

                        <th className="p-3">
                          Contact
                        </th>

                        <th className="p-3">
                          Action
                        </th>
                      </tr>
                    </thead>

                    <tbody className="divide-y divide-neutral-800 text-sm">
                      {sortedBulkData.map(
                        (item, index) => {
                          const intel =
                            item.intelligence || {};

                          return (
                            <tr
                              key={`${item.url}-${index}`}
                              className="hover:bg-neutral-800/40 transition-colors"
                            >
                              <td className="p-3">
                                <span className="text-xs text-neutral-500 font-mono">
                                  #{index + 1}
                                </span>
                              </td>

                              <td className="p-3 min-w-[220px]">
                                {item.status ===
                                "Success" ? (
                                  <button
                                    onClick={() =>
                                      setSelectedLead(
                                        item
                                      )
                                    }
                                    className="text-left group"
                                  >
                                    <div className="font-semibold text-neutral-200 group-hover:text-blue-400 transition-colors">
                                      {item.title ||
                                        getDomainName(
                                          item.url ||
                                            ""
                                        )}
                                    </div>

                                    <div className="text-xs text-neutral-500 truncate max-w-[220px] mt-1">
                                      {item.url}
                                    </div>
                                  </button>
                                ) : (
                                  <div>
                                    <div className="font-medium text-neutral-300">
                                      {item.url}
                                    </div>

                                    <div className="text-xs text-red-400 mt-1">
                                      Scan failed
                                    </div>
                                  </div>
                                )}
                              </td>

                              <td className="p-3">
                                {item.status ===
                                "Success" ? (
                                  <span
                                    className={`font-bold ${getScoreColor(
                                      intel.website_score ||
                                        0
                                    )}`}
                                  >
                                    {intel.website_score ||
                                      0}
                                  </span>
                                ) : (
                                  <span className="text-neutral-600">
                                    —
                                  </span>
                                )}
                              </td>

                              <td className="p-3">
                                {item.status ===
                                "Success" ? (
                                  <div className="flex flex-col gap-1">
                                    <span className="font-bold text-blue-400">
                                      {intel.opportunity_score ||
                                        0}
                                      /100
                                    </span>

                                    <span
                                      className={`w-fit inline-flex border px-1.5 py-0.5 rounded text-[9px] font-bold ${getOpportunityClasses(
                                        intel.opportunity_level
                                      )}`}
                                    >
                                      {
                                        intel.opportunity_level
                                      }
                                    </span>
                                  </div>
                                ) : (
                                  <span className="text-red-400 text-xs">
                                    FAILED
                                  </span>
                                )}
                              </td>

                              <td className="p-3 max-w-[220px]">
                                <div className="text-xs text-neutral-300 line-clamp-2">
                                  {intel.suggested_offer ||
                                    "—"}
                                </div>
                              </td>

                              <td className="p-3 whitespace-nowrap">
                                <span className="text-green-400 text-xs font-semibold">
                                  {intel.suggested_price ||
                                    "—"}
                                </span>
                              </td>

                              <td className="p-3 min-w-[170px]">
                                <div className="flex flex-col gap-1">
                                  {item.phones?.[0] && (
                                    <span className="text-xs text-neutral-400 flex items-center gap-1.5">
                                      <Phone className="w-3 h-3 text-blue-400" />
                                      {item.phones[0]}
                                    </span>
                                  )}

                                  {item.emails?.[0] && (
                                    <span className="text-xs text-neutral-400 flex items-center gap-1.5 truncate max-w-[170px]">
                                      <Mail className="w-3 h-3 text-purple-400" />
                                      {item.emails[0]}
                                    </span>
                                  )}

                                  {!item.phones?.length &&
                                    !item.emails
                                      ?.length && (
                                      <span className="text-xs text-neutral-600">
                                        No contact
                                      </span>
                                    )}
                                </div>
                              </td>

                              <td className="p-3">
                                {item.status ===
                                "Success" ? (
                                  <button
                                    onClick={() =>
                                      setSelectedLead(
                                        item
                                      )
                                    }
                                    className="bg-neutral-800 hover:bg-blue-600 text-white px-3 py-2 rounded-md text-xs flex items-center gap-1.5 transition-colors"
                                  >
                                    <Eye className="w-3.5 h-3.5" />
                                    Open
                                  </button>
                                ) : (
                                  <span className="text-xs text-neutral-600">
                                    —
                                  </span>
                                )}
                              </td>
                            </tr>
                          );
                        }
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}

        {/* Empty bulk state */}
        {mode === "bulk" &&
          bulkData.length === 0 &&
          !loading && (
            <div className="bg-neutral-900 border border-neutral-800 border-dashed rounded-xl p-10 text-center">
              <Layers className="w-10 h-10 text-neutral-700 mx-auto mb-3" />

              <h3 className="font-semibold text-neutral-300">
                No prospects analyzed yet
              </h3>

              <p className="text-sm text-neutral-500 mt-1">
                Add a list of websites above to find your highest-value opportunities.
              </p>
            </div>
          )}
      </div>

      {/* ================================================= */}
      {/* GENERATED WEBSITE MODAL */}
      {/* ================================================= */}

      {websitePreview && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm p-2 md:p-5">
          <div className="w-full h-full bg-neutral-900 border border-neutral-800 rounded-xl overflow-hidden flex flex-col">
            <div className="h-14 shrink-0 border-b border-neutral-800 flex items-center justify-between px-3 md:px-4">
              <div className="flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-blue-400" />

                <span className="text-sm font-semibold">
                  Generated Website Preview
                </span>
              </div>

              <div className="flex items-center gap-2">
                {data?.url && (
                  <a
                    href={data.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="bg-neutral-800 hover:bg-neutral-700 text-neutral-200 px-3 py-2 rounded-md text-xs flex items-center gap-2"
                  >
                    <ExternalLink className="w-3.5 h-3.5" />
                    Original Site
                  </a>
                )}

                <button
                  onClick={() =>
                    setWebsitePreview(null)
                  }
                  className="bg-neutral-800 hover:bg-neutral-700 p-2 rounded-md"
                  aria-label="Close preview"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            </div>

            <div className="flex-1 bg-white">
              <iframe
                srcDoc={websitePreview}
                title="Generated website preview"
                className="w-full h-full border-0"
                sandbox="allow-same-origin allow-forms"
              />
            </div>
          </div>
        </div>
      )}

      {/* ================================================= */}
      {/* BULK LEAD DETAIL MODAL */}
      {/* ================================================= */}

      {selectedLead && (
        <div className="fixed inset-0 z-40 bg-black/75 backdrop-blur-sm p-3 md:p-6 overflow-y-auto">
          <div className="max-w-6xl mx-auto">
            <div className="flex justify-end mb-2">
              <button
                onClick={() =>
                  setSelectedLead(null)
                }
                className="bg-neutral-900 border border-neutral-800 hover:bg-neutral-800 p-2.5 rounded-lg"
                aria-label="Close lead details"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="bg-neutral-950 border border-neutral-800 rounded-xl p-4 md:p-6 shadow-2xl">
              {renderLeadDetails(
                selectedLead,
                true
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}