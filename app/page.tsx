"use client";

import {
  useMemo,
  useState,
  type FormEvent,
  type ReactNode,
} from "react";

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
} from "lucide-react";

const API_BASE = "https://quicklead-intel.onrender.com";

type Mode = "single" | "bulk";

type LeadData = {
  url?: string;
  domain?: string;

  business_name?: string;
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
    form_count?: number;
    has_whatsapp?: boolean;
    has_tel_link?: boolean;
    has_mailto?: boolean;
    has_booking?: boolean;
    has_cta?: boolean;
    has_conversion_link?: boolean;
    cta_examples?: string[];
  };

  technical_signals?: {
    has_viewport?: boolean;
    has_favicon?: boolean;
    has_canonical?: boolean;
    has_robots_meta?: boolean;
    html_language?: string | null;
    has_ssl?: boolean;
  };

  locale_signals?: {
    language?: string | null;
    country_hint?: string | null;
    currency_hints?: string[];
  };

  business_signals?: {
    commercial_keyword_count?: number;
    commercial_keywords?: string[];
    commercial_navigation_signals?: number;
  };

  status?: string;
  error?: string;

  intelligence?: {
    website_score?: number;
    seo_score?: number;
    conversion_score?: number;
    technical_score?: number;

    opportunity_score?: number;
    opportunity_level?: "HOT" | "HIGH" | "MEDIUM" | "LOW" | string;

    opportunity_reasons?: string[];
    recommendations?: string[];

    service_reason?: string;

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

  const [selectedLead, setSelectedLead] =
    useState<BulkLead | null>(null);

  const [websitePreview, setWebsitePreview] =
    useState<string | null>(null);

  const [previewLead, setPreviewLead] =
    useState<LeadData | null>(null);

  const [generatingWebsite, setGeneratingWebsite] =
    useState(false);

  const [showTechnical, setShowTechnical] =
    useState(false);

  const [showPitch, setShowPitch] =
    useState(true);

  const [copySuccess, setCopySuccess] =
    useState(false);

  // =======================================================
  // HELPERS
  // =======================================================

  const normalizeUrl = (value: string): string => {
    const trimmed = value.trim();

    if (!trimmed) return "";

    if (/^https?:\/\//i.test(trimmed)) {
      return trimmed;
    }

    return `https://${trimmed}`;
  };

  const getDomainName = (value: string): string => {
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

  const getScoreColor = (score: number): string => {
    if (score >= 80) return "text-green-400";
    if (score >= 60) return "text-blue-400";
    if (score >= 40) return "text-yellow-400";
    return "text-red-400";
  };

  const getOpportunityClasses = (
    level?: string
  ): string => {
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

  const getOpportunityRing = (
    level?: string
  ): string => {
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

  const getBooleanLabel = (
    value?: boolean
  ): string => {
    return value ? "Detected" : "Not detected";
  };

  const getBooleanClasses = (
    value?: boolean
  ): string => {
    return value
      ? "text-green-400"
      : "text-neutral-500";
  };

  const getPrettyKey = (
    value: string
  ): string => {
    return value
      .replace(/_/g, " ")
      .replace(/\b\w/g, (letter) =>
        letter.toUpperCase()
      );
  };

  const getBusinessDisplayName = (
    lead: LeadData
  ): string => {
    return (
      lead.business_name ||
      getDomainName(lead.url || "") ||
      "Unknown Business"
    );
  };

  // =======================================================
  // BULK DATA
  // =======================================================

  const sortedBulkData = useMemo(() => {
    return [...bulkData].sort((a, b) => {
      const aScore =
        a.intelligence?.opportunity_score ?? -1;

      const bScore =
        b.intelligence?.opportunity_score ?? -1;

      return bScore - aScore;
    });
  }, [bulkData]);

  const successfulBulkLeads = useMemo(() => {
    return bulkData.filter(
      (item) => item.status === "Success"
    );
  }, [bulkData]);

  const hotLeads = useMemo(() => {
    return successfulBulkLeads.filter(
      (item) =>
        item.intelligence?.opportunity_level ===
        "HOT"
    );
  }, [successfulBulkLeads]);

  const highValueLeads = useMemo(() => {
    return successfulBulkLeads.filter((item) => {
      const score =
        item.intelligence?.opportunity_score ?? 0;

      return score >= 55;
    });
  }, [successfulBulkLeads]);

  const totalPotential = useMemo(() => {
    return successfulBulkLeads.reduce(
      (sum, item) => {
        const min =
          item.intelligence?.project_value?.min ??
          0;

        return sum + min;
      },
      0
    );
  }, [successfulBulkLeads]);

  // =======================================================
  // SCANNING
  // =======================================================

  const handleScan = async (
    e: FormEvent
  ): Promise<void> => {
    e.preventDefault();

    setError("");

    if (mode === "single") {
      if (!url.trim()) {
        setError(
          "Please enter a website URL."
        );
        return;
      }

      setLoading(true);
      setData(null);
      setWebsitePreview(null);
      setPreviewLead(null);

      try {
        const target = normalizeUrl(url);

        const response = await fetch(
          `${API_BASE}/api/scan?url=${encodeURIComponent(
            target
          )}`
        );

        if (!response.ok) {
          let message =
            "Failed to scan the target URL.";

          try {
            const payload =
              await response.json();

            message =
              payload?.detail ||
              payload?.message ||
              message;
          } catch {
            // Ignore parsing errors.
          }

          throw new Error(message);
        }

        const result: LeadData =
          await response.json();

        setData(result);
      } catch (err: unknown) {
        setError(
          err instanceof Error
            ? err.message
            : "An unexpected error occurred while scanning the website."
        );
      } finally {
        setLoading(false);
      }

      return;
    }

    if (!bulkUrls.trim()) {
      setError(
        "Please enter at least one URL."
      );
      return;
    }

    const urlList = bulkUrls
      .split("\n")
      .map((item) => item.trim())
      .filter(Boolean)
      .slice(0, 50);

    if (urlList.length === 0) {
      setError(
        "Please enter at least one valid URL."
      );
      return;
    }

    setLoading(true);
    setBulkData([]);
    setSelectedLead(null);

    try {
      const normalizedUrls =
        urlList.map(normalizeUrl);

      const response = await fetch(
        `${API_BASE}/api/bulk-scan`,
        {
          method: "POST",
          headers: {
            "Content-Type":
              "application/json",
          },
          body: JSON.stringify(
            normalizedUrls
          ),
        }
      );

      if (!response.ok) {
        let message =
          "Failed to execute bulk scan.";

        try {
          const payload =
            await response.json();

          message =
            payload?.detail ||
            payload?.message ||
            message;
        } catch {
          // Ignore parsing errors.
        }

        throw new Error(message);
      }

      const result =
        await response.json();

      setBulkData(
        Array.isArray(result?.results)
          ? result.results
          : []
      );
    } catch (err: unknown) {
      setError(
        err instanceof Error
          ? err.message
          : "An unexpected error occurred during bulk scanning."
      );
    } finally {
      setLoading(false);
    }
  };

  // =======================================================
  // WEBSITE GENERATOR
  // =======================================================

  const generateWebsiteForLead = async (
    lead: LeadData | null
  ): Promise<void> => {
    if (!lead) return;

    setGeneratingWebsite(true);
    setError("");
    setPreviewLead(lead);

    try {
      const response = await fetch(
        `${API_BASE}/api/generate-website`,
        {
          method: "POST",
          headers: {
            "Content-Type":
              "application/json",
          },
          body: JSON.stringify(lead),
        }
      );

      if (!response.ok) {
        let message =
          "Failed to generate website preview.";

        try {
          const payload =
            await response.json();

          message =
            payload?.detail ||
            payload?.message ||
            message;
        } catch {
          // Ignore parsing errors.
        }

        throw new Error(message);
      }

      const result =
        await response.json();

      if (!result?.html) {
        throw new Error(
          "The website generator returned no preview."
        );
      }

      setWebsitePreview(
        result.html
      );
    } catch (err: unknown) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to generate the website preview."
      );

      setPreviewLead(null);
    } finally {
      setGeneratingWebsite(false);
    }
  };

  // =======================================================
  // OUTREACH
  // =======================================================

  const copyOutreach = async (
    lead: LeadData | null
  ): Promise<void> => {
    const pitch =
      lead?.intelligence
        ?.personalized_pitch || "";

    if (!pitch) {
      setError(
        "No outreach message is available for this lead."
      );
      return;
    }

    try {
      await navigator.clipboard.writeText(
        pitch
      );

      setCopySuccess(true);

      window.setTimeout(() => {
        setCopySuccess(false);
      }, 1800);
    } catch {
      setError(
        "Could not copy the outreach message."
      );
    }
  };

  // =======================================================
  // EXPORT
  // =======================================================

  const exportRowsAsCsv = (
    rows: (string | number | boolean)[][]
  ): void => {
    const csvContent =
      "data:text/csv;charset=utf-8," +
      rows
        .map((row) =>
          row
            .map((cell) => {
              const value = String(
                cell ?? ""
              );

              return `"${value.replace(
                /"/g,
                '""'
              )}"`;
            })
            .join(",")
        )
        .join("\n");

    const encodedUri =
      encodeURI(csvContent);

    const link =
      document.createElement("a");

    link.setAttribute(
      "href",
      encodedUri
    );

    link.setAttribute(
      "download",
      "quicklead_intel_report.csv"
    );

    document.body.appendChild(link);

    link.click();

    document.body.removeChild(link);
  };

  const exportCSV = (): void => {
    if (mode === "single" && data) {
      const intel =
        data.intelligence || {};

      const rows: (
        | string
        | number
        | boolean
      )[][] = [
        ["Metric", "Value"],

        ["URL", data.url || ""],

        [
          "Domain",
          data.domain || "",
        ],

        [
          "Business Name",
          data.business_name ||
            getBusinessDisplayName(data),
        ],

        [
          "Page Title",
          data.title || "",
        ],

        [
          "Website Health Score",
          intel.website_score ?? "",
        ],

        [
          "SEO Score",
          intel.seo_score ?? "",
        ],

        [
          "Conversion Score",
          intel.conversion_score ?? "",
        ],

        [
          "Technical Score",
          intel.technical_score ?? "",
        ],

        [
          "Sales Opportunity Score",
          intel.opportunity_score ?? "",
        ],

        [
          "Opportunity Level",
          intel.opportunity_level ?? "",
        ],

        [
          "Opportunity Reasons",
          (
            intel.opportunity_reasons ||
            []
          ).join(" | "),
        ],

        [
          "Recommendations",
          (
            intel.recommendations ||
            []
          ).join(" | "),
        ],

        [
          "Recommended Service",
          intel.suggested_offer ||
            "",
        ],

        [
          "Suggested Price",
          intel.suggested_price ||
            "",
        ],

        [
          "Project Min",
          intel.project_value?.min ??
            "",
        ],

        [
          "Project Max",
          intel.project_value?.max ??
            "",
        ],

        [
          "Problems Found",
          (
            intel.problems_found ||
            []
          ).join(" | "),
        ],

        [
          "Personalized Pitch",
          intel.personalized_pitch ||
            "",
        ],

        [
          "Language",
          data.locale_signals
            ?.language || "",
        ],

        [
          "Country Hint",
          data.locale_signals
            ?.country_hint || "",
        ],

        [
          "Currency Hints",
          (
            data.locale_signals
              ?.currency_hints ||
            []
          ).join(", "),
        ],

        [
          "Emails",
          (
            data.emails || []
          ).join(", "),
        ],

        [
          "Phones",
          (
            data.phones || []
          ).join(", "),
        ],

        [
          "LinkedIn",
          data.socials
            ?.linkedin || "",
        ],

        [
          "Twitter/X",
          data.socials?.twitter ||
            "",
        ],

        [
          "Instagram",
          data.socials
            ?.instagram || "",
        ],

        [
          "Facebook",
          data.socials
            ?.facebook || "",
        ],
      ];

      Object.entries(
        data.tech_stack || {}
      ).forEach(
        ([key, value]) => {
          rows.push([
            `Tech: ${getPrettyKey(
              key
            )}`,
            value
              ? "Detected"
              : "Not detected",
          ]);
        }
      );

      Object.entries(
        data.trackers || {}
      ).forEach(
        ([key, value]) => {
          rows.push([
            `Tracker: ${getPrettyKey(
              key
            )}`,
            value
              ? "Detected"
              : "Not detected",
          ]);
        }
      );

      exportRowsAsCsv(rows);
      return;
    }

    if (
      mode === "bulk" &&
      bulkData.length > 0
    ) {
      const rows: (
        | string
        | number
        | boolean
      )[][] = [
        [
          "Rank",
          "URL",
          "Domain",
          "Business Name",
          "Website Health",
          "Sales Opportunity",
          "Opportunity Level",
          "Recommended Service",
          "Suggested Price",
          "Project Min",
          "Project Max",
          "Top Sales Reasons",
          "Phone",
          "Email",
          "Country",
        ],
      ];

      sortedBulkData.forEach(
        (item, index) => {
          if (item.status === "Success") {
            const intel =
              item.intelligence || {};

            rows.push([
              index + 1,
              item.url || "",
              item.domain || "",
              item.business_name ||
                getBusinessDisplayName(
                  item
                ),
              intel.website_score ??
                "",
              intel.opportunity_score ??
                "",
              intel.opportunity_level ??
                "",
              intel.suggested_offer ??
                "",
              intel.suggested_price ??
                "",
              intel.project_value
                ?.min ?? "",
              intel.project_value
                ?.max ?? "",
              (
                intel.opportunity_reasons ||
                []
              ).join(" | "),
              item.phones?.[0] ||
                "",
              item.emails?.[0] ||
                "",
              item.locale_signals
                ?.country_hint ||
                "",
            ]);
          } else {
            rows.push([
              index + 1,
              item.url || "",
              "",
              "",
              "",
              "",
              "FAILED",
              "",
              "",
              "",
              "",
              item.error ||
                "Scan failed",
              "",
              "",
              "",
            ]);
          }
        }
      );

      exportRowsAsCsv(rows);
    }
  };

  // =======================================================
  // SCORE CARD
  // =======================================================

  const renderScoreCard = (
    label: string,
    score: number,
    icon: ReactNode
  ): ReactNode => {
    return (
      <div className="bg-neutral-950 border border-neutral-800 rounded-xl p-5">
        <div className="flex items-center justify-between">
          <p className="text-[11px] text-neutral-500 uppercase tracking-wider">
            {label}
          </p>

          <div className="text-blue-400">
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

  // =======================================================
  // OPPORTUNITY BADGE
  // =======================================================

  const renderOpportunityBadge = (
    lead: LeadData
  ): ReactNode => {
    const level =
      lead.intelligence
        ?.opportunity_level ||
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

  // =======================================================
  // LEAD DETAILS
  // =======================================================

  const renderLeadDetails = (
    lead: LeadData,
    isModal = false
  ): ReactNode => {
    const intel =
      lead.intelligence || {};

    const businessName =
      getBusinessDisplayName(
        lead
      );

    const country =
      lead.locale_signals
        ?.country_hint;

    const language =
      lead.locale_signals
        ?.language;

    return (
      <div
        className={
          isModal
            ? "space-y-5"
            : "space-y-6"
        }
      >
        {/* PRIMARY SALES HEADER */}

        <div
          className={`bg-neutral-900 border ${getOpportunityRing(
            intel.opportunity_level
          )} rounded-2xl p-6`}
        >
          <div className="flex flex-col xl:flex-row justify-between gap-7">
            <div className="flex-1">
              <div className="flex flex-wrap items-center gap-3">
                <h2 className="text-2xl md:text-3xl font-bold text-white">
                  {businessName}
                </h2>

                {renderOpportunityBadge(
                  lead
                )}
              </div>

              <p className="text-sm text-neutral-400 mt-2">
                {lead.title ||
                  "Website analysis complete"}
              </p>

              <div className="flex flex-wrap items-center gap-x-4 gap-y-2 mt-3 text-xs text-neutral-500">
                <span className="flex items-center gap-1.5">
                  <Globe className="w-3.5 h-3.5" />

                  {lead.domain ||
                    getDomainName(
                      lead.url || ""
                    )}
                </span>

                {country && (
                  <span>
                    Country:{" "}
                    <span className="text-neutral-300">
                      {country}
                    </span>
                  </span>
                )}

                {language && (
                  <span>
                    Language:{" "}
                    <span className="text-neutral-300">
                      {language}
                    </span>
                  </span>
                )}
              </div>

              <div className="flex flex-wrap gap-2 mt-6">
                <button
                  onClick={() =>
                    generateWebsiteForLead(
                      lead
                    )
                  }
                  disabled={
                    generatingWebsite
                  }
                  className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white px-4 py-2.5 rounded-lg flex items-center gap-2 text-sm font-semibold transition-colors"
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
                    copyOutreach(
                      lead
                    )
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
                  onClick={() =>
                    window.print()
                  }
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

            <div className="grid grid-cols-2 gap-3 min-w-[300px]">
              {renderScoreCard(
                "Website Health",
                intel.website_score ??
                  0,
                <Activity className="w-4 h-4" />
              )}

              {renderScoreCard(
                "Sales Opportunity",
                intel.opportunity_score ??
                  0,
                <TrendingUp className="w-4 h-4" />
              )}
            </div>
          </div>
        </div>

        {/* COMMERCIAL SUMMARY */}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <div className="bg-neutral-900 border border-neutral-800 rounded-xl p-5">
            <div className="flex items-center gap-2 text-neutral-500 mb-3">
              <Target className="w-4 h-4 text-blue-400" />

              <p className="text-[11px] uppercase tracking-wider">
                Recommended Service
              </p>
            </div>

            <p className="text-lg font-semibold text-neutral-100">
              {intel.suggested_offer ||
                "No offer generated"}
            </p>

            {intel.service_reason && (
              <p className="text-xs text-neutral-500 mt-2 leading-relaxed">
                {intel.service_reason}
              </p>
            )}
          </div>

          <div className="bg-neutral-900 border border-neutral-800 rounded-xl p-5">
            <div className="flex items-center gap-2 text-neutral-500 mb-3">
              <DollarSign className="w-4 h-4 text-green-400" />

              <p className="text-[11px] uppercase tracking-wider">
                Estimated Project Value
              </p>
            </div>

            <p className="text-2xl font-bold text-green-400">
              {intel.suggested_price ||
                "N/A"}
            </p>

            {intel.project_value && (
              <p className="text-xs text-neutral-500 mt-1">
                Potential range: $
                {(
                  intel.project_value
                    .min ?? 0
                ).toLocaleString()}{" "}
                – $
                {(
                  intel.project_value
                    .max ?? 0
                ).toLocaleString()}
              </p>
            )}
          </div>

          <div className="bg-blue-900/10 border border-blue-500/30 rounded-xl p-5">
            <div className="flex items-center gap-2 text-blue-400 mb-3">
              <ArrowUpRight className="w-4 h-4" />

              <p className="text-[11px] uppercase tracking-wider">
                Best Sales Angle
              </p>
            </div>

            <p className="text-sm text-neutral-300 leading-relaxed">
              {intel.opportunity_reasons?.[0] ||
                intel.service_reason ||
                "No specific sales angle detected."}
            </p>
          </div>
        </div>

        {/* RECOMMENDATIONS */}

        {intel.recommendations &&
          intel.recommendations.length >
            0 && (
            <div className="bg-neutral-900 border border-neutral-800 rounded-xl p-6">
              <div className="flex items-center gap-2 mb-5">
                <Sparkles className="w-5 h-5 text-blue-400" />

                <div>
                  <h3 className="font-semibold text-neutral-100">
                    What You Could Sell
                  </h3>

                  <p className="text-xs text-neutral-500 mt-0.5">
                    Recommended improvements based on detected evidence.
                  </p>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {intel.recommendations.map(
                  (recommendation, index) => (
                    <div
                      key={`${recommendation}-${index}`}
                      className="bg-neutral-950 border border-neutral-800 rounded-lg p-4 flex items-start gap-3"
                    >
                      <div className="w-6 h-6 rounded-full bg-blue-500/10 border border-blue-500/20 flex items-center justify-center shrink-0">
                        <span className="text-xs text-blue-400 font-bold">
                          {index + 1}
                        </span>
                      </div>

                      <p className="text-sm text-neutral-300 leading-relaxed">
                        {recommendation}
                      </p>
                    </div>
                  )
                )}
              </div>
            </div>
          )}

        {/* SALES OPPORTUNITIES */}

        <div className="bg-neutral-900 border border-neutral-800 rounded-xl p-6">
          <div className="flex items-center justify-between gap-4 mb-5">
            <div className="flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-blue-400" />

              <div>
                <h3 className="font-semibold">
                  Sales Opportunities
                </h3>

                <p className="text-xs text-neutral-500 mt-0.5">
                  Evidence used to determine the commercial opportunity.
                </p>
              </div>
            </div>

            <div className="text-sm font-bold text-blue-400">
              {intel.opportunity_score ?? 0}
              /100
            </div>
          </div>

          {intel.opportunity_reasons &&
          intel.opportunity_reasons.length >
            0 ? (
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

        {/* OUTREACH */}

        <div className="bg-blue-900/10 border border-blue-500/30 rounded-xl overflow-hidden">
          <button
            onClick={() =>
              setShowPitch(
                (value) => !value
              )
            }
            className="w-full px-6 py-4 flex items-center justify-between hover:bg-blue-500/5 transition-colors"
          >
            <div className="flex items-center gap-2">
              <MessageSquare className="w-5 h-5 text-blue-400" />

              <div className="text-left">
                <h3 className="font-semibold">
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
                      copyOutreach(
                        lead
                      )
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

        {/* PROBLEMS */}

        <div className="bg-red-950/15 border border-red-900/40 rounded-xl p-6">
          <div className="flex items-center gap-2 text-red-400 mb-4">
            <AlertCircle className="w-5 h-5" />

            <div>
              <h3 className="font-semibold">
                Problems Found
              </h3>

              <p className="text-xs text-red-400/60 mt-0.5">
                Technical and conversion evidence supporting the opportunity.
              </p>
            </div>
          </div>

          {intel.problems_found &&
          intel.problems_found.length >
            0 ? (
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

        {/* TECHNICAL DETAILS */}

        <div className="bg-neutral-900 border border-neutral-800 rounded-xl overflow-hidden">
          <button
            onClick={() =>
              setShowTechnical(
                (value) => !value
              )
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
                  Raw website evidence and extracted data
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
                      Business Name
                    </p>

                    <p className="text-sm font-medium">
                      {lead.business_name ||
                        "Not confidently detected"}
                    </p>
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
                          href={
                            lead.og_image
                          }
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

                {/* CONTACTS */}

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

                    {(!lead.socials ||
                      Object.values(
                        lead.socials
                      ).every(
                        (value) => !value
                      )) && (
                      <p className="text-xs text-neutral-500 italic">
                        No social profiles detected
                      </p>
                    )}
                  </div>
                </div>

                {/* CONVERSION */}

                <div className="bg-neutral-950 border border-neutral-800 rounded-lg p-5">
                  <div className="flex items-center gap-2 text-neutral-400 mb-4">
                    <Target className="w-5 h-5 text-blue-400" />

                    <h3 className="font-medium text-neutral-200">
                      Conversion Signals
                    </h3>
                  </div>

                  <div className="space-y-2">
                    {[
                      [
                        "CTA",
                        lead
                          .conversion_signals
                          ?.has_cta,
                      ],
                      [
                        "Lead Form",
                        lead
                          .conversion_signals
                          ?.has_form,
                      ],
                      [
                        "WhatsApp",
                        lead
                          .conversion_signals
                          ?.has_whatsapp,
                      ],
                      [
                        "Phone Link",
                        lead
                          .conversion_signals
                          ?.has_tel_link,
                      ],
                      [
                        "Email Link",
                        lead
                          .conversion_signals
                          ?.has_mailto,
                      ],
                      [
                        "Booking",
                        lead
                          .conversion_signals
                          ?.has_booking,
                      ],
                      [
                        "Conversion Link",
                        lead
                          .conversion_signals
                          ?.has_conversion_link,
                      ],
                    ].map(
                      ([label, value]) => (
                        <div
                          key={String(label)}
                          className="flex items-center justify-between bg-neutral-900 border border-neutral-800 px-3 py-2 rounded"
                        >
                          <span className="text-sm text-neutral-300">
                            {String(label)}
                          </span>

                          <span
                            className={`text-xs font-semibold ${getBooleanClasses(
                              Boolean(
                                value
                              )
                            )}`}
                          >
                            {getBooleanLabel(
                              Boolean(
                                value
                              )
                            )}
                          </span>
                        </div>
                      )
                    )}
                  </div>
                </div>

                {/* TECH */}

                <div className="bg-neutral-950 border border-neutral-800 rounded-lg p-5">
                  <div className="flex items-center gap-2 text-neutral-400 mb-4">
                    <Code className="w-5 h-5 text-orange-400" />

                    <h3 className="font-medium text-neutral-200">
                      Tech Stack
                    </h3>
                  </div>

                  <div className="space-y-2">
                    {lead.tech_stack &&
                      Object.entries(
                        lead.tech_stack
                      ).map(
                        ([tech, present]) => (
                          <div
                            key={tech}
                            className="flex items-center justify-between bg-neutral-900 border border-neutral-800 px-3 py-2 rounded"
                          >
                            <span className="text-sm text-neutral-300">
                              {getPrettyKey(
                                tech
                              )}
                            </span>

                            <span
                              className={`text-xs font-semibold ${getBooleanClasses(
                                present
                              )}`}
                            >
                              {getBooleanLabel(
                                present
                              )}
                            </span>
                          </div>
                        )
                      )}
                  </div>
                </div>

                {/* MARKETING */}

                <div className="bg-neutral-950 border border-neutral-800 rounded-lg p-5">
                  <div className="flex items-center gap-2 text-neutral-400 mb-4">
                    <Globe className="w-5 h-5 text-yellow-400" />

                    <h3 className="font-medium text-neutral-200">
                      Marketing & Tracking
                    </h3>
                  </div>

                  <div className="space-y-2">
                    {lead.trackers &&
                      Object.entries(
                        lead.trackers
                      ).map(
                        ([tracker, present]) => (
                          <div
                            key={tracker}
                            className="flex items-center justify-between bg-neutral-900 border border-neutral-800 px-3 py-2 rounded"
                          >
                            <span className="text-sm text-neutral-300">
                              {getPrettyKey(
                                tracker
                              )}
                            </span>

                            <span
                              className={`text-xs font-semibold ${getBooleanClasses(
                                present
                              )}`}
                            >
                              {getBooleanLabel(
                                present
                              )}
                            </span>
                          </div>
                        )
                      )}
                  </div>
                </div>

                {/* LOCALIZATION */}

                <div className="bg-neutral-950 border border-neutral-800 rounded-lg p-5">
                  <div className="flex items-center gap-2 text-neutral-400 mb-4">
                    <Globe className="w-5 h-5 text-blue-400" />

                    <h3 className="font-medium text-neutral-200">
                      Global Signals
                    </h3>
                  </div>

                  <div className="space-y-2">
                    <div className="flex items-center justify-between bg-neutral-900 border border-neutral-800 px-3 py-2 rounded">
                      <span className="text-sm text-neutral-300">
                        Country Hint
                      </span>

                      <span className="text-xs text-neutral-400">
                        {lead.locale_signals
                          ?.country_hint ||
                          "Unknown"}
                      </span>
                    </div>

                    <div className="flex items-center justify-between bg-neutral-900 border border-neutral-800 px-3 py-2 rounded">
                      <span className="text-sm text-neutral-300">
                        Language
                      </span>

                      <span className="text-xs text-neutral-400">
                        {lead.locale_signals
                          ?.language ||
                          "Unknown"}
                      </span>
                    </div>

                    <div className="flex items-center justify-between bg-neutral-900 border border-neutral-800 px-3 py-2 rounded">
                      <span className="text-sm text-neutral-300">
                        Currency Hints
                      </span>

                      <span className="text-xs text-neutral-400 text-right max-w-[55%]">
                        {lead.locale_signals
                          ?.currency_hints &&
                        lead.locale_signals
                          .currency_hints
                          .length > 0
                          ? lead.locale_signals.currency_hints.join(
                              ", "
                            )
                          : "None detected"}
                      </span>
                    </div>
                  </div>
                </div>

                {/* TECHNICAL */}

                <div className="bg-neutral-950 border border-neutral-800 rounded-lg p-5 md:col-span-2">
                  <div className="flex items-center gap-2 text-neutral-400 mb-4">
                    <Activity className="w-5 h-5 text-blue-400" />

                    <h3 className="font-medium text-neutral-200">
                      Technical Signals
                    </h3>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
                    <div className="bg-neutral-900 border border-neutral-800 rounded-lg p-4">
                      <p className="text-xs text-neutral-500 uppercase tracking-wider">
                        Viewport
                      </p>

                      <p
                        className={`text-sm font-semibold mt-1 ${getBooleanClasses(
                          lead
                            .technical_signals
                            ?.has_viewport
                        )}`}
                      >
                        {getBooleanLabel(
                          lead
                            .technical_signals
                            ?.has_viewport
                        )}
                      </p>
                    </div>

                    <div className="bg-neutral-900 border border-neutral-800 rounded-lg p-4">
                      <p className="text-xs text-neutral-500 uppercase tracking-wider">
                        Canonical
                      </p>

                      <p
                        className={`text-sm font-semibold mt-1 ${getBooleanClasses(
                          lead
                            .technical_signals
                            ?.has_canonical
                        )}`}
                      >
                        {getBooleanLabel(
                          lead
                            .technical_signals
                            ?.has_canonical
                        )}
                      </p>
                    </div>

                    <div className="bg-neutral-900 border border-neutral-800 rounded-lg p-4">
                      <p className="text-xs text-neutral-500 uppercase tracking-wider">
                        Favicon
                      </p>

                      <p
                        className={`text-sm font-semibold mt-1 ${getBooleanClasses(
                          lead
                            .technical_signals
                            ?.has_favicon
                        )}`}
                      >
                        {getBooleanLabel(
                          lead
                            .technical_signals
                            ?.has_favicon
                        )}
                      </p>
                    </div>

                    <div className="bg-neutral-900 border border-neutral-800 rounded-lg p-4">
                      <p className="text-xs text-neutral-500 uppercase tracking-wider">
                        Robots Meta
                      </p>

                      <p
                        className={`text-sm font-semibold mt-1 ${getBooleanClasses(
                          lead
                            .technical_signals
                            ?.has_robots_meta
                        )}`}
                      >
                        {getBooleanLabel(
                          lead
                            .technical_signals
                            ?.has_robots_meta
                        )}
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* STATUS */}

        {!isModal && (
          <div className="flex items-center justify-between text-xs text-neutral-600 px-1">
            <span>
              Scan status:{" "}
              <span className="text-green-500">
                {lead.status ||
                  "Success"}
              </span>
            </span>

            <span>
              Engine: Global Sales Intelligence
            </span>
          </div>
        )}
      </div>
    );
  };

  // =======================================================
  // MAIN UI
  // =======================================================

  return (
    <div className="min-h-screen bg-neutral-950 text-neutral-100 p-4 md:p-8 font-sans">
      <div className="max-w-7xl mx-auto space-y-6">

        {/* HEADER */}

        <div className="flex flex-col xl:flex-row justify-between items-start xl:items-center gap-5 border-b border-neutral-800 pb-6">
          <div>
            <div className="flex items-center gap-2">
              <Zap className="text-blue-500 fill-blue-500/20" />

              <h1 className="text-3xl font-bold">
                QuickLead Intel
              </h1>
            </div>

            <p className="text-neutral-400 mt-1">
              AshishRaut-Labs | Global Lead Intelligence → Website Sales
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

        {/* SCANNER */}

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
                  placeholder="Enter any website worldwide"
                  value={url}
                  onChange={(e) =>
                    setUrl(
                      e.target.value
                    )
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
                placeholder={
                  "business1.com\nbusiness2.com\nbusiness3.com"
                }
                value={bulkUrls}
                onChange={(e) =>
                  setBulkUrls(
                    e.target.value
                  )
                }
                className="w-full bg-neutral-950 border border-neutral-800 rounded-lg p-3 focus:outline-none focus:border-blue-500 transition-colors text-sm font-mono"
              />

              <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
                <p className="text-xs text-neutral-500">
                  QuickLead ranks prospects by global commercial opportunity.
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

        {/* ERROR */}

        {error && (
          <div className="bg-red-500/10 border border-red-500/40 text-red-400 p-4 rounded-lg text-sm flex items-start gap-2">
            <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" />

            <span>{error}</span>
          </div>
        )}

        {/* SINGLE */}

        {mode === "single" &&
          data && (
            <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
              <div className="flex flex-col md:flex-row justify-between md:items-center gap-3 border-b border-neutral-800 pb-4">
                <div>
                  <h2 className="text-xl font-semibold">
                    Sales Opportunity Report
                  </h2>

                  <p className="text-xs text-neutral-500 mt-1">
                    Commercial intelligence first. Technical evidence underneath.
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

        {/* BULK */}

        {mode === "bulk" &&
          bulkData.length > 0 && (
            <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">

              {/* BULK METRICS */}

              <div className="grid grid-cols-2 lg:grid-cols-5 gap-3">
                <div className="bg-neutral-900 border border-neutral-800 rounded-xl p-5">
                  <p className="text-xs text-neutral-500 uppercase tracking-wider">
                    Leads
                  </p>

                  <p className="text-3xl font-bold mt-2">
                    {bulkData.length}
                  </p>
                </div>

                <div className="bg-red-500/5 border border-red-500/20 rounded-xl p-5">
                  <p className="text-xs text-red-400 uppercase tracking-wider">
                    Hot
                  </p>

                  <p className="text-3xl font-bold text-red-400 mt-2">
                    {hotLeads.length}
                  </p>
                </div>

                <div className="bg-green-500/5 border border-green-500/20 rounded-xl p-5">
                  <p className="text-xs text-green-400 uppercase tracking-wider">
                    High+
                  </p>

                  <p className="text-3xl font-bold text-green-400 mt-2">
                    {highValueLeads.length}
                  </p>
                </div>

                <div className="bg-blue-500/5 border border-blue-500/20 rounded-xl p-5">
                  <p className="text-xs text-blue-400 uppercase tracking-wider">
                    Successful
                  </p>

                  <p className="text-3xl font-bold text-blue-400 mt-2">
                    {
                      successfulBulkLeads.length
                    }
                  </p>
                </div>

                <div className="bg-neutral-900 border border-neutral-800 rounded-xl p-5">
                  <p className="text-xs text-neutral-500 uppercase tracking-wider">
                    Minimum Pipeline
                  </p>

                  <p className="text-2xl font-bold text-green-400 mt-2">
                    $
                    {totalPotential.toLocaleString()}
                  </p>
                </div>
              </div>

              {/* TABLE HEADER */}

              <div className="flex flex-col md:flex-row justify-between md:items-center gap-3 border-b border-neutral-800 pb-4">
                <div>
                  <h2 className="text-xl font-semibold">
                    Ranked Prospecting Queue
                  </h2>

                  <p className="text-xs text-neutral-500 mt-1">
                    Highest commercial opportunity appears first.
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

              {/* TABLE */}

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
                          Service
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
                            item.intelligence ||
                            {};

                          return (
                            <tr
                              key={`${item.url}-${index}`}
                              className="hover:bg-neutral-800/40 transition-colors"
                            >
                              <td className="p-3">
                                <span className="text-xs text-neutral-500 font-mono">
                                  #
                                  {index +
                                    1}
                                </span>
                              </td>

                              <td className="p-3 min-w-[230px]">
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
                                      {getBusinessDisplayName(
                                        item
                                      )}
                                    </div>

                                    <div className="text-xs text-neutral-500 truncate max-w-[230px] mt-1">
                                      {item.domain ||
                                        getDomainName(
                                          item.url ||
                                            ""
                                        )}
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
                                      intel.website_score ??
                                        0
                                    )}`}
                                  >
                                    {intel.website_score ??
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
                                      {intel.opportunity_score ??
                                        0}
                                      /100
                                    </span>

                                    <span
                                      className={`w-fit inline-flex border px-1.5 py-0.5 rounded text-[9px] font-bold ${getOpportunityClasses(
                                        intel.opportunity_level
                                      )}`}
                                    >
                                      {
                                        intel.opportunity_level ||
                                        "UNKNOWN"
                                      }
                                    </span>
                                  </div>
                                ) : (
                                  <span className="text-red-400 text-xs">
                                    FAILED
                                  </span>
                                )}
                              </td>

                              <td className="p-3 max-w-[230px]">
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

                              <td className="p-3 min-w-[175px]">
                                <div className="flex flex-col gap-1">
                                  {item.phones?.[0] && (
                                    <span className="text-xs text-neutral-400 flex items-center gap-1.5">
                                      <Phone className="w-3 h-3 text-blue-400" />

                                      {
                                        item
                                          .phones[0]
                                      }
                                    </span>
                                  )}

                                  {item.emails?.[0] && (
                                    <span className="text-xs text-neutral-400 flex items-center gap-1.5 truncate max-w-[175px]">
                                      <Mail className="w-3 h-3 text-purple-400" />

                                      {
                                        item
                                          .emails[0]
                                      }
                                    </span>
                                  )}

                                  {!item
                                    .phones
                                    ?.length &&
                                    !item
                                      .emails
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

        {/* EMPTY BULK */}

        {mode === "bulk" &&
          bulkData.length === 0 &&
          !loading && (
            <div className="bg-neutral-900 border border-neutral-800 border-dashed rounded-xl p-10 text-center">
              <Layers className="w-10 h-10 text-neutral-700 mx-auto mb-3" />

              <h3 className="font-semibold text-neutral-300">
                No prospects analyzed yet
              </h3>

              <p className="text-sm text-neutral-500 mt-1 max-w-md mx-auto">
                Add a list of websites above and QuickLead will rank the best commercial opportunities first.
              </p>
            </div>
          )}
      </div>

      {/* WEBSITE PREVIEW MODAL */}

      {websitePreview && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm p-2 md:p-5">
          <div className="w-full h-full bg-neutral-900 border border-neutral-800 rounded-xl overflow-hidden flex flex-col">
            <div className="h-14 shrink-0 border-b border-neutral-800 flex items-center justify-between px-3 md:px-4">
              <div className="flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-blue-400" />

                <div>
                  <span className="text-sm font-semibold">
                    Generated Website Preview
                  </span>

                  {previewLead && (
                    <div className="text-[10px] text-neutral-500">
                      {getBusinessDisplayName(
                        previewLead
                      )}
                    </div>
                  )}
                </div>
              </div>

              <div className="flex items-center gap-2">
                {previewLead?.url && (
                  <a
                    href={previewLead.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="bg-neutral-800 hover:bg-neutral-700 text-neutral-200 px-3 py-2 rounded-md text-xs flex items-center gap-2"
                  >
                    <ExternalLink className="w-3.5 h-3.5" />
                    Original Site
                  </a>
                )}

                <button
                  onClick={() => {
                    setWebsitePreview(
                      null
                    );
                    setPreviewLead(
                      null
                    );
                  }}
                  className="bg-neutral-800 hover:bg-neutral-700 p-2 rounded-md"
                  aria-label="Close preview"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            </div>

            <div className="flex-1 bg-white">
              <iframe
                srcDoc={
                  websitePreview
                }
                title="Generated website preview"
                className="w-full h-full border-0"
                sandbox="allow-same-origin allow-forms"
              />
            </div>
          </div>
        </div>
      )}

      {/* BULK LEAD DETAIL MODAL */}

      {selectedLead && (
        <div className="fixed inset-0 z-40 bg-black/75 backdrop-blur-sm p-3 md:p-6 overflow-y-auto">
          <div className="max-w-7xl mx-auto">
            <div className="flex justify-end mb-2">
              <button
                onClick={() =>
                  setSelectedLead(
                    null
                  )
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