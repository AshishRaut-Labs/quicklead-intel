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
  BriefcaseBusiness,
  MapPin,
  Gauge,
} from "lucide-react";

const API_BASE = "https://quicklead-intel.onrender.com";

type Mode = "single" | "bulk";

type LeadData = {
  url?: string;
  domain?: string;

  business_name?: string;
  business_name_source?: string;
  business_name_confidence?: number;

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
    country_confidence?: string;

    country_evidence?: {
      phone_country?: string | null;
      explicit_country?: string | null;
      tld_country?: string | null;
      language_country?: string | null;
      language_country_confidence?: string;
    };

    currency_hints?: string[];

    primary_currency?: string | null;
    primary_currency_symbol?: string | null;
    currency_source?: string;
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
    opportunity_level?:
      | "HOT"
      | "HIGH"
      | "MEDIUM"
      | "LOW"
      | string;

    opportunity_reasons?: string[];
    recommendations?: string[];

    best_sales_angle?: string;

    service_reason?: string;

    problems_found?: string[];

    suggested_offer?: string;
    suggested_price?: string;
    suggested_price_localized?: string;

    personalized_pitch?: string;

    lead_type?: string;
    lead_type_confidence?: string;

    commercial_intent?: string;

    project_value?: {
      min?: number;
      max?: number;
      currency?: string;
    };

    localized_project_value?: {
      currency?: string;
      symbol?: string;
      min?: number;
      max?: number;
      formatted?: string;
      source?: string;
    };
  };
};

type BulkLead = LeadData;

export default function QuickLeadDashboard() {
  const [url, setUrl] = useState("");
  const [bulkUrls, setBulkUrls] = useState("");
  const [mode, setMode] =
    useState<Mode>("single");

  const [loading, setLoading] =
    useState(false);

  const [error, setError] =
    useState("");

  const [data, setData] =
    useState<LeadData | null>(null);

  const [bulkData, setBulkData] =
    useState<BulkLead[]>([]);

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

  const normalizeUrl = (
    value: string
  ): string => {
    const trimmed =
      value.trim();

    if (!trimmed) return "";

    if (
      /^https?:\/\//i.test(
        trimmed
      )
    ) {
      return trimmed;
    }

    return `https://${trimmed}`;
  };

  const getDomainName = (
    value: string
  ): string => {
    try {
      const normalized =
        normalizeUrl(value);

      const parsed = new URL(
        normalized
      );

      return parsed.hostname.replace(
        /^www\./i,
        ""
      );
    } catch {
      return value
        .replace(
          /^https?:\/\//i,
          ""
        )
        .replace(
          /^www\./i,
          ""
        )
        .split("/")[0];
    }
  };

  const getScoreColor = (
    score: number
  ): string => {
    if (score >= 80) {
      return "text-green-400";
    }

    if (score >= 60) {
      return "text-blue-400";
    }

    if (score >= 40) {
      return "text-yellow-400";
    }

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

  const getIntentClasses = (
    intent?: string
  ): string => {
    switch (
      intent?.toUpperCase()
    ) {
      case "HIGH":
        return "bg-green-500/10 text-green-400 border-green-500/20";

      case "MEDIUM":
        return "bg-yellow-500/10 text-yellow-400 border-yellow-500/20";

      default:
        return "bg-neutral-800 text-neutral-400 border-neutral-700";
    }
  };

  const getLeadTypeClasses = (
    leadType?: string
  ): string => {
    switch (leadType) {
      case "B2B":
        return "bg-blue-500/10 text-blue-400 border-blue-500/20";

      case "LOCAL_SERVICE":
        return "bg-purple-500/10 text-purple-400 border-purple-500/20";

      case "ECOMMERCE":
        return "bg-orange-500/10 text-orange-400 border-orange-500/20";

      case "SOFTWARE_TECH":
        return "bg-cyan-500/10 text-cyan-400 border-cyan-500/20";

      default:
        return "bg-neutral-800 text-neutral-400 border-neutral-700";
    }
  };

  const getCurrencyClasses = (
    currency?: string
  ): string => {
    switch (
      currency?.toUpperCase()
    ) {
      case "INR":
        return "bg-orange-500/10 text-orange-300 border-orange-500/20";

      case "GBP":
        return "bg-blue-500/10 text-blue-300 border-blue-500/20";

      case "EUR":
        return "bg-cyan-500/10 text-cyan-300 border-cyan-500/20";

      case "AED":
        return "bg-green-500/10 text-green-300 border-green-500/20";

      case "CAD":
        return "bg-red-500/10 text-red-300 border-red-500/20";

      case "AUD":
        return "bg-yellow-500/10 text-yellow-300 border-yellow-500/20";

      default:
        return "bg-neutral-800 text-neutral-300 border-neutral-700";
    }
  };

  const getBooleanLabel = (
    value?: boolean
  ): string => {
    return value
      ? "Detected"
      : "Not detected";
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
      .replace(
        /_/g,
        " "
      )
      .replace(
        /\b\w/g,
        (letter) =>
          letter.toUpperCase()
      );
  };

  const getBusinessDisplayName = (
    lead: LeadData
  ): string => {
    return (
      lead.business_name ||
      getDomainName(
        lead.url || ""
      ) ||
      "Unknown Business"
    );
  };

  const getCountryEvidenceText = (
    lead: LeadData
  ): string => {
    const evidence =
      lead.locale_signals
        ?.country_evidence;

    if (!evidence) {
      return "No country evidence available";
    }

    const pieces: string[] = [];

    if (
      evidence.phone_country
    ) {
      pieces.push(
        `Phone: ${evidence.phone_country}`
      );
    }

    if (
      evidence.explicit_country
    ) {
      pieces.push(
        `Page: ${evidence.explicit_country}`
      );
    }

    if (
      evidence.tld_country
    ) {
      pieces.push(
        `Domain: ${evidence.tld_country}`
      );
    }

    if (
      evidence.language_country
    ) {
      const languageLabel =
        evidence
          .language_country_confidence ===
        "Weak"
          ? "Language (weak)"
          : "Language";

      pieces.push(
        `${languageLabel}: ${evidence.language_country}`
      );
    }

    return (
      pieces.join(" • ") ||
      "No country evidence available"
    );
  };

  const getPrimaryCurrency = (
    lead: LeadData
  ): string => {
    return (
      lead.locale_signals
        ?.primary_currency ||
      lead.intelligence
        ?.localized_project_value
        ?.currency ||
      lead.intelligence
        ?.project_value
        ?.currency ||
      "USD"
    );
  };

  const getPrimaryCurrencySymbol = (
    lead: LeadData
  ): string => {
    return (
      lead.locale_signals
        ?.primary_currency_symbol ||
      lead.intelligence
        ?.localized_project_value
        ?.symbol ||
      "$"
    );
  };

  const getCurrencySource = (
    lead: LeadData
  ): string => {
    return (
      lead.locale_signals
        ?.currency_source ||
      lead.intelligence
        ?.localized_project_value
        ?.source ||
      "unknown"
    );
  };

  const getLocalizedProjectPrice = (
    lead: LeadData
  ): string => {
    return (
      lead.intelligence
        ?.suggested_price_localized ||
      lead.intelligence
        ?.localized_project_value
        ?.formatted ||
      lead.intelligence
        ?.suggested_price ||
      "N/A"
    );
  };

  const sortedBulkData =
    useMemo(() => {
      return [...bulkData].sort(
        (a, b) => {
          const aScore =
            a.intelligence
              ?.opportunity_score ??
            -1;

          const bScore =
            b.intelligence
              ?.opportunity_score ??
            -1;

          return bScore - aScore;
        }
      );
    }, [bulkData]);

  const successfulBulkLeads =
    useMemo(() => {
      return bulkData.filter(
        (item) =>
          item.status ===
          "Success"
      );
    }, [bulkData]);

  const hotLeads = useMemo(() => {
    return successfulBulkLeads.filter(
      (item) =>
        item.intelligence
          ?.opportunity_level ===
        "HOT"
    );
  }, [successfulBulkLeads]);

  const highValueLeads =
    useMemo(() => {
      return successfulBulkLeads.filter(
        (item) => {
          const score =
            item.intelligence
              ?.opportunity_score ??
            0;

          return score >= 55;
        }
      );
    }, [successfulBulkLeads]);

  /*
   * Keep pipeline math in USD because bulk leads
   * may use different local currencies.
   */
  const totalPotential =
    useMemo(() => {
      return successfulBulkLeads.reduce(
        (sum, item) => {
          const min =
            item.intelligence
              ?.project_value
              ?.min ?? 0;

          return sum + min;
        },
        0
      );
    }, [successfulBulkLeads]);

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
        const target =
          normalizeUrl(url);

        const response =
          await fetch(
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
            // Ignore.
          }

          throw new Error(
            message
          );
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
      .map((item) =>
        item.trim()
      )
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
        urlList.map(
          normalizeUrl
        );

      const response =
        await fetch(
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
          // Ignore.
        }

        throw new Error(
          message
        );
      }

      const result =
        await response.json();

      setBulkData(
        Array.isArray(
          result?.results
        )
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

  const generateWebsiteForLead =
    async (
      lead: LeadData | null
    ): Promise<void> => {
      if (!lead) return;

      setGeneratingWebsite(
        true
      );

      setError("");
      setPreviewLead(
        lead
      );

      try {
        const response =
          await fetch(
            `${API_BASE}/api/generate-website`,
            {
              method: "POST",
              headers: {
                "Content-Type":
                  "application/json",
              },
              body: JSON.stringify(
                lead
              ),
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
            // Ignore.
          }

          throw new Error(
            message
          );
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

        setPreviewLead(
          null
        );
      } finally {
        setGeneratingWebsite(
          false
        );
      }
    };

  const copyOutreach = async (
    lead: LeadData | null
  ): Promise<void> => {
    const pitch =
      lead?.intelligence
        ?.personalized_pitch ||
      "";

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

      setCopySuccess(
        true
      );

      window.setTimeout(
        () =>
          setCopySuccess(
            false
          ),
        1800
      );
    } catch {
      setError(
        "Could not copy the outreach message."
      );
    }
  };

  /*
   * Escape a CSV value safely.
   */
  const escapeCsvCell = (
    cell: string | number | boolean
  ): string => {
    const value = String(
      cell ?? ""
    );

    return `"${value.replace(
      /"/g,
      '""'
    )}"`;
  };

  /*
   * Prevent Excel from converting phone numbers into
   * scientific notation.
   *
   * Example:
   * +918658263639
   *
   * becomes an Excel text formula:
   * =" +918658263639 "
   *
   * without spaces, of course.
   *
   * This keeps the exact phone number visible in Excel.
   */
  const prepareCsvCell = (
    cell: string | number | boolean
  ): string => {
    const value = String(
      cell ?? ""
    );

    const phoneLike =
      /^\+\d{8,15}$/.test(
        value.trim()
      );

    if (phoneLike) {
      return `="${value.replace(
        /"/g,
        '""'
      )}"`;
    }

    return escapeCsvCell(
      cell
    );
  };

  const exportRowsAsCsv = (
    rows: (
      | string
      | number
      | boolean
    )[][]
  ): void => {
    const csvText =
      rows
        .map((row) =>
          row
            .map(
              prepareCsvCell
            )
            .join(",")
        )
        .join("\r\n");

    /*
     * UTF-8 BOM is important for Excel so symbols such as
     * ₹, £, €, ¥, etc. are decoded correctly.
     */
    const blob =
      new Blob(
        [
          "\ufeff",
          csvText,
        ],
        {
          type: "text/csv;charset=utf-8;",
        }
      );

    const url =
      URL.createObjectURL(
        blob
      );

    const link =
      document.createElement(
        "a"
      );

    link.href = url;

    link.download =
      "quicklead_intel_report.csv";

    document.body.appendChild(
      link
    );

    link.click();

    document.body.removeChild(
      link
    );

    URL.revokeObjectURL(
      url
    );
  };

  const exportCSV = (): void => {
    if (
      mode === "single" &&
      data
    ) {
      const intel =
        data.intelligence ||
        {};

      const locale =
        data.locale_signals ||
        {};

      const localizedValue =
        intel.localized_project_value ||
        {};

      const rows: (
        | string
        | number
        | boolean
      )[][] = [
        [
          "Metric",
          "Value",
        ],
        [
          "URL",
          data.url || "",
        ],
        [
          "Domain",
          data.domain || "",
        ],
        [
          "Business Name",
          data.business_name ||
            getBusinessDisplayName(
              data
            ),
        ],
        [
          "Business Name Source",
          data.business_name_source ||
            "",
        ],
        [
          "Business Name Confidence",
          data.business_name_confidence ??
            "",
        ],
        [
          "Page Title",
          data.title || "",
        ],
        [
          "Website Health Score",
          intel.website_score ??
            "",
        ],
        [
          "SEO Score",
          intel.seo_score ?? "",
        ],
        [
          "Conversion Score",
          intel.conversion_score ??
            "",
        ],
        [
          "Technical Score",
          intel.technical_score ??
            "",
        ],
        [
          "Sales Opportunity Score",
          intel.opportunity_score ??
            "",
        ],
        [
          "Opportunity Level",
          intel.opportunity_level ??
            "",
        ],
        [
          "Lead Type",
          intel.lead_type || "",
        ],
        [
          "Lead Type Confidence",
          intel.lead_type_confidence ||
            "",
        ],
        [
          "Commercial Intent",
          intel.commercial_intent ||
            "",
        ],
        [
          "Best Sales Angle",
          intel.best_sales_angle ||
            "",
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
          "Suggested Price Localized",
          intel.suggested_price_localized ||
            "",
        ],
        [
          "Project Currency",
          intel.project_value
            ?.currency ||
            "USD",
        ],
        [
          "Project Min (USD)",
          intel.project_value
            ?.min ?? "",
        ],
        [
          "Project Max (USD)",
          intel.project_value
            ?.max ?? "",
        ],
        [
          "Localized Currency",
          localizedValue.currency ||
            locale.primary_currency ||
            "",
        ],
        [
          "Localized Currency Symbol",
          localizedValue.symbol ||
            locale.primary_currency_symbol ||
            "",
        ],
        [
          "Localized Project Min",
          localizedValue.min ??
            "",
        ],
        [
          "Localized Project Max",
          localizedValue.max ??
            "",
        ],
        [
          "Localized Project Value",
          localizedValue.formatted ||
            "",
        ],
        [
          "Currency Source",
          locale.currency_source ||
            localizedValue.source ||
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
          locale.language ||
            "",
        ],
        [
          "Language Country",
          locale
            .country_evidence
            ?.language_country ||
            "",
        ],
        [
          "Language Evidence Strength",
          locale
            .country_evidence
            ?.language_country_confidence ||
            "",
        ],
        [
          "Country Hint",
          locale.country_hint ||
            "",
        ],
        [
          "Country Confidence",
          locale.country_confidence ||
            "",
        ],
        [
          "Country Evidence",
          getCountryEvidenceText(
            data
          ),
        ],
        [
          "Currency Hints",
          (
            locale.currency_hints ||
            []
          ).join(", "),
        ],
        [
          "Primary Currency",
          locale.primary_currency ||
            "",
        ],
        [
          "Primary Currency Symbol",
          locale.primary_currency_symbol ||
            "",
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
          data.socials
            ?.twitter || "",
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

      exportRowsAsCsv(
        rows
      );

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
          "Business Name Confidence",
          "Website Health",
          "Sales Opportunity",
          "Opportunity Level",
          "Lead Type",
          "Commercial Intent",
          "Best Sales Angle",
          "Recommended Service",
          "Suggested Price",
          "Suggested Price Localized",
          "Project Currency",
          "Project Min USD",
          "Project Max USD",
          "Localized Currency",
          "Localized Project Value",
          "Country",
          "Country Confidence",
          "Primary Currency",
          "Currency Source",
          "Top Sales Reasons",
          "Phone",
          "Email",
        ],
      ];

      sortedBulkData.forEach(
        (
          item,
          index
        ) => {
          if (
            item.status ===
            "Success"
          ) {
            const intel =
              item.intelligence ||
              {};

            const localized =
              intel.localized_project_value ||
              {};

            const locale =
              item.locale_signals ||
              {};

            rows.push([
              index + 1,
              item.url || "",
              item.domain || "",
              item.business_name ||
                getBusinessDisplayName(
                  item
                ),
              item.business_name_confidence ??
                "",
              intel.website_score ??
                "",
              intel.opportunity_score ??
                "",
              intel.opportunity_level ??
                "",
              intel.lead_type ||
                "",
              intel.commercial_intent ||
                "",
              intel.best_sales_angle ||
                "",
              intel.suggested_offer ||
                "",
              intel.suggested_price ||
                "",
              intel.suggested_price_localized ||
                localized.formatted ||
                "",
              intel.project_value
                ?.currency ||
                "USD",
              intel.project_value
                ?.min ?? "",
              intel.project_value
                ?.max ?? "",
              localized.currency ||
                locale.primary_currency ||
                "",
              localized.formatted ||
                "",
              locale.country_hint ||
                "",
              locale.country_confidence ||
                "",
              locale.primary_currency ||
                "",
              locale.currency_source ||
                localized.source ||
                "",
              (
                intel.opportunity_reasons ||
                []
              ).join(" | "),
              item.phones
                ?.join(" | ") ||
                "",
              item.emails
                ?.join(" | ") ||
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
              "",
              "FAILED",
              "",
              "",
              "",
              "",
              "",
              "",
              "",
              "",
              "",
              "",
              "",
              "",
              "",
              "",
              item.error ||
                "Scan failed",
              "",
              "",
            ]);
          }
        }
      );

      exportRowsAsCsv(
        rows
      );
    }
  };

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

  const renderClassificationBadges = (
    lead: LeadData
  ): ReactNode => {
    const intel =
      lead.intelligence || {};

    return (
      <div className="flex flex-wrap gap-2 mt-4">
        {intel.lead_type && (
          <span
            className={`inline-flex items-center gap-1.5 border px-2.5 py-1.5 rounded-lg text-[11px] font-semibold ${getLeadTypeClasses(
              intel.lead_type
            )}`}
          >
            <BriefcaseBusiness className="w-3.5 h-3.5" />

            {getPrettyKey(
              intel.lead_type
            )}
          </span>
        )}

        {intel.commercial_intent && (
          <span
            className={`inline-flex items-center gap-1.5 border px-2.5 py-1.5 rounded-lg text-[11px] font-semibold ${getIntentClasses(
              intel.commercial_intent
            )}`}
          >
            <Gauge className="w-3.5 h-3.5" />

            Commercial Intent:{" "}
            {intel.commercial_intent}
          </span>
        )}

        {lead.locale_signals
          ?.country_hint && (
          <span className="inline-flex items-center gap-1.5 bg-neutral-800 border border-neutral-700 px-2.5 py-1.5 rounded-lg text-[11px] font-semibold text-neutral-300">
            <MapPin className="w-3.5 h-3.5" />

            {lead.locale_signals.country_hint}

            {lead.locale_signals
              .country_confidence
              ? ` • ${lead.locale_signals.country_confidence}`
              : ""}
          </span>
        )}

        {getPrimaryCurrency(
          lead
        ) && (
          <span
            className={`inline-flex items-center gap-1.5 border px-2.5 py-1.5 rounded-lg text-[11px] font-semibold ${getCurrencyClasses(
              getPrimaryCurrency(
                lead
              )
            )}`}
          >
            <DollarSign className="w-3.5 h-3.5" />

            {getPrimaryCurrency(
              lead
            )}{" "}
            {getPrimaryCurrencySymbol(
              lead
            )}
          </span>
        )}
      </div>
    );
  };

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

    const primaryCurrency =
      getPrimaryCurrency(
        lead
      );

    const primaryCurrencySymbol =
      getPrimaryCurrencySymbol(
        lead
      );

    const currencySource =
      getCurrencySource(
        lead
      );

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

              {renderClassificationBadges(
                lead
              )}

              <div className="flex flex-wrap items-center gap-x-4 gap-y-2 mt-4 text-xs text-neutral-500">
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

                    {lead
                      .locale_signals
                      ?.country_confidence && (
                      <span className="text-neutral-500">
                        {" "}
                        (
                        {
                          lead
                            .locale_signals
                            .country_confidence
                        }
                        )
                      </span>
                    )}
                  </span>
                )}

                {language && (
                  <span>
                    Language:{" "}
                    <span className="text-neutral-300">
                      {language}
                    </span>

                    {lead
                      .locale_signals
                      ?.country_evidence
                      ?.language_country_confidence ===
                      "Weak" && (
                      <span className="text-yellow-500">
                        {" "}
                        (weak country evidence)
                      </span>
                    )}
                  </span>
                )}

                <span>
                  Currency:{" "}
                  <span className="text-neutral-300">
                    {primaryCurrency}{" "}
                    {primaryCurrencySymbol}
                  </span>

                  {currencySource &&
                    currencySource !==
                      "unknown" && (
                      <span className="text-neutral-500">
                        {" "}
                        (
                        {currencySource
                          .replace(
                            /_/g,
                            " "
                          )}
                        )
                      </span>
                    )}
                </span>
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
                    href={
                      lead.url
                    }
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
              {getLocalizedProjectPrice(
                lead
              )}
            </p>

            <div className="space-y-1 mt-2">
              {intel.project_value && (
                <p className="text-xs text-neutral-500">
                  Internal USD range: $
                  {(
                    intel
                      .project_value
                      .min ?? 0
                  ).toLocaleString()}{" "}
                  – $
                  {(
                    intel
                      .project_value
                      .max ?? 0
                  ).toLocaleString()}
                </p>
              )}

              {intel.localized_project_value
                ?.formatted && (
                <p className="text-xs text-neutral-400">
                  Local range:{" "}
                  {
                    intel
                      .localized_project_value
                      .formatted
                  }
                </p>
              )}

              <p className="text-[10px] text-neutral-600">
                Currency:{" "}
                {primaryCurrency}{" "}
                {primaryCurrencySymbol}
                {currencySource &&
                  currencySource !==
                    "unknown"
                  ? ` • ${currencySource.replace(
                      /_/g,
                      " "
                    )}`
                  : ""}
              </p>
            </div>
          </div>

          <div className="bg-blue-900/10 border border-blue-500/30 rounded-xl p-5">
            <div className="flex items-center gap-2 text-blue-400 mb-3">
              <ArrowUpRight className="w-4 h-4" />

              <p className="text-[11px] uppercase tracking-wider">
                Best Sales Angle
              </p>
            </div>

            <p className="text-sm text-neutral-300 leading-relaxed">
              {intel.best_sales_angle ||
                intel.opportunity_reasons?.[0] ||
                intel.service_reason ||
                "No specific sales angle detected."}
            </p>
          </div>
        </div>

        {/* SALES CLASSIFICATION */}

        <div className="bg-neutral-900 border border-neutral-800 rounded-xl p-6">
          <div className="flex items-center gap-2 mb-5">
            <BriefcaseBusiness className="w-5 h-5 text-blue-400" />

            <div>
              <h3 className="font-semibold text-neutral-100">
                Prospect Classification
              </h3>

              <p className="text-xs text-neutral-500 mt-0.5">
                QuickLead's commercial classification for outreach prioritization.
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-5 gap-3">
            <div className="bg-neutral-950 border border-neutral-800 rounded-lg p-4">
              <p className="text-[10px] uppercase tracking-wider text-neutral-500">
                Lead Type
              </p>

              <p className="text-base font-semibold text-neutral-200 mt-2">
                {intel.lead_type
                  ? getPrettyKey(
                      intel.lead_type
                    )
                  : "Unknown"}
              </p>

              {intel.lead_type_confidence && (
                <p className="text-xs text-neutral-500 mt-1">
                  Confidence:{" "}
                  {intel.lead_type_confidence}
                </p>
              )}
            </div>

            <div className="bg-neutral-950 border border-neutral-800 rounded-lg p-4">
              <p className="text-[10px] uppercase tracking-wider text-neutral-500">
                Commercial Intent
              </p>

              <span
                className={`inline-flex mt-2 border px-2 py-1 rounded-md text-xs font-semibold ${getIntentClasses(
                  intel.commercial_intent
                )}`}
              >
                {intel.commercial_intent ||
                  "Unknown"}
              </span>
            </div>

            <div className="bg-neutral-950 border border-neutral-800 rounded-lg p-4">
              <p className="text-[10px] uppercase tracking-wider text-neutral-500">
                Country
              </p>

              <p className="text-base font-semibold text-neutral-200 mt-2">
                {country ||
                  "Unknown"}
              </p>

              <p className="text-xs text-neutral-500 mt-1">
                {lead
                  .locale_signals
                  ?.country_confidence ||
                  "No confidence score"}
              </p>
            </div>

            <div className="bg-neutral-950 border border-neutral-800 rounded-lg p-4">
              <p className="text-[10px] uppercase tracking-wider text-neutral-500">
                Business Name Confidence
              </p>

              <p className="text-2xl font-bold text-blue-400 mt-2">
                {lead.business_name_confidence ??
                  0}
              </p>

              <p className="text-xs text-neutral-500 mt-1">
                Source:{" "}
                {lead.business_name_source ||
                  "Unknown"}
              </p>
            </div>

            <div className="bg-neutral-950 border border-neutral-800 rounded-lg p-4">
              <p className="text-[10px] uppercase tracking-wider text-neutral-500">
                Primary Currency
              </p>

              <div className="flex items-center gap-2 mt-2">
                <span
                  className={`inline-flex border px-2 py-1 rounded-md text-xs font-semibold ${getCurrencyClasses(
                    primaryCurrency
                  )}`}
                >
                  {primaryCurrency}
                </span>

                <span className="text-lg font-semibold text-neutral-200">
                  {primaryCurrencySymbol}
                </span>
              </div>

              <p className="text-xs text-neutral-500 mt-1">
                Source:{" "}
                {currencySource}
              </p>
            </div>
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
                  (
                    recommendation,
                    index
                  ) => (
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
              {intel.opportunity_score ??
                0}
              /100
            </div>
          </div>

          {intel.opportunity_reasons &&
          intel.opportunity_reasons.length >
            0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {intel.opportunity_reasons.map(
                (
                  reason,
                  index
                ) => (
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
                (value) =>
                  !value
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
                (
                  problem,
                  index
                ) => (
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
                (value) =>
                  !value
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
                      Detection
                    </p>

                    <p className="text-sm text-neutral-300">
                      {lead.business_name_source ||
                        "Unknown"}

                      {typeof lead.business_name_confidence ===
                        "number" &&
                        ` • ${lead.business_name_confidence}% confidence`}
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
                          (
                            h1,
                            index
                          ) => (
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
                          (
                            email,
                            index
                          ) => (
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
                          (
                            phone,
                            index
                          ) => (
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
                          ([
                            platform,
                            link,
                          ]) =>
                            link ? (
                              <a
                                key={platform}
                                href={
                                  link
                                }
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
                        (
                          value
                        ) => !value
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
                      ([
                        label,
                        value,
                      ]) => (
                        <div
                          key={String(
                            label
                          )}
                          className="flex items-center justify-between bg-neutral-900 border border-neutral-800 px-3 py-2 rounded"
                        >
                          <span className="text-sm text-neutral-300">
                            {String(
                              label
                            )}
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
                        ([
                          tech,
                          present,
                        ]) => (
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
                        ([
                          tracker,
                          present,
                        ]) => (
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
                    <div className="bg-neutral-900 border border-neutral-800 px-3 py-3 rounded">
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-neutral-300">
                          Country
                        </span>

                        <span className="text-xs font-semibold text-neutral-200">
                          {country ||
                            "Unknown"}
                        </span>
                      </div>

                      <div className="text-[11px] text-neutral-500 mt-1">
                        Confidence:{" "}
                        {lead
                          .locale_signals
                          ?.country_confidence ||
                          "Unknown"}
                      </div>
                    </div>

                    <div className="bg-neutral-900 border border-neutral-800 px-3 py-3 rounded">
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-neutral-300">
                          Language
                        </span>

                        <span className="text-xs text-neutral-400 text-right">
                          {lead
                            .locale_signals
                            ?.language ||
                            "Unknown"}
                        </span>
                      </div>

                      {lead
                        .locale_signals
                        ?.country_evidence
                        ?.language_country && (
                        <div className="text-[11px] text-neutral-500 mt-1">
                          Country signal:{" "}
                          {
                            lead
                              .locale_signals
                              .country_evidence
                              .language_country
                          }{" "}
                          (
                          {
                            lead
                              .locale_signals
                              .country_evidence
                              .language_country_confidence ||
                            "Unknown"
                          }
                          )
                        </div>
                      )}
                    </div>

                    <div className="bg-neutral-900 border border-neutral-800 px-3 py-3 rounded">
                      <p className="text-xs text-neutral-500 uppercase tracking-wider mb-2">
                        Evidence
                      </p>

                      <p className="text-xs text-neutral-300 leading-relaxed">
                        {getCountryEvidenceText(
                          lead
                        )}
                      </p>
                    </div>

                    <div className="bg-neutral-900 border border-neutral-800 px-3 py-3 rounded">
                      <div className="flex items-center justify-between gap-3">
                        <span className="text-sm text-neutral-300">
                          Currency Hints
                        </span>

                        <span className="text-xs text-neutral-400 text-right">
                          {lead
                            .locale_signals
                            ?.currency_hints &&
                          lead
                            .locale_signals
                            .currency_hints
                            .length > 0
                            ? lead.locale_signals.currency_hints.join(
                                ", "
                              )
                            : "None detected"}
                        </span>
                      </div>
                    </div>

                    <div className="bg-neutral-900 border border-neutral-800 px-3 py-3 rounded">
                      <div className="flex items-center justify-between gap-3">
                        <span className="text-sm text-neutral-300">
                          Primary Currency
                        </span>

                        <span
                          className={`inline-flex border px-2 py-1 rounded-md text-xs font-semibold ${getCurrencyClasses(
                            primaryCurrency
                          )}`}
                        >
                          {primaryCurrency}{" "}
                          {primaryCurrencySymbol}
                        </span>
                      </div>

                      <div className="text-[11px] text-neutral-500 mt-1">
                        Source:{" "}
                        {currencySource}
                      </div>
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
              Engine: Global Sales Intelligence V6
            </span>
          </div>
        )}
      </div>
    );
  };

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
                  onClick={
                    exportCSV
                  }
                  className="bg-neutral-800 hover:bg-neutral-700 text-white px-4 py-2 rounded-lg flex items-center gap-2 transition-colors text-sm"
                >
                  <Download className="w-4 h-4" />

                  Export Lead
                </button>
              </div>

              {renderLeadDetails(
                data
              )}
            </div>
          )}

        {/* BULK */}

        {mode === "bulk" &&
          bulkData.length > 0 && (
            <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">

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
                    {successfulBulkLeads.length}
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

                  <p className="text-[10px] text-neutral-600 mt-1">
                    USD baseline across mixed-country leads
                  </p>
                </div>

              </div>

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
                  onClick={
                    exportCSV
                  }
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
                          Type
                        </th>

                        <th className="p-3">
                          Intent
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
                          Currency
                        </th>

                        <th className="p-3">
                          Country
                        </th>

                        <th className="p-3">
                          Action
                        </th>
                      </tr>
                    </thead>

                    <tbody className="divide-y divide-neutral-800 text-sm">
                      {sortedBulkData.map(
                        (
                          item,
                          index
                        ) => {
                          const intel =
                            item.intelligence ||
                            {};

                          const itemCurrency =
                            getPrimaryCurrency(
                              item
                            );

                          const itemCurrencySymbol =
                            getPrimaryCurrencySymbol(
                              item
                            );

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
                                      {getBusinessDisplayName(
                                        item
                                      )}
                                    </div>

                                    <div className="text-xs text-neutral-500 truncate max-w-[220px] mt-1">
                                      {item.domain ||
                                        getDomainName(
                                          item.url ||
                                            ""
                                        )}
                                    </div>

                                    {item
                                      .business_name_confidence !==
                                      undefined && (
                                      <div className="text-[10px] text-neutral-600 mt-1">
                                        Name confidence:{" "}
                                        {
                                          item.business_name_confidence
                                        }
                                        %
                                      </div>
                                    )}
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
                                    className={`inline-flex border px-2 py-1 rounded-md text-[10px] font-semibold ${getLeadTypeClasses(
                                      intel.lead_type
                                    )}`}
                                  >
                                    {intel.lead_type
                                      ? getPrettyKey(
                                          intel.lead_type
                                        )
                                      : "Unknown"}
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
                                  <span
                                    className={`inline-flex border px-2 py-1 rounded-md text-[10px] font-semibold ${getIntentClasses(
                                      intel.commercial_intent
                                    )}`}
                                  >
                                    {intel.commercial_intent ||
                                      "Unknown"}
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
                                      {intel.opportunity_level ||
                                        "UNKNOWN"}
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
                                <div className="flex flex-col gap-0.5">
                                  <span className="text-green-400 text-xs font-semibold">
                                    {intel.suggested_price_localized ||
                                      intel.localized_project_value
                                        ?.formatted ||
                                      intel.suggested_price ||
                                      "—"}
                                  </span>

                                  {intel
                                    .project_value && (
                                    <span className="text-[10px] text-neutral-600">
                                      USD $
                                      {(
                                        intel
                                          .project_value
                                          .min ??
                                        0
                                      ).toLocaleString()}
                                      {" – "}
                                      $
                                      {(
                                        intel
                                          .project_value
                                          .max ??
                                        0
                                      ).toLocaleString()}
                                    </span>
                                  )}
                                </div>
                              </td>

                              <td className="p-3 whitespace-nowrap">
                                <div className="flex flex-col gap-1">
                                  <span
                                    className={`inline-flex w-fit border px-2 py-1 rounded-md text-[10px] font-semibold ${getCurrencyClasses(
                                      itemCurrency
                                    )}`}
                                  >
                                    {itemCurrency}{" "}
                                    {
                                      itemCurrencySymbol
                                    }
                                  </span>

                                  <span className="text-[10px] text-neutral-600">
                                    {item.locale_signals
                                      ?.currency_source ||
                                      ""}
                                  </span>
                                </div>
                              </td>

                              <td className="p-3 whitespace-nowrap">
                                <div className="flex flex-col">
                                  <span className="text-xs text-neutral-300">
                                    {item.locale_signals
                                      ?.country_hint ||
                                      "Unknown"}
                                  </span>

                                  <span className="text-[10px] text-neutral-600">
                                    {item.locale_signals
                                      ?.country_confidence ||
                                      ""}
                                  </span>
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

      {/* WEBSITE PREVIEW */}

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
                    href={
                      previewLead.url
                    }
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